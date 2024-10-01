import os
import re
import shutil
import markdown

class LeetcodeUtility:
    SUBMISSIONS_API_URL = "https://leetcode.com/api/submissions/?offset={}&limit={}"
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

    LEETCODE_HEADERS = DEFAULT_HEADERS

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

    def clear():
        current_os = sys.platform
        
        if current_os.startswith('darwin'):
            os.system('clear')
        elif current_os.startswith('linux'):
            os.system('clear')
        elif current_os.startswith('win32') or current_os.startswith('cygwin'):
            os.system('cls')


    def copy_question_file(save_path, question_id, question_title, dest_dir, copy_pdf = True, copy_videos = False):
        questions_dir = os.path.join(save_path, "questions")
        question_filename = LeetcodeUtility.question_html(question_id, question_title)
        question_filepath = os.path.join(questions_dir, question_filename)

        # logger.info(f"Copying {question_filepath} to {dest_dir}")

        if not os.path.exists(question_filepath):
            # logger.error(f"File not found: {question_filepath}")
            return False

        if not os.path.exists(dest_dir):
            # logger.error(f"Destination not found: {dest_dir}")
            return False

        # Copy html
        destination_filepath = os.path.join(dest_dir, question_filename)
        shutil.copy2(question_filepath, destination_filepath)

        question_id_str = LeetcodeUtility.qstr(question_id)

        # Copy images
        images_dir = os.path.join(questions_dir, "images")
        dest_images_dir = os.path.join(dest_dir, "images")
        os.makedirs(dest_images_dir, exist_ok=True)

        for filename in os.listdir(images_dir):
            if filename.startswith(question_id_str):
                source_imagepath = os.path.join(images_dir, filename)
                dest_imagepath = os.path.join(dest_images_dir, filename)
                shutil.copy2(source_imagepath, dest_imagepath)

        # Copy pdf
        if copy_pdf:
            question_basename = LeetcodeUtility.question_id_title(question_id, question_title)
            pdf_dir = os.path.join(save_path, "questions_pdf")
            dest_pdf_dir = os.path.join(dest_dir, "questions_pdf")

            os.makedirs(dest_pdf_dir, exist_ok=True)
            question_filepath = os.path.join(pdf_dir, f"{question_basename}.pdf")
            destination_filepath = os.path.join(dest_pdf_dir, f"{question_basename}.pdf")
            
            if os.path.exists(question_filepath):
                shutil.copy2(question_filepath, destination_filepath)

        # Copy videos
        if copy_videos:
            videos_dir = os.path.join(questions_dir, "videos")
            dest_videos_dir = os.path.join(dest_dir, "videos")
            os.makedirs(dest_videos_dir, exist_ok=True)
            for filename in os.listdir(videos_dir):
                if filename.startswith(question_id_str):
                    source_imagepath = os.path.join(videos_dir, filename)
                    dest_imagepath = os.path.join(dest_videos_dir, filename)
                    shutil.copy2(source_imagepath, dest_imagepath)
        
        return True

    def html_toquestion(filename):
        filename = os.path.basename(filename)

        # Remove the file extension
        name, _ = os.path.splitext(filename)
        
        # Split the string on the first dash and strip whitespace
        try:
            question_id, question_title = name.split('-', 1)
            question_id = int(question_id.strip())
            question_title = question_title.strip()
            
            return question_id, question_title
        except ValueError:
            raise ValueError(f"Filename format is incorrect: {filename}")

    def qstr(question_id):
        return f"{question_id:04}"

    def question_html(question_id, queston_title):
        return f"{LeetcodeUtility.question_id_title(question_id, queston_title)}.html"

    def question_id_title(question_id, queston_title):
        return f"{LeetcodeUtility.qstr(question_id)}-{queston_title}"

    def get_script_dir():
        # Get the absolute path to the script
        script_path = os.path.abspath(__file__)

        # Get the directory containing the script
        script_dir = os.path.dirname(script_path)

        return script_dir

    def convert_display_math_to_inline(content):
        # Strip spaces inside $$ ... $$ and convert it to $ ... $
        content = re.sub(r'\$\$\s*(.*?)\s*\$\$', r'$\1$', content)
        return content

    # Function to clean up math expressions
    def clean_tex_math(content):
        # Replace \space with a regular space
        return re.sub(r'\\space', ' ', content)

    def markdown_with_math(content):
        content = LeetcodeUtility.convert_display_math_to_inline(content)
        content = LeetcodeUtility.clean_tex_math(content)

        # Convert Markdown to HTML and ensure TeX math is not escaped
        return markdown.markdown(
            content,
            extensions=['extra', 'mdx_math'])

    def markdown_with_iframe(content):
        return LeetcodeUtility.markdown_with_math(content)
    
    def replace_filename(str):
        numDict = {':': ' ', '?': ' ', '|': ' ', '>': ' ', '<': ' ', '/': ' ', '\\': ' '}
        return numDict[str.group()]

    def get_cache_path(save_path, category, filename):
        data_dir = os.path.join(save_path, "cache", category)
        os.makedirs(data_dir, exist_ok=True)

        data_path = os.path.join(data_dir, filename)
        return data_path
    
    def get_header():
        filepath = os.path.join(LeetcodeUtility.get_script_dir(), "leetheader.txt")
        with open(filepath, "r") as file:
            data = file.read()

        return data
