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
        self.download_questions: str = "new"  # Options: "none", "always", "new"
        self.preferred_language_order: list = ["all"]
        self.include_submissions_count: int = 0
        self.include_community_solution_count: int = 1
        self.include_default_code: bool = False
        self.extract_gif_frames: bool = False
        self.recompress_image_formats: list = ["webp"]  # Options: "png", "jpg", "webp"
        self.base64_encode_image: bool = False
        self.download_images: str = "new"  # Options: "none", "always", "new"
        self.download_videos: str = "new"  # Options: "none", "always", "new"
        self.threads_count_for_pdf_conversion: int = 8
        self.api_max_failures = 3

        self.logging_level = "warning" # Options: "debug", "info", "warning", "error"

        # None, ollama or openai
        self.ai_solution_generator = None # Options: "none", "ollama", "openai"

        self.open_ai_api_key = ""
        self.open_ai_model = "gpt-5-mini"

        self.ollama_url = "http://localhost:11434/api/generate"
        self.ollama_model = "llama3.1"

        # Dynamically update the attributes from kwargs
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        # Migrate old boolean values to new string format
        self._migrate_boolean_fields()

        self.set_derivative_values()

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
            "download_questions": "Download questions: new, always? (new): ",
            "download_images": "Download images: none, new, always? (new): ",
            "download_videos": "Download videos: none, new, always? (new): ",
            "preferred_language_order": "Enter order of preferred languages for solution (comma-separated or all): ",
            "include_submissions_count": "How many submissions to include (0 for none): ",
            "include_community_solution_count": "How many community solutions to include (0 for none): ",
            "cache_api_calls": "Should the API calls be cached T/F? (T/F): "
        }
        return prompts
    
    @staticmethod
    def get_images_dir(directory):
        return os.path.join(directory, "images")
    
    def _migrate_boolean_fields(self):
        """Migrate old boolean values to new string format for backward compatibility."""
        # Migrate overwrite/download_questions: True -> "always", False -> "new"
        # Also handle old "overwrite" field name
        if hasattr(self, 'overwrite'):
            if isinstance(self.overwrite, bool):
                self.download_questions = "always" if self.overwrite else "new"
            else:
                self.download_questions = self.overwrite
            # Remove old attribute
            delattr(self, 'overwrite')
        elif isinstance(self.download_questions, bool):
            self.download_questions = "always" if self.download_questions else "new"
        
        # Migrate download_images: True -> "new", False -> "none"
        if isinstance(self.download_images, bool):
            self.download_images = "new" if self.download_images else "none"
        
        # Migrate download_videos: True -> "new", False -> "none"
        if isinstance(self.download_videos, bool):
            self.download_videos = "new" if self.download_videos else "none"
        
        # Migrate recompress_image (old name) to recompress_image_formats
        if hasattr(self, 'recompress_image'):
            if isinstance(self.recompress_image, bool):
                self.recompress_image_formats = ["webp"] if self.recompress_image else []
            elif isinstance(self.recompress_image, list):
                self.recompress_image_formats = self.recompress_image
            # Remove old attribute
            delattr(self, 'recompress_image')
        # Also handle if recompress_image_formats was somehow set as bool
        elif isinstance(self.recompress_image_formats, bool):
            self.recompress_image_formats = ["webp"] if self.recompress_image_formats else []

