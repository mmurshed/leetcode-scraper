import os
import json
from dataclasses import dataclass

@dataclass
class LeetcodeConfig:
    leetcode_cookie: str
    cards_url_path: str
    questions_url_path: str
    save_path: str
    cache_data: bool
    force_download: bool
    company_tag_save_path: str
    preferred_language_order: str
    include_submissions_count: int
    include_default_code: bool
    convert_to_pdf: bool
    extract_gif_frames: bool
    recompress_image: bool
    base64_encode_image: bool
    download_images: bool
    download_videos: bool

    @staticmethod
    def from_json(json_str: str) -> 'LeetcodeConfig':
        data = json.loads(json_str)
        return LeetcodeConfig(
            leetcode_cookie=data.get("leetcode_cookie", ""),
            cards_url_path=data.get("cards_url_path", ""),
            questions_url_path=data.get("questions_url_path", ""),
            save_path=data.get("save_path", ""),
            cache_data=data.get("cache_data", False),
            force_download=data.get("force_download", False),
            company_tag_save_path=data.get("company_tag_save_path", ""),
            preferred_language_order=data.get("preferred_language_order", ""),
            include_submissions_count=data.get("include_submissions_count", 0),
            include_default_code=data.get("include_default_code", False),
            convert_to_pdf=data.get("convert_to_pdf", False),
            extract_gif_frames=data.get("extract_gif_frames", False),
            recompress_image=data.get("recompress_image", False),
            base64_encode_image=data.get("base64_encode_image", False),
            download_images=data.get("download_images", False),
            download_videos=data.get("download_videos", False),
        )

    def to_json(self) -> str:
        return json.dumps(self.__dict__, indent=4)
    
    @staticmethod
    def prompt_from_dataclass():
        # Default prompts based on the fields of the LeetCodeConfig class
        prompts = {
            "leetcode_cookie": "Enter the LEETCODE_SESSION Cookie Value: ",
            "cards_url_path": "Enter Cards URL Save Path: ",
            "questions_url_path": "Enter Questions URL Save Path: ",
            "save_path": "Enter Save Path: ",
            "company_tag_save_path": "Enter Company Tag Save Path: ",
            "cache_data": "Cache temporary data files locally T/F? (T/F): ",
            "force_download": "Download again even if the file exists T/F? (T/F): ",
            "preferred_language_order": "Enter order of preferred languages (comma-separated): ",
            "include_submissions_count": "How many submissions to include (0 for none): ",
            "include_default_code": "Include default code section? (T/F): ",
            "convert_to_pdf": "Convert to pdf? (T/F): "
        }
        return prompts