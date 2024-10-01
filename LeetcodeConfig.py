import json
from dataclasses import dataclass
import os

@dataclass
class LeetcodeConfig:
    leetcode_cookie: str
    cards_filepath: str
    questions_filepath: str
    save_directory: str
    cache_directory: str
    cache_api_calls: bool
    overwrite: bool
    company_filepath: str
    preferred_language_order: str
    include_submissions_count: int
    include_default_code: bool
    extract_gif_frames: bool
    recompress_image: bool
    base64_encode_image: bool
    download_images: bool
    download_videos: bool

    @staticmethod
    def from_json_file(json_file: str) -> 'LeetcodeConfig':
        with open(json_file, "r") as file:
            return LeetcodeConfig.from_json(file.read())

    @staticmethod
    def from_json(json_str: str) -> 'LeetcodeConfig':
        data = json.loads(json_str)
        return LeetcodeConfig(
            leetcode_cookie=data.get("leetcode_cookie", ""),
            cards_filepath=data.get("cards_filepath", ""),
            questions_filepath=data.get("questions_filepath", ""),
            company_filepath=data.get("company_filepath", ""),
            save_directory=data.get("save_directory", ""),
            cache_directory=data.get("cache_directory", ""),
            cache_api_calls=data.get("cache_api_calls", True),
            overwrite=data.get("overwrite", False),
            preferred_language_order=data.get("preferred_language_order", ""),
            include_submissions_count=data.get("include_submissions_count", 0),
            include_default_code=data.get("include_default_code", False),
            extract_gif_frames=data.get("extract_gif_frames", False),
            recompress_image=data.get("recompress_image", False),
            base64_encode_image=data.get("base64_encode_image", False),
            download_images=data.get("download_images", True),
            download_videos=data.get("download_videos", False),
        )

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