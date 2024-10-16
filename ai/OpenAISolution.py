from logging import Logger

from diskcache import Cache
from openai import OpenAI

from ai.AISolution import AISolution
from ai.OpenAIPrompt import OpenAIPrompt
from api.ApiManager import ApiManager
from utils.Config import Config

class OpenAISolution(AISolution):
    def __init__(
        self,
        config: Config,
        logger: Logger,
        leetapi: ApiManager,
        cache: Cache):

        AISolution.__init__(self, config, logger, leetapi, cache)       
        self.client = OpenAI(api_key=self.config.open_ai_api_key)
        self.prompt_gen = OpenAIPrompt(
            config=config,
            logger=logger,
            leetapi=leetapi)


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
