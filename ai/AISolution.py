from logging import Logger

from diskcache import Cache

from api.ApiManager import ApiManager
from models.Question import Question
from models.QuestionContent import QuestionContent
from utils.Config import Config

class AISolution:
    def __init__(
        self,
        config: Config,
        logger: Logger,
        cache: Cache):
        
        self.config = config
        self.logger = logger
        self.cache = cache
        self.prompt_gen = None

    def submit(self, text):
        raise NotImplemented("Method not implemented")
    
    def generate_solution(self, quesion: Question, question_content: QuestionContent):
        full_text = self.prompt_gen.get_prompt(quesion, question_content)

        response = self.submit(full_text)
        return response

    def get_solution(self, quesion: Question, question_content: QuestionContent):
        key = f"question-{quesion.id}-solution-{self.config.ai_solution_generator}"

        if not self.config.cache_api_calls:
            self.logger.debug(f"Cache bypass {key}")
            data = self.generate_solution(quesion, question_content)
            return data

        # Check if data exists in the cache and retrieve it
        data = self.cache.get(key=key)

        if data is None:
            self.logger.debug(f"Cache miss {key}")
            data = self.generate_solution(quesion, question_content)

            # Store data in the cache
            if data:
                self.cache.set(key=key, value=data)
        else:
            self.logger.debug(f"Cache hit {key}")

        return data
