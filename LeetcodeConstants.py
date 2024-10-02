import os
from requests.structures import CaseInsensitiveDict

from LeetcodeUtility import LeetcodeUtility

class LeetcodeConstants:
    SUBMISSIONS_API_URL = "https://leetcode.com/api/submissions/?offset={}&limit={}"
    LEETCODE_URL = "https://leetcode.com"
    LEETCODE_GRAPHQL_URL = "https://leetcode.com/graphql"

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

    HTML_HEADER = None

    @staticmethod
    def get_html_header():
        filepath = os.path.join(LeetcodeConstants.ROOT_DIR, "leetheader.txt")
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"The file '{filepath}' does not exist.")
        with open(filepath, "r") as file:
            data = file.read()

        return data

    #region headers
    @staticmethod
    def create_headers(leetcode_cookie=""):
        headers = LeetcodeConstants.DEFAULT_HEADERS
        headers["cookie"] = f"LEETCODE_SESSION={leetcode_cookie}"
        return headers
    
    DEFAULT_HEADERS = CaseInsensitiveDict({
        "content-type": "application/json",
        "cookie": "LEETCODE_SESSION=",
        "referer": "https://leetcode.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"
        # "accept-encoding": "gzip, deflate, br, zstd"
    })

    LEETCODE_HEADERS = CaseInsensitiveDict(DEFAULT_HEADERS.copy())

    #endregion headers

LeetcodeConstants.HTML_HEADER = LeetcodeConstants.get_html_header()