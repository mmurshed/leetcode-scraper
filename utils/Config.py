import json
from dataclasses import dataclass
import os

@dataclass
class Config:
    def __init__(self, **kwargs):
        self.leetcode_cookie = ""
        self.save_directory: str = ""
        self.cache_directory: str = ""
        self.cards_directory: str = ""
        self.companies_directory: str = ""
        self.questions_directory: str = ""
        self.submissions_directory: str = ""
        self.cache_api_calls: bool = True
        self.cache_expiration_days: int = 7
        self.overwrite: bool = True
        self.preferred_language_order: list = ["all"]
        self.include_submissions_count: int = 0
        self.include_community_solution_count: int = 1
        self.include_default_code: bool = False
        self.extract_gif_frames: bool = False
        self.recompress_image: bool = False
        self.base64_encode_image: bool = False
        self.download_images: bool = True
        self.download_videos: bool = False
        self.threads_count_for_pdf_conversion: int = 8
        self.api_max_failures = 3

        self.generate_ai_solution = False
        self.open_ai_api_key = ""
        self.open_ai_model = "gpt-4o-mini"

        # Dynamically update the attributes from kwargs
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    @staticmethod
    def from_json(json_str: str) -> 'Config':
        data = json.loads(json_str)
        return Config(**data)

    @staticmethod
    def from_json_file(json_file: str) -> 'Config':
        with open(json_file, "r") as file:
            return Config.from_json(file.read())

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

    @staticmethod
    def prompt_from_dataclass():
        # Default prompts based on the fields of the LeetCodeConfig class
        prompts = {
            "leetcode_cookie": "Enter the LEETCODE_SESSION Cookie Value: ",
            "save_directory": "Enter directory where files should be saved: ",
            "overwrite": "Download again even if the file exists T/F? (T/F): ",
            "download_images": "Download images T/F? (T/F): ",
            "download_videos": "Download videos T/F? (T/F): ",
            "preferred_language_order": "Enter order of preferred languages for solution (comma-separated or all): ",
            "generate_ai_solution": "Generate AI solution when missing T/F? (T/F): ",
            "open_ai_api_key": "Open AI API Key for generating solution (required only if you want to generate AI solution)",
            "include_submissions_count": "How many submissions to include (0 for none): ",
            "include_community_solution_count": "How many community solutions to include (0 for none): ",
            "cache_api_calls": "Should the API calls be cached T/F? (T/F): "
        }
        return prompts
    
    @staticmethod
    def get_images_dir(directory):
        return os.path.join(directory, "images")
    
