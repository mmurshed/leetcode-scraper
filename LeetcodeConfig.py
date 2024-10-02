import json
from dataclasses import dataclass
import os

@dataclass
class LeetcodeConfig:
    leetcode_cookie: str = ""
    cards_filepath: str = ""
    questions_filepath: str = ""
    save_directory: str = ""
    cache_directory: str = ""
    cards_directory: str = ""
    companies_directory: str = ""
    questions_directory: str = ""
    submissions_directory: str = ""
    cache_api_calls: bool = True
    cache_expiration_days: int = 7
    cache_expiration_seconds: int = 7 * 24 * 60 * 60
    overwrite: bool = True
    company_filepath: str = ""
    preferred_language_order: str = "all"
    include_submissions_count: int = 0
    include_default_code: bool = False
    extract_gif_frames: bool = False
    recompress_image: bool = False
    base64_encode_image: bool = False
    download_images: bool = True
    download_videos: bool = False
    number_of_threads_for_pdf_conversion: int = 8

    def __init__(self, **kwargs):
        # Dynamically update the attributes from kwargs
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    @staticmethod
    def from_json(json_str: str) -> 'LeetcodeConfig':
        data = json.loads(json_str)
        return LeetcodeConfig(**data)

    @staticmethod
    def from_json_file(json_file: str) -> 'LeetcodeConfig':
        with open(json_file, "r") as file:
            return LeetcodeConfig.from_json(file.read())

    def to_json(self) -> str:
        return json.dumps(self.__dict__, indent=4)

    def to_json_file(self, json_file):
        with open(json_file, "w") as file:
            file.write(self.to_json())

    def set_derivative_values(self):
        self.cards_filepath = os.path.join(self.save_directory, "cards.csv")
        self.questions_filepath = os.path.join(self.save_directory, "questions.csv")
        self.company_filepath = os.path.join(self.save_directory, "company.csv")
        self.cache_directory = os.path.join(self.save_directory, "cache")
        self.cards_directory = os.path.join(self.save_directory, "cards")
        self.companies_directory = os.path.join(self.save_directory, "companies")
        self.questions_directory = os.path.join(self.save_directory, "questions")
        self.submissions_directory = os.path.join(self.save_directory, "submissions")
        self.cache_expiration_seconds = self.cache_expiration_days * 24 * 60 * 60

    @staticmethod
    def prompt_from_dataclass():
        # Default prompts based on the fields of the LeetCodeConfig class
        prompts = {
            "leetcode_cookie": "Enter the LEETCODE_SESSION Cookie Value: ",
            "save_directory": "Enter Save Path: ",
            "overwrite": "Download again even if the file exists T/F? (T/F): ",
            "download_images": "Download images T/F? (T/F): ",
            "download_videos": "Download videos T/F? (T/F): ",
            "preferred_language_order": "Enter order of preferred languages (comma-separated or all): ",
            "include_submissions_count": "How many submissions to include (0 for none): ",
        }
        return prompts