from logging import Logger

from models.Question import Question
from models.QuestionContent import QuestionContent
from utils.Config import Config
from utils.Constants import Constants

class Prompt:
    def __init__(
        self,
        config: Config,
        logger: Logger):
        
        self.config = config
        self.logger = logger

    def get_intial_prompt(self, question: Question, question_content: QuestionContent):
        raise NotImplemented("Method not implemented")

    def get_prompt(self, question: Question, question_content: QuestionContent):
        prompt = self.get_intial_prompt(question, question_content)

        lang_name = Constants.LANG_NAMES[self.config.preferred_language_order[0]]
        prompt = str.replace(prompt, "{{preferred_language}}", lang_name)

        hint_content = ""
        for hint in question_content.hints:
            hint_content +=  f"{hint}\n"
        
        prompt = f"""{prompt}

Question:
{question_content.content}

Hint:
{hint_content}

Solution:

"""
        return prompt

