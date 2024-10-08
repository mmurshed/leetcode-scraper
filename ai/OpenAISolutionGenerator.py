from logging import Logger

from openai import OpenAI

from api.ApiManager import ApiManager
from models.Question import Question
from models.QuestionContent import QuestionContent
from utils.Config import Config
from utils.Constants import Constants

class OpenAISolutionGenerator:
    def __init__(
        self,
        config: Config,
        logger: Logger,
        leetapi: ApiManager,
        cache):
        
        self.config = config
        self.logger = logger
        self.lc = leetapi
        self.cache = cache

        self.client = OpenAI(api_key=self.config.open_ai_api_key)

    def generate_example(self, question_content: QuestionContent):
        hint_content = ""
        for hint in question_content.hints:
            hint_content +=  f"{hint}\n"
        question_text = f"""Question:
{question_content.content}

Hint:
{hint_content}

Solution:
{question_content.solution}"""

        return question_text

    def generate_examples_from_similar_questions(self, question_content: QuestionContent, limit):
        example_text = ""
        count = 0
        questions = self.lc.get_all_questions()

        if len(questions) == 0:
            return example_text, count
        
    
        questions = {question.slug: question for question in questions}
        for similar_question in question_content.similar_questions:
            title_slug = similar_question['titleSlug']
            if title_slug in questions.keys():
                question = questions[title_slug]
                question_content_data = self.lc.get_question(question.id, question.slug)
                question_content = QuestionContent.from_json(question_content_data)

                if question_content.solution:
                    example_text += self.generate_example(question_content) + "\n\n"
                    count += 1
            if count >= limit:
                break

        return example_text, count

    def generate_examples_from_default_questions(self, limit):
        example_text = ""
        questions = {
            "3sum": 15,
            "unique-paths-ii": 63,
            "decode-ways": 91
        }
        
        count = 0
        for slug, id in questions.items():
            question_content_data = self.lc.get_question(id, slug)
            question_content = QuestionContent.from_json(question_content_data)

            if question_content.solution:
                example_text += self.generate_example(question_content) + "\n\n"
                count += 1
            if count >= limit:
                break

        return example_text, count

    def generate_examples(self, question_content: QuestionContent, limit):
        example_text, count = self.generate_examples_from_similar_questions(question_content, limit)
        if count < limit:
            default_example_text, default_count = self.generate_examples_from_default_questions(limit-count)
            example_text = example_text + "\n\n" + default_example_text
            count += default_count
        return example_text, count

    def generate_community_solutions(self, question: Question, limit):
        community_solution_text = ""
        count = 0
        community_solutions = self.lc.get_all_community_solutions(question.slug)

        if len(community_solutions) == 0:
            return community_solution_text, count
    
        for community_solution in community_solutions:
            community_solution_content = self.lc.get_community_solution_content(int(community_solution['id']))
            if community_solution_content:
                community_solution_text += f"""Community Solution:\n{community_solution_content}\n\n"""
                count += 1
            if count >= limit:
                break

        return community_solution_text, count

    def generate_prompt(self, question: Question, question_content: QuestionContent):
        example_text, count = self.generate_examples(question_content, 2)
        self.logger.debug(f"Examples generated {count}")

        community_solution, comsol_count = self.generate_community_solutions(question, 3)
        self.logger.debug(f"Community solution generated {comsol_count}")

        lang_name = Constants.LANG_NAMES[self.config.preferred_language_order[0]]
        prompt = str.replace(Constants.AI_PROMPT, "{{preferred_language}}", lang_name)

        hint_content = ""
        for hint in question_content.hints:
            hint_content +=  f"{hint}\n"
        
        prompt = f"""{prompt}

{example_text}

{community_solution}

Question:
{question_content.content}

Hint:
{hint_content}

Solution:

"""
        return prompt

    def submit(self, text):
        try:
            response = self.client.chat.completions.create(
                model=self.config.open_ai_model,
                messages=[{
                    "role": "user",
                    "content": [{
                        "type": "text",
                        "text": text
                        }
                    ]}],
                temperature=1,
                max_tokens=16384,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
                response_format={
                    "type": "text"
                })

            return response.choices[0].message.content
        except Exception as e:
            self.logger.error(f"An error occurred: {e}")

    def generate(self, quesion: Question, question_content: QuestionContent):
        full_text = self.generate_prompt(quesion, question_content)

        response = self.submit(full_text)
        return response

    def cached_generate(self, quesion: Question, question_content: QuestionContent):
        key = f"question-{quesion.id}-solution-gen"

        if not self.config.cache_api_calls:
            self.logger.debug(f"Cache bypass {key}")
            data = self.generate(quesion, question_content)
            return data

        # Check if data exists in the cache and retrieve it
        data = self.cache.get(key=key)

        if data is None:
            self.logger.debug(f"Cache miss {key}")
            data = self.generate(quesion, question_content)

            # Store data in the cache
            if data:
                self.cache.set(key=key, value=data)
        else:
            self.logger.debug(f"Cache hit {key}")

        return data
