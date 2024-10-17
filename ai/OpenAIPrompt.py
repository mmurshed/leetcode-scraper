from logging import Logger

from ai.Prompt import Prompt
from api.ApiManager import ApiManager
from models.Question import Question
from models.QuestionContent import QuestionContent
from utils.Config import Config
from utils.Constants import Constants

class OpenAIPrompt(Prompt):
    def __init__(
        self,
        config: Config,
        logger: Logger,
        leetapi: ApiManager):

        self.lc = leetapi

        Prompt.__init__(self, config, logger)
        

    def format_example(self, question_content: QuestionContent, id):
        hint_content = ""
        for hint in question_content.hints:
            hint_content +=  f"{hint}\n"
        example_question_text = f"""Example Question {id}:
{question_content.content}

Example Hint {id}:
{hint_content}

Example Solution {id}:
{question_content.solution}"""

        return example_question_text

    def generate_examples_from_similar_questions(self, question_content: QuestionContent, limit):
        example_text = ""
        questions = self.lc.get_all_questions()

        if len(questions) == 0:
            return example_text, 0

        questions = {question.slug: question for question in questions}
        for id, similar_question in enumerate(question_content.similar_questions, start=1):
            title_slug = similar_question['titleSlug']
            if title_slug in questions.keys():
                question = questions[title_slug]
                question_content_data = self.lc.get_question(question.id, question.slug)
                question_content = QuestionContent.from_json(question_content_data)

                if question_content.solution:
                    example_text += self.format_example(question_content, id) + "\n\n"
            if id >= limit:
                break

        return example_text, id

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
                count += 1
                example_text += self.format_example(question_content, count) + "\n\n"
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
        community_solutions = self.lc.get_all_community_solutions(question.slug)

        if len(community_solutions) == 0:
            return community_solution_text, 0
    
        for id, community_solution in enumerate(community_solutions, start=1):
            community_solution_content = self.lc.get_community_solution_content(int(community_solution['id']))
            if community_solution_content:
                community_solution_text += f"""Community Solution {id}:\n{community_solution_content}\n\n"""
            if id >= limit:
                break

        return community_solution_text, id

    def get_intial_prompt(self, question: Question, question_content: QuestionContent):
        example_text, count = self.generate_examples(question_content, 2)
        self.logger.debug(f"Examples generated {count}")

        community_solution, comsol_count = self.generate_community_solutions(question, 3)
        self.logger.debug(f"Community solution generated {comsol_count}")
        
        prompt = f"""{Constants.OPEN_AI_PROMPT}

{example_text}

{community_solution}"""
        
        return prompt
