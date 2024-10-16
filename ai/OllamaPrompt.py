from logging import Logger

from ai.Prompt import Prompt
from models.Question import Question
from models.QuestionContent import QuestionContent
from utils.Config import Config
from utils.Constants import Constants

class OllamaPrompt(Prompt):
    def __init__(
        self,
        config: Config,
        logger: Logger):

        Prompt.__init__(self, config, logger)
        
    def get_intial_prompt(self, question: Question, question_content: QuestionContent):       
        return Constants.OLLAMA_PROMPT

