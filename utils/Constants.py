import os
from requests.structures import CaseInsensitiveDict

class Constants:
    SUBMISSIONS_API_URL = "https://leetcode.com/api/submissions/?offset={}&limit={}"
    LEETCODE_URL = "https://leetcode.com"
    LEETCODE_GRAPHQL_URL = "https://leetcode.com/graphql"

    OS_ROOT = os.path.expanduser('~')
    ROOT_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

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

    LANG_NAMES = {
        "all": "Python, Java",
        "python": "python",
        "python3": "python 3",
        "c": "C",
        "cpp": "C++",
        "csharp": "C#",
        "java": "Java",
        "kotlin": "Kotlin",
        "mysql": "SQL",
        "mssql": "SQL",
        "oraclesql": "SQL",
        "javascript": "JavaScript",
        "html": "HTML",
        "php": "PHP",
        "golang": "Go",
        "scala": "Scala",
        "pythonml": "Python",
        "rust": "Rust",
        "ruby": "Ruby",
        "bash": "Bash",
        "swift": "Swift",
    }

    LANG_NAMES_TO_SLUG = {
        "python 3": "python",
        "c++": "cpp",
        "c#": "csharp",
        "sql": "mysql",
        "go": "golang",
    }

    HTML_HEADER = None

    ASSETS_DIR = None

    TEX_TEMPLATE_PATH = None
    TEX_HEADER_PATH = None

    OPEN_AI_PROMPT = None
    OLLAMA_PROMPT = None

    @staticmethod
    def get_assets_dir():
        return os.path.join(Constants.ROOT_DIR, "assets")

    @staticmethod
    def get_tex_template_path():
        filepath = os.path.join(Constants.ASSETS_DIR, "template.latex")
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"The file '{filepath}' does not exist.")
        return filepath

    @staticmethod
    def get_tex_header_path():
        filepath = os.path.join(Constants.ASSETS_DIR, "enumitem.tex")
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"The file '{filepath}' does not exist.")
        return filepath

    @staticmethod
    def get_html_header():
        filepath = os.path.join(Constants.ASSETS_DIR, "header.txt")
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"The file '{filepath}' does not exist.")
        with open(filepath, "r") as file:
            data = file.read()

        return data


    @staticmethod
    def get_open_ai_prompt():
        filepath = os.path.join(Constants.ASSETS_DIR, "opanaiprompt.txt")
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"The file '{filepath}' does not exist.")
        with open(filepath, "r") as file:
            data = file.read()

        return data

    @staticmethod
    def get_ollama_prompt():
        filepath = os.path.join(Constants.ASSETS_DIR, "ollamaprompt.txt")
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"The file '{filepath}' does not exist.")
        with open(filepath, "r") as file:
            data = file.read()

        return data

    #region headers
    @staticmethod
    def create_headers(leetcode_cookie=""):
        headers = Constants.DEFAULT_HEADERS
        headers["cookie"] = f"LEETCODE_SESSION={leetcode_cookie}"
        return headers
    
    DEFAULT_HEADERS = CaseInsensitiveDict({
        "content-type": "application/json",
        "cookie": "LEETCODE_SESSION=",
        "referer": "https://leetcode.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"
    })

    IMAGE_HEADERS = CaseInsensitiveDict({
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0",
        "accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8"
    })

    LEETCODE_HEADERS = CaseInsensitiveDict(DEFAULT_HEADERS.copy())

    #endregion headers

Constants.ASSETS_DIR = Constants.get_assets_dir()
Constants.HTML_HEADER = Constants.get_html_header()
Constants.TEX_TEMPLATE_PATH = Constants.get_tex_template_path()
Constants.TEX_HEADER_PATH = Constants.get_tex_header_path()
Constants.OPEN_AI_PROMPT = Constants.get_open_ai_prompt()
Constants.OLLAMA_PROMPT = Constants.get_ollama_prompt()