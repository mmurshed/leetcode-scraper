import json
from logging import Logger

from diskcache import Cache
import requests

from ai.AISolution import AISolution
from ai.OllamaPrompt import OllamaPrompt
from utils.Config import Config

class OllamaSolution(AISolution):
    def __init__(
        self,
        config: Config,
        logger: Logger,
        cache: Cache):
        
        AISolution.__init__(self, config, logger, cache)       

        self.prompt_gen = OllamaPrompt(
            config=config,
            logger=logger)
        
    def submit(self, text):
        try:
            data = {
                'model': self.config.ollama_model,
                'prompt': text,
                'stream': False,
                'system': 'You are an editor for a blog providing solution in an easy to understand language and step by step approach to programming problems that appear in software engineering job interviews.',
                'options': {
                    'num_predict': -1
                }
            }

            self.logger.debug(f"Ollama data:\n{json.dumps(data)}")

            response = requests.post(
                url=self.config.ollama_url,
                json=data)
            
            response.raise_for_status()

            return response.json()['response']
        except Exception as e:
            self.logger.error(f"An error occurred: {e}")


