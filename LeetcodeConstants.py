import os
from requests.structures import CaseInsensitiveDict

class LeetcodeConstants:
    SUBMISSIONS_API_URL = "https://leetcode.com/api/submissions/?offset={}&limit={}"
    
    LEETCODE_URL = "https://leetcode.com"
    LEETCODE_GRAPHQL_URL = "https://leetcode.com/graphql"

    # Define default config with all necessary keys
    DEFAULT_CONFIG = {}

    DEFAULT_HEADERS = CaseInsensitiveDict({
        "content-type": "application/json",
        "cookie": "",
        "referer": "https://leetcode.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"
        # "accept-encoding": "gzip, deflate, br, zstd"
    })

    LEETCODE_HEADERS = CaseInsensitiveDict(DEFAULT_HEADERS.copy())

    OS_ROOT = os.path.expanduser('~')
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

    FILE_EXTENSIONS = {
        "python": "py",
        "python3": "py",
        "pythondata": "pd.py",
        "c": "c",
        "cpp": "cpp",
        "csharp": "cs",
        "java": "java",
        "kotlin": "kt",
        "mysql": "sql",
        "mssql": "sql",
        "oraclesql": "sql",
        "javascript": "js",
        "html": "html",
        "php": "php",
        "golang": "go",
        "scala": "scala",
        "pythonml": "py",
        "rust": "rs",
        "ruby": "rb",
        "bash": "sh",
        "swift": "swift",
    }

    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

    @property
    def HTML_HEADER():
        filepath = os.path.join(LeetcodeConstants.SCRIPT_DIR, "leetheader.txt")
        with open(filepath, "r") as file:
            data = file.read()

        return data
