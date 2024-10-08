import json
import os

from logging import Logger
from utils.Config import Config

class FileCache:
    def __init__(
        self,
        config: Config,
        logger: Logger):

        self.config = config
        self.logger = logger

    def key_to_path(self, key):
        path = os.path.join(self.config.cache_directory, f"{key}.json")
        return path

    def get(self, key):
        path = self.key_to_path(key)

        with open(path, "r") as file:
            value = file.read()
        return value


    def set(self, key, value):
        path = self.key_to_path(key)

        with open(path, 'w') as file:
            file.write(value)
