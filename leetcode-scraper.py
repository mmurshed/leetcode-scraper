import requests
import json
from requests.structures import CaseInsensitiveDict
from bs4 import BeautifulSoup
import markdown
import re
import base64
import os
import sys
import shutil
import argparse
import csv
import hashlib
import validators
import datetime
from urllib.parse import urlparse, urlsplit
from PIL import Image
import cloudscraper
import pypandoc
import yt_dlp

import logging
from logging.handlers import RotatingFileHandler

import yt_dlp.downloader

# Set up logging
log_file = 'scrape_errors.log'
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Leet")
handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=2)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

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
    global current_os
    if current_os.startswith('darwin'):
        os.system('clear')
    elif current_os.startswith('linux'):
        os.system('clear')
    elif current_os.startswith('win32') or current_os.startswith('cygwin'):
        os.system('cls')


def create_base_config_dir():
    base_config_path = os.path.join(OS_ROOT, ".leetcode-scraper")
    os.makedirs(base_config_path, exist_ok=True)
    return base_config_path


def select_config():
    global selected_config
    base_config_path = create_base_config_dir()
    print("\nIf you are creating a new config, Please select 1 in Main Menu to setup the new config\n")

    if len(os.listdir(base_config_path)) > 0:
        for configs in os.listdir(base_config_path):
            if ".json" in configs:
                print(configs)
        selected_config = input(
            "\nSelect a config or Enter a number to create a new config: ") or "0"


def generate_config():
    clear()
    base_config_path = create_base_config_dir()
    config_file_path = os.path.join(base_config_path, f"config_{selected_config}.json")
    print(f'''
        Leave Blank and press Enter if you don't want to overwrite Previous Values
        Config Save Folder: {config_file_path}
    ''')

    # Try to load existing config, or initialize empty config if it doesn't exist
    config = DEFAULT_CONFIG
    try:
        config = load_config_dict()
    except Exception:
        print('''
            Config doesn't exist, creating a new one.
            Enter the paths for your config:
        ''')

    # Default configuration keys and their prompts
    config_prompts = {
        "leetcode_cookie": "Enter the LEETCODE_SESSION Cookie Value: ",
        "cards_url_path": "Enter Cards URL Save Path: ",
        "questions_url_path": "Enter Questions URL Save Path: ",
        "save_path": "Enter Save Path: ",
        "company_tag_save_path": "Enter Company Tag Save Path: ",
        "cache_data": "Cache temporary data files locally T/F? (T/F): ",
        "force_download": "Download again even if the file exists T/F? (T/F): ",
        "preferred_language_order": "Enter order of the preferred solution language (all or a command separate list of languages c, cpp, csharp, java, python3, javascript, typescript, golang): ",
        "include_submissions_count": "How many of your own submissions should be incldued (0 for none, a large integer for all): ",
        "include_default_code": "Include default code section? (T/F): ",
        "convert_to_pdf": "Convert to pdf? (T/F): "
    }

    # Prompt user for values and retain existing config if no new input is provided
    for key, prompt in config_prompts.items():
        if "T/F" in prompt:
            config[key] = bool(input(prompt) == 'T') if input(prompt) else config.get(key, False)
        else:
            config[key] = input(prompt) or config.get(key, "")

    # Write config to JSON file
    with open(config_file_path, "w") as config_file:
        json.dump(config, config_file, indent=4)

def load_default_config():
    config_path = os.path.join(get_script_dir(), "defaultconfig.json")

    # Check if config file exists
    if not os.path.exists(config_path):
        raise Exception("Default config not found.")

    # Load the JSON config file
    with open(config_path, "r") as config_file:
        config = json.load(config_file)

    return config

def load_config_dict():
    global selected_config
    config_dir = os.path.join(OS_ROOT, ".leetcode-scraper")
    config_path = os.path.join(config_dir, f"config_{selected_config}.json")

    # Check if config file exists
    if not os.path.exists(config_path):
        raise Exception("No config found, please create one")

    # Load the JSON config file
    with open(config_path, "r") as config_file:
        config = json.load(config_file)

    # Use the default config for missing fields
    for key in DEFAULT_CONFIG:
        config[key] = config.get(key, DEFAULT_CONFIG[key])

    return config

def load_config(config = None):
    if not config:
        config = load_config_dict()
    
    # Dynamically create an anonymous class with attributes from config
    config_class = type('Config', (object,), config)
    return config_class()

def create_headers(leetcode_cookie=""):
    headers = DEFAULT_HEADERS
    headers["cookie"] = f"LEETCODE_SESSION={leetcode_cookie}"
    return headers

def get_cache_path(category, filename):
    data_dir = os.path.join(CONFIG.save_path, "cache", category)
    os.makedirs(data_dir, exist_ok=True)

    data_path = os.path.join(data_dir, filename)

    return data_path

def copy_question_file(question_id, question_title, dest_dir, copy_pdf = True, copy_videos = False):
    questions_dir = os.path.join(CONFIG.save_path, "questions")
    question_filename = question_html(question_id, question_title)
    question_filepath = os.path.join(questions_dir, question_filename)

    logger.info(f"Copying {question_filepath} to {dest_dir}")

    if not os.path.exists(question_filepath):
        logger.error(f"File not found: {question_filepath}")
        return False

    if not os.path.exists(dest_dir):
        logger.error(f"Destination not found: {dest_dir}")
        return False

    # Copy html
    destination_filepath = os.path.join(dest_dir, question_filename)
    shutil.copy2(question_filepath, destination_filepath)

    question_id_str = qstr(question_id)

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
        question_basename = question_id_title(question_id, question_title)
        pdf_dir = os.path.join(CONFIG.save_path, "questions_pdf")
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


def extract_by_selector(response_content, selector):
    """
    Navigate through the response_content using the keys and/or indices in the selector.
    The selector can contain both dictionary keys (strings) and list indices (integers).
    """
    data = response_content

    for key in selector:
        # Check if the current element is a dictionary and the key is a string
        if isinstance(data, dict) and isinstance(key, str):
            if key in data:
                data = data[key]
            else:
                raise KeyError(f"Key '{key}' not found in response_content")
        # Check if the current element is a list and the key is an integer (index)
        elif isinstance(data, list) and isinstance(key, int):
            try:
                data = data[key]
            except IndexError:
                raise IndexError(f"Index '{key}' out of range in response_content list")
        else:
            raise ValueError(f"Unexpected type for key: {key}. Expected str for dict or int for list.")

    return data


def cached_query(data_path, method="post", query=None, selector=None, url=LEETCODE_GRAPHQL_URL, headers=LEETCODE_HEADERS):
    """
    This function caches and performs a query if data is not already cached.
    Optionally uses a selector to filter out the required part of the response.
    The file_type is inferred based on the response's Content-Type header.
    """
    data = None

    # Check if data exists in the cache and try to read it
    if CONFIG.cache_data and os.path.exists(data_path):
        with open(data_path, "r") as file:
            try:
                data = json.load(file)  # Try reading the cached data as JSON
            except json.JSONDecodeError:
                data = file.read()  # If not JSON, read as plain text
    else:
        response = REQ_SESSION.request(
            method=method,
            url=url,
            headers=headers,
            json=query
        )

        response.raise_for_status()

        # Infer the file_type from the Content-Type header
        content_type = response.headers.get('Content-Type', '').lower()
        is_json = 'application/json' in content_type

        try:
            if is_json:
                # Parse the JSON response
                response_content = json.loads(response.content)
                data = response_content
                # Use the selector to get the desired data if applicable
                if selector:
                    data = extract_by_selector(response_content, selector)
            else:
                # Treat the response as raw text if it's not JSON
                data = response.text
        except Exception as e:
            raise Exception(f"Error in getting data: {e}\n"
                            f"data_path: {data_path}\n"
                            f"method: {method}\n"
                            f"url: {url}\n"
                            f"query: {query}\n"
                            f"selector: {selector}")

        # Cache the data to the file if available
        if data:
            try:
                with open(data_path, 'w') as f:
                    if is_json:
                        json.dump(data, f)
                    else:
                        f.write(data)
            except IOError as e:
                raise Exception(f"Error writing to file: {data_path}. Exception: {e}")

    return data

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
    return f"{question_id_title(question_id, queston_title)}.html"

def question_id_title(question_id, queston_title):
    return f"{qstr(question_id)}-{queston_title}"

def get_script_dir():
    # Get the absolute path to the script
    script_path = os.path.abspath(__file__)

    # Get the directory containing the script
    script_dir = os.path.dirname(script_path)

    return script_dir

def convert_html_to_pdf(question_id, question_title, overwrite):
    script_dir = get_script_dir()

    base_name = question_id_title(question_id, question_title)
    html_filename = question_html(question_id, question_title)
    question_dir = os.path.join(CONFIG.save_path, "questions")
    images_dir = os.path.join(question_dir, "images")

    html_path = os.path.join(question_dir, html_filename)

    if not os.path.exists(html_path):
        raise Exception(f"html file doesn't exist {html_path}")
    
    logger.info(f"Converting to pdf: {html_path}")

    docx_dir = os.path.join(CONFIG.save_path, "cache", "docx")
    pdf_dir = os.path.join(CONFIG.save_path, "questions_pdf")
    os.makedirs(docx_dir, exist_ok=True)
    os.makedirs(pdf_dir, exist_ok=True)

    docx_path = os.path.join(docx_dir, f"{base_name}.docx",)
    pdf_path = os.path.join(pdf_dir, f"{base_name}.pdf")
    
    if overwrite or not os.path.exists(docx_path):
        try:
            docxArgs = [
                '--resource-path', images_dir
            ]

            pypandoc.convert_file(
                source_file=html_path,
                to='docx',
                #format='html+tex_math_dollars+tex_math_single_backslash',
                format='html+tex_math_dollars-tex_math_double_backslash',
                outputfile=docx_path,
                extra_args=docxArgs)
        except Exception as e:
            if os.path.exists(docx_path):
                os.remove(docx_path)
            logger.error(f"{docx_path}\n{e}")
            return False

    if not os.path.exists(docx_path):
        logger.error(f"Docx file doesn't exist {docx_path}")
        return False

    if overwrite or not os.path.exists(pdf_path):
        # Define additional arguments
        pdfArgs = [
            # '-V', 'mainfont="Unifont"',
            '-V', 'geometry:margin=0.5in',
            '--pdf-engine=xelatex',
            f'--template={script_dir}/leet-template.latex',
            f'--include-in-header={script_dir}/enumitem.tex',
            '--resource-path', images_dir
        ]

        try:
            pypandoc.convert_file(
                source_file=docx_path,
                to='pdf',
                outputfile=pdf_path,
                extra_args=pdfArgs)
        except Exception as e:
            logger.error(f"{pdf_path}\n{e}")
            return False

    logger.info(f"Removing docx {docx_path}")
    os.remove(docx_path)

    return True


def get_all_cards_url():
    logger.info("Getting all cards url")

    data_path = get_cache_path("cards", "allcards.json")

    query = {
        "operationName": "GetCategories",
        "variables": {
            "num": 1000
        },
        "query": "query GetCategories($categorySlug: String, $num: Int) {\n  categories(slug: $categorySlug) {\n  slug\n    cards(num: $num) {\n ...CardDetailFragment\n }\n  }\n  }\n\nfragment CardDetailFragment on CardNode {\n   slug\n  categorySlug\n  }\n"
    }
    selector = ['data', 'categories']

    cards = cached_query(
        data_path=data_path,
        query=query,
        selector=selector)

    with open(CONFIG.cards_url_path, "w") as f:
        for category_card in cards:
            if category_card['slug'] != "featured":
                for card in category_card['cards']:
                    card_url = "https://leetcode.com/explore/" + \
                        card['categorySlug'] + "/card/" + card['slug'] + "/\n"
                    f.write(card_url)


def get_all_questions_url(force_download):
    logger.info("Getting all questions url")

    data_path = get_cache_path("qdata", "allquestioncount.json")

    query = {
        "query": "\n query getQuestionsCount {allQuestionsCount {\n    difficulty\n    count\n }} \n    "
    }
    selector = ['data', 'allQuestionsCount', 0,'count']

    all_questions_count = cached_query(
        data_path=data_path,
        query=query,
        selector=selector)
    all_questions_count = int(all_questions_count)

    logger.info(f"Total no of questions: {all_questions_count}")

    data_path = get_cache_path("qdata", "allquestions.json")

    query = {
        "query": "\n query problemsetQuestionList($categorySlug: String, $limit: Int, $skip: Int, $filters: QuestionListFilterInput) {\n  problemsetQuestionList: questionList(\n    categorySlug: $categorySlug\n    limit: $limit\n    skip: $skip\n    filters: $filters\n  ) {\n  questions: data {\n title\n titleSlug\n frontendQuestionId: questionFrontendId\n }\n  }\n}\n    ",
        "variables": {
            "categorySlug": "",
            "skip": 0,
            "limit": all_questions_count,
            "filters": {}
        }
    }

    selector = ['data', 'problemsetQuestionList', 'questions']

    all_questions = cached_query(
        data_path=data_path,
        query=query,
        selector=selector)
    
    if force_download:
        write_questions_to_file(all_questions, CONFIG.questions_url_path)

    return all_questions


def write_questions_to_file(all_questions, questions_url_path):
    with open(questions_url_path, "w") as f:
        for question in all_questions:
            frontendQuestionId = question['frontendQuestionId']
            question_url = "https://leetcode.com/problems/" + \
                question['titleSlug'] + "/\n"
            f.write(f"{frontendQuestionId},{question_url}")


def scrape_question_url():
    all_questions = get_all_questions_url(force_download=CONFIG.force_download)
    questions_dir = os.path.join(CONFIG.save_path, "questions")
    os.makedirs(questions_dir, exist_ok=True)
    os.chdir(questions_dir)

    # Convert the list of questions to a dictionary using titleSlug as the key
    questions_dict = {question['titleSlug']: question for question in all_questions}

    with open(CONFIG.questions_url_path) as f:
        for row in csv.reader(f):
            question_id = int(row[0])
            question_url = row[1]
            question_url = question_url.strip()
            question_slug = question_url.split("/")[-2]

            if question_slug in questions_dict:
                question = questions_dict[question_slug]
                question_title = re.sub(r'[:?|></\\]', replace_filename, question['title'])
            else:
                raise Exception(f"Question id {question_id}, slug {question_slug} not found")

            question_file = question_html(question_id, question_title)
            question_path = os.path.join(questions_dir, question_file)
            
            if CONFIG.force_download or not os.path.exists(question_path):            
                logger.info(f"Scraping question {question_id} url: {question_url}")
                create_question_html(question_id, question_slug, question_title)
            else:
                logger.info(f"Already scraped {question_file}")

        if CONFIG.convert_to_pdf:
            for row in csv.reader(f):
                converted = convert_html_to_pdf(question_id, question_title, overwrite=CONFIG.force_download)
                if not converted:
                    logger.info(f"Compressing images and retrying pdf convert")
                    recompress_images(question_id)
                    converted = convert_html_to_pdf(question_id, question_title, overwrite=True)
            
    with open(os.path.join(questions_dir, "index.html"), 'w') as main_index:
        main_index_html = ""
        for idx, files in enumerate(os.listdir(questions_dir),start=1):
            if "index.html" not in files:
                main_index_html += f"""<a href="{files}">{idx}-{files}</a><br>"""
        main_index.write(main_index_html)
    os.chdir('..')


def create_question_html(question_id, question_slug, question_title):
    item_content = {
        "question": {
            'titleSlug': question_slug,
            'frontendQuestionId': question_id,
            'title': question_title
        }
    }
    content = """<body>"""
    question_content, question_title = get_question_data(item_content)
    content += question_content
    content += """</body>"""
    slides_json = find_slides_json2(content, question_id)
    content = attach_header_in_html() + content
    content_soup = BeautifulSoup(content, 'html.parser')
    content_soup = place_solution_slides(content_soup, slides_json)
    content_soup = fix_image_urls(content_soup, question_id)

    with open(question_html(question_id, question_title), 'w', encoding="utf-8") as f:
        f.write(content_soup.prettify())

def scrape_card_url():
    cards_dir = os.path.join(CONFIG.save_path, "cards")
    os.makedirs(cards_dir, exist_ok=True)
    os.chdir(cards_dir)

    # Creating Index for Card Folder
    with open(os.path.join(cards_dir, "index.html"), 'w') as main_index:
        main_index_html = ""
        with open(CONFIG.cards_url_path, "r") as f:
            card_urls = f.readlines()
            for card_url in card_urls:
                card_url = card_url.strip()
                card_slug = card_url.split("/")[-2]
                main_index_html += f"""<a href={card_slug}/index.html>{card_slug}</a><br>"""        
        main_index.write(main_index_html)

    # Creating HTML for each cards topics
    with open(CONFIG.cards_url_path, "r") as f:
        card_urls = f.readlines()
        for card_url in card_urls:
            card_url = card_url.strip()

            logger.info("Scraping card url: ", card_url)

            card_slug = card_url.split("/")[-2]

            data_path = get_cache_path("cards", f"{card_slug}-detail.json")

            query = {
                "operationName": "GetChaptersWithItems",
                "variables": {
                    "cardSlug": card_slug
                },
                "query": "query GetChaptersWithItems($cardSlug: String!) {\n  chapters(cardSlug: $cardSlug) {\n    ...ExtendedChapterDetail\n   }\n}\n\nfragment ExtendedChapterDetail on ChapterNode {\n  id\n  title\n  slug\n description\n items {\n    id\n    title\n  }\n }\n"
            }
            selector = ['data', 'chapters']

            chapters = cached_query(
                data_path=data_path,
                query=query,
                selector=selector)

            if chapters:
                cards_dir = os.path.join(CONFIG.save_path, "cards", card_slug)
                os.makedirs(cards_dir, exist_ok=True)
                
                create_card_index_html(chapters, card_slug)
                for subcategory in chapters:
                    logger.info("Scraping subcategory: ", subcategory['title'])

                    for item in subcategory['items']:
                        logger.info("Scraping Item: ", item['title'])

                        item_id = item['id']
                        item_title = re.sub(r'[:?|></\\]', replace_filename, item['title'])

                        filename = question_html(item_id, item_title)
                        
                        cards_filepath = os.path.join(cards_dir, filename)

                        if not CONFIG.force_download and os.path.exists(cards_filepath):
                            logger.info(f"Already scraped {cards_filepath}")
                            continue

                        if CONFIG.force_download or not copy_question_file(item_id, item_title, cards_dir):
                            data_path = get_cache_path("cards", f"{card_slug}-{item_id}.json")

                            query = {
                                "operationName": "GetItem",
                                "variables": {
                                    "itemId": item_id
                                },
                                "query": "query GetItem($itemId: String!) {\n  item(id: $itemId) {\n    id\n title\n  question {\n questionId\n frontendQuestionId: questionFrontendId\n   title\n  titleSlug\n }\n  article {\n id\n title\n }\n  htmlArticle {\n id\n  }\n  webPage {\n id\n  }\n  }\n }\n"
                            }
                            selector = ['data', 'item']

                            item_content = cached_query(
                                data_path=data_path,
                                query=query,
                                selector=selector)

                            if item_content:
                                create_card_html(item_content, item_title, item_id)
                os.chdir("..")
    os.chdir('..')


def create_card_html(item_content, item_title, item_id):
    content = """<body>"""
    question_content, _ = get_question_data(item_content)
    content += question_content
    content += get_article_data(item_content, item_title, item_id)
    content += get_html_article_data(item_content, item_title)
    content += """</body>"""
    slides_json = find_slides_json2(content, item_id)
    content = attach_header_in_html() + content
    content_soup = BeautifulSoup(content, 'html.parser')
    content_soup = place_solution_slides(content_soup, slides_json)
    content_soup = fix_image_urls(content_soup, item_id)

    with open(question_html(item_id, item_title), "w", encoding="utf-8") as f:
        f.write(content_soup.prettify())

def is_valid_image(image_path):
    # SVG file is allowed by default
    if image_path.lower().endswith('.svg'):
        return True

    try:
        with Image.open(image_path) as img:
            img.verify()
    except:
        return False
    return True

def decompose_gif(gif_path, filename_no_ext, output_folder):
    # Open the GIF file
    gif = Image.open(gif_path)
    
    frame_paths = []

    # Iterate over each frame in the GIF
    frame_number = 0
    while True:
        try:
            # Save each frame as a separate image
            frame_path = os.path.join(output_folder, f"{filename_no_ext}_{frame_number:03d}.png")
            gif.seek(frame_number)
            gif.save(frame_path, 'PNG')
            frame_number += 1
            frame_paths.append(frame_path)
        except EOFError:
            break
    return frame_paths


def convert_to_uncompressed_png(img_path, img_ext):
    # Open the PNG file
    try:
        if img_ext == 'png':
            with Image.open(img_path) as img:
                # Save the image without compression
                img.save(img_path, 'PNG', compress_level=0)
                logger.debug(f"Decompressed PNG saved at {img_path}")
    except Exception as e:
        logger.error(f"Error reading file {img_path}\n{e}")
        return None

def recompress_images(question_id):
    images_dir = os.path.join(CONFIG.save_path, "questions", "images")

    # Convert the question_id to a zero-padded 4-digit string
    question_id_str = qstr(question_id)

    # Loop through all files in the source folder
    for filename in os.listdir(images_dir):
        if filename.startswith(question_id_str):
            input_image_path = os.path.join(images_dir, filename)
            recompress_image(input_image_path)


def recompress_image(img_path):
    try:
        img_path_lower = img_path.lower()
        # Open the image
        with Image.open(img_path) as img:
            if img_path_lower.endswith('.png'):
                # Save the image with optimization
                img.save(img_path, optimize=True)
                logger.debug(f"Recompressed and overwrote: {img_path}")
            elif img_path_lower.endswith(('.jpg', '.jpeg')):
                # Recompress JPEG with a quality parameter (default is 75, you can adjust)
                img.save(img_path, 'JPEG', quality=85, optimize=True)
                logger.debug(f"Recompressed and overwrote: {img_path}")
    except Exception as e:
        logger.error(f"Error recompressing {img_path}: {e}")
        return

def download_image(question_id, img_url):
    logger.debug(f"Downloading image: {img_url}")

    if not validators.url(img_url):
        logger.error(f"Invalid image url: {img_url}")
        return
    
    images_dir = os.path.join(CONFIG.save_path, "questions", "images")
    os.makedirs(images_dir, exist_ok=True)
    
    parsed_url = urlsplit(img_url)
    basename = os.path.basename(parsed_url.path)

    img_ext = str.lower(basename.split('.')[-1])

    url_hash = hashlib.md5(img_url.encode()).hexdigest()
    image_path = os.path.join(images_dir, f"{question_id_title(question_id, url_hash)}.{img_ext}")

    if not CONFIG.cache_data or not os.path.exists(image_path):
        try:
            img_data = CLOUD_SCRAPER.get(url=img_url).content

            with open(image_path, 'wb') as file:
                file.write(img_data)

            if CONFIG.recompress_image:
                recompress_image(image_path)

        except Exception as e:
            logger.error(f"Error downloading image url: {img_url}")
            return None

    if not is_valid_image(image_path):
        os.remove(image_path)
        logger.error(f"Invalid image file from url: {img_url}")
        return None

    if CONFIG.extract_gif_frames and img_ext == "gif":
        files = decompose_gif(image_path, url_hash, images_dir)
    else:
        files = [image_path]

    return files

def load_image_local(files):
    questions_dir = os.path.join(CONFIG.save_path, "questions")
    relframes = [os.path.relpath(frame, questions_dir) for frame in files]

    return relframes

def load_image_in_b64(files, img_url):
    logger.debug(f"Loading image: {img_url}")

    parsed_url = urlsplit(img_url)
    basename = os.path.basename(parsed_url.path)
    img_ext = str.lower(basename.split('.')[-1])

    if img_ext == "svg":
        img_ext = "svg+xml"

    encoded_string = None

    imgs_decoded = []
    for file in files:
        if not is_valid_image(file):
            continue

        with open(file, "rb") as file:
            img_data = file.read()
            encoded_string = base64.b64encode(img_data)

        if not encoded_string:
            logger.error(f"Error loading image url: {img_url}")
            return None

        decoded_string = encoded_string.decode('utf-8')
        decoded_image = f"data:image/{img_ext};base64,{decoded_string}"
        imgs_decoded.append(decoded_image)

    return imgs_decoded

def fix_image_urls(content_soup, question_id):
    logger.info("Fixing image urls")

    images = content_soup.select('img')

    for image in images:
        logger.debug(f"img[src]: {image['src']}")
        if image.has_attr('src') and "base64" not in image['src']:
            splitted_image_src = image['src'].split('/')

            if ".." in splitted_image_src:
                index = 0
                for idx in range(len(splitted_image_src)-1):
                    if splitted_image_src[idx] == ".." and splitted_image_src[idx+1] != "..":
                        index = idx+1
                img_url = f"https://leetcode.com/explore/{'/'.join(splitted_image_src[index:])}"
            else:
                img_url = image['src']
                # Parse the URL
                img_url_parsed = urlparse(img_url)
                hostname = img_url_parsed.hostname

                # Check for localhost or 127.0.0.1
                if hostname == "127.0.0.1" or hostname == "localhost":
                    logger.warning(f"localhost detected: {img_url}")
                    # Remove leading `/` from the path before appending, or directly append the path
                    img_url = f"https://leetcode.com/explore{img_url_parsed.path}"                    

            logger.debug(f"img_url: {img_url}")

            image['src'] = img_url

            if CONFIG.download_images:
                files = download_image(question_id, img_url)
                if files:
                    if CONFIG.base64_encode_image:
                        frames = load_image_in_b64(files, img_url)
                    else:
                        frames = load_image_local(files)

                    if frames and len(frames) > 0:
                        if len(frames) == 1:
                            if frames[0]:
                                image['src'] = frames[0]
                            else:
                                image.decompose()
                        else:
                            new_tags = []
                            for frame in frames:
                                if frame:
                                    frame_tag = content_soup.new_tag('img', src=frame)
                                    new_tags.append(frame_tag)

                            # Replace the GIF <img> tag with the new image tags
                            image.replace_with(*new_tags)
                    else:
                        image.decompose()
                else:
                    image.decompose()
    return content_soup


def convert_display_math_to_inline(content_soup):
    logger.debug("Converting display math $$ to inline math $")

    for element in content_soup.find_all(string=True):
        text = element.string.strip()
        if text:
            # Replace double $$ with single $
            new_text = re.sub(r'\$\$\s*(.*?)\s*\$\$', r'$\1$', text)
            element.replace_with(new_text)
    return content_soup

def convert_display_math_to_inline2(content):
    logger.debug("Converting display math $$ to inline math $")
    # Strip spaces inside $$ ... $$ and convert it to $ ... $
    content = re.sub(r'\$\$\s*(.*?)\s*\$\$', r'$\1$', content)
    return content

def place_solution_slides(content_soup, slides_json):
    logger.debug("Placing solution slides")

    slide_p_tags = set()
    for p in content_soup.find_all('p'):
        text = p.get_text().lower()
        if '/documents/' in text and ".json" in text:
            slide_p_tags.add(p)

    logger.debug(f"slide_p_tags len {len(slide_p_tags)}")

    # For case when <p> is selected twice because of nested <p>
    # Input: <p>something<p>../Documents/a.json</p></p>
    # List contains:
    # 1. <p>something<p>../Documents/a.json</p></p>
    # 2. <p>../Documents/a.json</p>
    # Output:
    # 1. <p>../Documents/a.json</p>
    slide_p_tags_deduped = set()

    # Iterate over all <p> tags in slide_p_tags
    for slide_p_tagx in slide_p_tags:
        textx = slide_p_tagx.get_text().lower()
        # Flag to check if this tag is a duplicate (nested in another tag)
        is_nested = False

        # Compare with all other <p> tags to check if it's nested
        for slide_p_tagy in slide_p_tags:
            if slide_p_tagx == slide_p_tagy:
                continue
            
            texty = slide_p_tagy.get_text().lower()
            
            # If textx is fully contained in texty, mark it as nested
            if textx in texty:
                is_nested = True
                break

        # Add only if it's not nested
        if not is_nested:
            slide_p_tags_deduped.add(slide_p_tagx)

    slide_p_tags = slide_p_tags_deduped
    logger.debug(f"slide_p_tags len {len(slide_p_tags)}")
    
    for slide_idx, slide_p_tag in enumerate(slide_p_tags):
        logger.debug(f"slide_idx {slide_idx} {slide_p_tag}")
        
        if slides_json[slide_idx] == []:
            continue

        slides_html = f"""<div id="carouselExampleControls-{slide_idx}" class="carousel slide" data-bs-ride="carousel">
                        <div  class="carousel-inner">"""
        for img_idx, img_links in enumerate(slides_json[slide_idx]):
            logger.debug(f"Image links: {img_links}")
            slides_html += f"""<div class="carousel-item {'active' if img_idx == 0 else ''}">
                                <img src="{img_links['image']}" class="d-block" alt="...">
                            </div>"""
        
        slides_html += f"""</div>
                            <button class="carousel-control-prev" type="button" data-bs-target="#carouselExampleControls-{slide_idx}" data-bs-slide="prev">
                                <span class="carousel-control-prev-icon" aria-hidden="true"></span>
                                <span class="visually-hidden"></span>
                            </button>
                            <button class="carousel-control-next" type="button" data-bs-target="#carouselExampleControls-{slide_idx}" data-bs-slide="next">
                                <span class="carousel-control-next-icon" aria-hidden="true"></span>
                                <span class="visually-hidden"></span>
                            </button>
                            </div>"""
        slide_p_tag.replace_with(BeautifulSoup(
            slides_html, 'html.parser'))
    return content_soup


def replace_iframes_with_codes(content, question_id):
    logger.debug("Replacing iframe with code")

    videos_dir = os.path.join(CONFIG.save_path, "questions", "videos")
    os.makedirs(videos_dir, exist_ok=True)

    content_soup = BeautifulSoup(content, 'html.parser')
    iframes = content_soup.find_all('iframe')
    for if_idx, iframe in enumerate(iframes, start=1):
        src_url = iframe['src']
        logger.debug(f"Playground url: {src_url}")

        src_url_lcase = str.lower(src_url)

        if "playground" in src_url_lcase:
            uuid = src_url.split('/')[-2]
            logger.debug(f"Playground uuid: {uuid} url: {src_url}")
            
            data_path = get_cache_path("code", f"{question_id_title(question_id, uuid)}.json")

            query = {
                "operationName": "allPlaygroundCodes",
                "query": f"""query allPlaygroundCodes {{\n allPlaygroundCodes(uuid: \"{uuid}\") {{\n    code\n    langSlug\n }}\n}}\n"""
            }
            selector = ['data', 'allPlaygroundCodes']

            playground_content = cached_query(
                data_path=data_path,
                query=query,
                selector=selector)

            if not playground_content:
                logger.error(f"Error in getting code data from source url {src_url}")
                continue

            code_html = f"""<div>"""
            
            lang_to_include = "all"
            languages = set(item.get("langSlug") for item in playground_content)

            if CONFIG.preferred_language_order == "all":
                lang_to_include = CONFIG.preferred_language
            else:
                preferred_languages = CONFIG.preferred_language_order.split(",")
                for preferred_language in preferred_languages:
                    preferred_language = preferred_language.strip()
                    if preferred_language in languages:
                        lang_to_include = preferred_language
                        break

            for code_idx in range(len(playground_content)):
                lang = playground_content[code_idx]['langSlug']
                if lang_to_include == "all" or lang_to_include == lang:
                    code_html += f"""<div style="font-weight: bold;">{lang}</div>"""
                    code_html += f"""<div><code style="color:black"><pre>{playground_content[code_idx]['code']}</pre></code></div>"""

            code_html += f"""</div>"""
            iframe.replace_with(BeautifulSoup(
                f""" {code_html} """, 'html.parser'))
        elif "vimeo" in src_url_lcase:
            width = iframe.get('width') or 640
            height = iframe.get('height') or 360

            video_id = src_url.split("/")[-1]
            video_extension = "mp4"
            video_basename = f"{question_id_title(question_id, video_id)}.{video_extension}"

            if CONFIG.download_videos:
                ydl_opts = {
                    'outtmpl': f'{videos_dir}/{qstr(question_id)}-%(id)s.%(ext)s',
                    'format': 'bestvideo[height<=720]+bestaudio/best[height<=720]',
                    'http_headers': {
                        'Referer': 'https://leetcode.com',
                    }
                }

                # Download the video using yt-dlp
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info_dict = ydl.extract_info(src_url, download=CONFIG.download_videos)
                    video_extension = info_dict.get('ext')
                    video_filename = ydl.prepare_filename(info_dict)
                    video_basename = os.path.basename(video_filename)

            if video_basename:
                video_html = f"""
                    <video width="{width}" height="{height}" controls>
                        <source src="videos/{video_basename}" type="video/{video_extension}">
                    </video>
                """
                iframe.replace_with(BeautifulSoup(video_html, 'html.parser'))

    return str(content_soup)


def attach_header_in_html():
    return r"""<head>
                    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet"/>
                    <link crossorigin="anonymous" href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css" integrity="sha384-rbsA2VBKQhggwzxH7pPCaAqO46MgnOM80zW1RWuH61DGLwZJEdK2Kadq2F9CUG65" rel="stylesheet"/>
                    <script crossorigin="anonymous" integrity="sha384-kenU1KFdBIe4zVF0s0G1M5b4hcpxyD9F7jL+jjXkk+Q2h455rYXK/7HAuoJl+0I4" src="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/js/bootstrap.bundle.min.js">
                    </script>
                    <script src="https://md-block.verou.me/md-block.js" type="module">
                    </script>
                    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/9000.0.1/prism.min.js">
                    </script>
                    <script src="https://polyfill.io/v3/polyfill.min.js?features=es6">
                    </script>
                    <script async="" src="https://cdn.mathjax.org/mathjax/latest/MathJax.js?config=TeX-MML-AM_CHTML" type="text/javascript">
                    MathJax.Hub.Config({
                                        TeX: {
                                            Macros: {
                                            "exclude": "\\def\\exclude#1{}"
                                            }
                                        },
                                        tex2jax: {
                                            inlineMath: [["$", "$"], ["\\(", "\\)"], ["$$", "$$"], ["\\[", "\\]"] ],
                                            processEscapes: true,
                                            processEnvironments: true,
                                            skipTags: ['script', 'noscript', 'style', 'textarea', 'pre']
                                        },
                                        CommonHTML: {
                                                            scale: 80
                                                        },
                                        });

                                        MathJax.Hub.Register.StartupHook("TeX Jax Ready", function() {
                                        MathJax.Hub.Insert(MathJax.InputJax.TeX.Definitions.macros, {
                                            exclude: "exclude"
                                        });
                                        });
                    </script>
                    <script>
                    document.addEventListener('DOMContentLoaded', function() {
                                                const carousel = document.querySelectorAll('.carousel');
                                                console.log(carousel)
                                                const items = Array.from(document.querySelectorAll('.carousel-item'));
                                                console.log(items)
                                                const maxWidth = Math.max(...items.map(item => item.querySelector('img').clientWidth));
                                                console.log(maxWidth);
                                                for (let i = 0; i < carousel.length; i++) {
                                                    carousel[i].style.width = maxWidth + 'px';            }
                                                
                                                $( ".change" ).on("click", function() {
                                                if( $( "body" ).hasClass( "dark" )) {
                                                    $( "body" ).removeClass( "dark" );
                                                    $( "div[style*='background: wheat;']" ).removeClass( "dark-banner" );
                                                    $( "div[style*='background: beige;']" ).removeClass( "dark-banner-sq" );
                                                    $("div[id*='v-pills-tabContent']").removeClass( "tab-content dark" );
                                                    $("table").removeClass( "table-color-dark" );
                                                    $("table").addClass( "table-color" );
                                                    $("div[id*='v-pills-tabContent']").addClass( "tab-content" );
                                                    $( ".change" ).text( "OFF" );
                                                } else {
                                                    $( "body" ).addClass( "dark" );
                                                    $( "div[style*='background: wheat;']" ).addClass( "dark-banner" );
                                                    $( "div[style*='background: beige;']" ).addClass( "dark-banner-sq" );
                                                    $("div[id*='v-pills-tabContent']").addClass( "tab-content dark" );
                                                    $("table").removeClass( "table-color" );
                                                    $("table").addClass( "table-color-dark" );
                                                    $( ".change" ).text( "ON" );
                                                }
                            });
                                    });
                    </script>
                    <script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/3.4.0/jquery.min.js"></script>
                    <style>
                                body {
                                    overflow-x: hidden;
                                    background-color: white;
                                    left: 10% !important;
                                    right: 10% !important;
                                    position: absolute;

                                    }
                                    .similar-questions-container {
                                        display: flex;
                                        justify-content: space-between;
                                        }

                                        .left::after {
                                        content: "-";
                                        margin-left: 5px;
                                        }

                                        .right::before {
                                        content: "-";
                                        margin-right: 5px;
                                        }
                                    .mode {
                                        float:right;
                                    }
                                    .dark.tab-content{
                                            background: repeating-linear-gradient(45deg, #130f0f, #3b3b3b4d 100px) !important;
                                    }
                                    .dark-banner-sq{
                                            background-color: #3b3451b8 !important;
                                            border: 1px solid #DCDCDC;
                                    }
                                    .tab-content{
                                        background: white !important;
                                    }
                                    .change {
                                        cursor: pointer;
                                        border: 1px solid #555;
                                        border-radius: 40%;
                                        width: 20px;
                                        text-align: center;
                                        padding: 5px;
                                        margin-left: 8px;
                                    }
                                    .dark{
                                        background-color: #222;
                                        color: #e6e6e6;
                                    }
                                    .dark-banner{
                                        background-color: darkslategray !important;
                                        color: #e6e6e6 !important;
                                    }
                                    .carousel-control-prev > span,
                                    .carousel-control-next > span {
                                    background-color: #007bff; 
                                    border-color: #007bff; 
                                    }
                                    img {
                                        width: auto;
                                        height: auto;
                                        max-width: 100%;
                                        max-height: 100%;
                                    }
                    </style>
                    <style>
                    mjx-container, .mjx-chtml {
                                        display: inline !important;
                                    }
                    </style></head>
 """

def wrap_slides_with_p_tags(content):
    # Define the regex pattern to match the entire target string, including the !?! at both ends
    pattern = re.compile(r'(?<!<p>)(\!\?\!.*/Documents/.*\!\?\!)(?!</p>)', re.IGNORECASE | re.MULTILINE)

    # Replace the matched pattern with the <p> wrapped version
    result = pattern.sub(r'<p>\g<0></p>', content)

    return result

def find_slides_json(content, question_id):
    logger.info("Finding slides json")

    word = "/Documents/"
    all_slides_json_list = re.compile(
        fr".*{word}.*", re.MULTILINE).findall(content)
    slides_json_list = [x for x in all_slides_json_list if ".json" in x]
    slides_json = []

    for link in slides_json_list:
        slide_url = "https://leetcode.com/explore/" + \
            "/".join(link.strip().split(".json")[-2].split("/")[1:]) + ".json"
        logger.info(slide_url)

        file_hash = hashlib.md5(slide_url.encode()).hexdigest()

        data_path = get_cache_path("slides", f"{question_id_title(question_id, file_hash)}.json")
        selector = ['timeline']

        slides_json_content = cached_query(
            data_path=data_path,
            method="get",
            selector=selector,
            url=slide_url,
            headers=DEFAULT_HEADERS)
      
        slides_json.append(slides_json_content)

    return slides_json

def find_slides_json2(content, question_id):
    logger.info("Finding slides json")

    word = "/Documents/"
    pattern = re.compile(fr"!?!.*{word}.*!?!", re.IGNORECASE | re.MULTILINE)
    slide_names_list = pattern.findall(content)

    slide_names = [x for x in slide_names_list if ".json" in x]

    logger.debug(f"Slide names count: {len(slide_names)}")

    slide_contents = []
    for slide_name in slide_names:
        logger.debug(f"Slide name: {slide_name}")
        json_split = slide_name.strip().split(".json")
        base_name = json_split[-2]

        logger.debug(f"Base name: {base_name}")
        
        json_split = base_name.split("/")
        drop_dots = json_split[1:]
        
        documents = drop_dots[0] # Documents
        logger.debug(f"documents: {documents}")

        rest_after_documents = drop_dots[1:] # 01_LIS.json
        filename = "/".join(rest_after_documents)
        logger.debug(f"filename: {filename}")

        filename_var1 = f"{str.lower(documents)}/{filename}" # variation 1: only documents/ lower
        filename_var2 = f"{str.lower(documents)}/{str.lower(filename)}" # variation 2: all lower
        logger.debug(f"filename_var1: {filename_var1}")
        logger.debug(f"filename_var2: {filename_var2}")
    
        file_hash = hashlib.md5(filename_var1.encode()).hexdigest()

        data_path = get_cache_path("slides", f"{question_id_title(question_id, file_hash)}.json")
        slide_url1 = f"https://assets.leetcode.com/static_assets/media/{filename_var1}.json"
        slide_url2 = f"https://assets.leetcode.com/static_assets/media/{filename_var2}.json"
        selector = ['timeline']
        
        try:
            logger.debug(f"Slide url1: {slide_url1}")
            slide_content = cached_query(
                data_path=data_path,
                method="get",
                url=slide_url1,
                selector=selector,
                headers=DEFAULT_HEADERS)
        except:
            logger.error(f"Slide url1 failed: {slide_url1}")
            logger.debug(f"Slide url2: {slide_url2}")

            try:
                slide_content = cached_query(
                    data_path=data_path,
                    method="get",
                    url=slide_url2,
                    selector=selector,
                    headers=DEFAULT_HEADERS)
            except:
                logger.error(f"Slide url2 failed: {slide_url2}")
                pass

        if not slide_content:    
            slide_content = []

        slide_contents.append(slide_content)

    return slide_contents


def get_article_data(item_content, item_title, question_id):
    logger.info("Getting article data")

    article_data = ""

    if item_content['article']:
        article_id = item_content['article']['id']
        data_path = get_cache_path("articles", f"{question_id_title(question_id, article_id)}.json")

        query = {
            "operationName": "GetArticle",
            "variables": {
                "articleId": article_id
            },
            "query": "query GetArticle($articleId: String!) {\n  article(id: $articleId) {\n    id\n    title\n    body\n  }\n}\n"
        }
        selector = ['data', 'article', 'body']

        article_content = cached_query(
            data_path=data_path,
            query=query,
            selector=selector)

        article_data = f"""<h3>{item_title}</h3>
                    <md-block class="article__content">{article_content}</md-block>
                """
    return article_data

def get_html_article_data(item_content, item_title):
    logger.info("Getting html article data")

    html_article_data = ""
    if item_content['htmlArticle']:
        html_article_id = item_content['htmlArticle']['id']

        data_path = get_cache_path("articles", f"{html_article_id}-data.html")

        query = {
            "operationName": "GetHtmlArticle",
            "variables": {
                "htmlArticleId": html_article_id
            },
            "query": "query GetHtmlArticle($htmlArticleId: String!) {\n  htmlArticle(id: $htmlArticleId) {\n    id\n    html\n      }\n}\n"
        }
        selector = ['data', 'htmlArticle', 'html']

        html_article = cached_query(
            data_path=data_path,
            query=query,
            selector=selector)

        html_article_data = f"""<h3>{item_title}</h3>
                    <md-block class="html_article__content">{html_article}</md-block>
                """
    return html_article_data



def generate_similar_questions(similar_questions):
    logger.info("Generating similar questions")
    similar_questions_html = ""

    if similar_questions:
        similar_questions = json.loads(similar_questions)
        if similar_questions != []:
            similar_questions_html += f"""<div style="background: white;"><h3>Similar Questions</h3>"""
            for idx, similar_question in enumerate(similar_questions, start=1):
                # similar_question = question_html(similar_question['title'], similar_question['title'])
                similar_questions_html += f"""<div class="similar-questions-container"><div>{idx}. <a target="_blank" href="https://leetcode.com/problems/{similar_question['titleSlug']}">{similar_question['title']}</a> ({similar_question['difficulty']}) <a target="_blank" href="./{similar_question['title']}.html">Local</a></div></div>"""
            similar_questions_html += f"""</div>"""

    return similar_questions_html


def get_question_company_tag_stats(company_tag_stats):
    company_tag_stats_html = ""

    if company_tag_stats:
        company_tag_stats = json.loads(company_tag_stats)
        if company_tag_stats != {}:
            company_tag_stats =  {int(k): v for k, v in sorted(company_tag_stats.items(), key=lambda item: int(item[0]))}
            company_tag_stats_html += f"""<div style="background: white;"><h3>Company Tag Stats</h3>"""
            for key, value in company_tag_stats.items():
                company_tag_stats_html += f"""<h4>Years: {str(key-1)}-{str(key)}</h4><div>"""
                for idx, company_tag_stat in enumerate(value):
                    if idx != 0:
                        company_tag_stats_html += ", "
                    company_tag_stats_html += f"""{company_tag_stat['name']}"""
                    company_tag_stats_html += f""": {company_tag_stat['timesEncountered']}"""
                company_tag_stats_html += "</div>"
            company_tag_stats_html += "</div>"
    return company_tag_stats_html


def get_all_submissions():
    all_questions = get_all_questions_url(force_download=CONFIG.force_download)
    for question in all_questions:
        item_content = {"question": {'titleSlug': question['titleSlug'], 'frontendQuestionId': question['frontendQuestionId'], 'title': question['title']}}
        get_submission_data(item_content, False)

def get_submission_data(item_content, save_submission_as_file):

    list_of_submissions = {}

    if item_content['question']:
        question_frontend_id = int(item_content['question']['frontendQuestionId']) if item_content['question']['frontendQuestionId'] else 0
        question_title_slug = item_content['question']['titleSlug']

        data_path = get_cache_path("submissions", f"{question_id_title(question_frontend_id, 'subm')}.json")

        query = {
            "operationName": "submissionList",
            "variables": {
                "questionSlug": question_title_slug,
                "offset": 0,
                "limit": 20,
                "lastKey": None
            },
            "query": "\n    query submissionList($offset: Int!, $limit: Int!, $lastKey: String, $questionSlug: String!, $lang: Int, $status: Int) {\n  questionSubmissionList(\n    offset: $offset\n    limit: $limit\n    lastKey: $lastKey\n    questionSlug: $questionSlug\n    lang: $lang\n    status: $status\n  ) {\n    lastKey\n    hasNext\n    submissions {\n      id\n      title\n      titleSlug\n      status\n      statusDisplay\n      lang\n      langName\n      runtime\n      timestamp\n      url\n      isPending\n      memory\n      hasNotes\n      notes\n      flagType\n      topicTags {\n        id\n      }\n    }\n  }\n}\n    "
        }
        selector = ['data', 'questionSubmissionList', 'submissions']

        submission_content = cached_query(
            data_path=data_path,
            query=query,
            selector=selector)
            
        if not submission_content or len(submission_content) == 0:
            return

        for i, submission in enumerate(submission_content):
            submission_id = submission['id']
            if submission["statusDisplay"] != "Accepted":
                continue

            data_path = get_cache_path("submissions", f"{question_id_title(question_frontend_id, submission_id)}-detail.json")

            query = {
                "operationName": "submissionDetails",
                "variables": {
                    "submissionId": submission_id
                },                
                "query":"\n    query submissionDetails($submissionId: Int!) {\n  submissionDetails(submissionId: $submissionId) {\n    runtime\n    runtimeDisplay\n    runtimePercentile\n    runtimeDistribution\n    memory\n    memoryDisplay\n    memoryPercentile\n    memoryDistribution\n    code\n    timestamp\n    statusCode\n    user {\n      username\n      profile {\n        realName\n        userAvatar\n      }\n    }\n    lang {\n      name\n      verboseName\n    }\n    question {\n      questionId\n      titleSlug\n      hasFrontendPreview\n    }\n    notes\n    flagType\n    topicTags {\n      tagId\n      slug\n      name\n    }\n    runtimeError\n    compileError\n    lastTestcase\n    totalCorrect\n    totalTestcases\n    fullCodeOutput\n    testDescriptions\n    testBodies\n    testInfo\n  }\n}\n    "
            }
            selector = ['data', 'submissionDetails']

            submission_detail_content = None
            try:
                submission_detail_content = cached_query(
                    data_path=data_path,
                    query=query,
                    selector=selector)
            except:
                pass

            if not submission_detail_content:
                continue
            
            if save_submission_as_file:
                list_of_submissions[int(submission["timestamp"])] = submission_detail_content['code']
            else:
                submissions_download_dir = os.path.join(CONFIG.save_path, "questions", "submissions")
                os.makedirs(submissions_download_dir, exist_ok=True)

                file_extension = FILE_EXTENSIONS[submission["lang"]]
                submission_file_name = f"{question_frontend_id:04}-{i+1:02}-{submission_id}.{file_extension}"
                submission_file_path = os.path.join(submissions_download_dir, submission_file_name)

                with open(submission_file_path, "w") as outfile:
                    outfile.write(submission_detail_content['code'])
    return list_of_submissions

def get_solution_content(question_id, question_title_slug):
    logger.info("Getting solution data")

    data_path = get_cache_path("soldata", f"{question_id_title(question_id, 'sol')}.json")

    query = {
        "operationName": "officialSolution",
        "variables": {
            "titleSlug": question_title_slug
        },
        "query": "\n    query officialSolution($titleSlug: String!) {\n  question(titleSlug: $titleSlug) {\n    solution {\n      id\n      title\n      content\n      contentTypeId\n      paidOnly\n      hasVideoSolution\n      paidOnlyVideo\n      canSeeDetail\n      rating {\n        count\n        average\n        userRating {\n          score\n        }\n      }\n      topic {\n        id\n        commentCount\n        topLevelCommentCount\n        viewCount\n        subscribed\n        solutionTags {\n          name\n          slug\n        }\n        post {\n          id\n          status\n          creationDate\n          author {\n            username\n            isActive\n            profile {\n              userAvatar\n              reputation\n            }\n          }\n        }\n      }\n    }\n  }\n}\n    "
    }
    selector = ['data', 'question', 'solution']

    sol_content = cached_query(
        data_path=data_path,
        query=query,
        selector=selector)

    solution = None
    if sol_content:
        solution = sol_content['content']
    return solution


# Function to clean up math expressions
def clean_tex_math(content):
    # Replace \space with a regular space
    return re.sub(r'\\space', ' ', content)

def markdown_with_math(content):
    content = convert_display_math_to_inline2(content)
    content = clean_tex_math(content)

    # Convert Markdown to HTML and ensure TeX math is not escaped
    return markdown.markdown(
        content,
        extensions=['extra', 'mdx_math'])

def markdown_with_iframe(content):
    return markdown_with_math(content)

def markdown2_with_math(content):
    # Convert Markdown to HTML and ensure TeX math is not escaped
    return markdown2.markdown(
        content,
        extras=["code-friendly", "fenced-code-blocks", "html-classes"])

def markdown2_with_iframe(content):
    # Store iframe before processing markdown
    iframe_tags = re.findall(r'<iframe.*?>.*?</iframe>', content, re.DOTALL)

    # Placeholder text for iframes
    for idx, iframe in enumerate(iframe_tags):
        content = content.replace(iframe, f"{{iframe_placeholder_{idx}}}")

    # Convert the rest of the markdown to HTML
    html_content = markdown2_with_math(content)

    # Replace the placeholders with actual iframe tags
    for idx, iframe in enumerate(iframe_tags):
        html_content = html_content.replace(f"{{iframe_placeholder_{idx}}}", iframe)
    
    return html_content


def get_question_data(item_content):
    logger.info("Getting question data")
    if item_content['question']:
        question_id = int(item_content['question']['frontendQuestionId']) if item_content['question']['frontendQuestionId'] else 0
        question_title_slug = item_content['question']['titleSlug']
        question_title = item_content['question']['title'] if item_content['question']['title'] else question_title_slug

        data_path = get_cache_path("qdata", f"{question_id_title(question_id, 'qdat')}.json")

        query = {
            "operationName": "GetQuestion",
            "variables": {
                "titleSlug": question_title_slug
            },
            "query": "query GetQuestion($titleSlug: String!) {\n  question(titleSlug: $titleSlug) {\n title\n submitUrl\n similarQuestions\n difficulty\n  companyTagStats\n codeDefinition\n    content\n    hints\n    solution {\n      content\n   }\n   }\n }\n"
        }

        selector = ['data', 'question']

        question_content = cached_query(
            data_path=data_path,
            query=query,
            selector=selector)

        question_title = re.sub(r'[:?|></\\]', replace_filename, question_content['title'])        
        question = question_content['content']
        difficulty = question_content['difficulty']
        company_tag_stats = get_question_company_tag_stats(question_content['companyTagStats'])
        similar_questions = generate_similar_questions(question_content['similarQuestions'])
        question_url = "https://leetcode.com" + question_content['submitUrl'][:-7]

        default_code = json.loads(question_content['codeDefinition'])[0]['defaultCode']
        solution = question_content['solution']
        if solution:
            solution = solution['content']
            solution = re.sub(r'\[TOC\]', '', solution) # remove [TOC]
        else:
            solution = None

        hints = question_content['hints']

        hint_content = None
        if hints:
            hint_content = ""
            for hint in hints:
                # hint = convert_display_math_to_inline2(hint)
                hint = str.strip(hint)
                hint = markdown_with_math(hint)
                hint = str.strip(hint)
                hint_content += f"<li>{hint}</li>"
            hint_content += f"<div><ul>{hint_content}</ul></div>"
            

        submission_content = None

        if CONFIG.include_submissions_count > 0:
            item_content = {
                "question": {
                    'titleSlug': question_title_slug,
                    'frontendQuestionId': question_id,
                    'title': question_title
                }
            }
            submissions = get_submission_data(item_content, True)
            if submissions and len(submissions) > 0:
                # Sorted by timestamp in descending order
                ordered_submissions = sorted(submissions.items(), key=lambda item: item[0], reverse=True)
                # Take top n of submissions
                ordered_submissions = ordered_submissions[:CONFIG.include_submissions_count]

                submission_content = ""
                for sub_timestamp, code in ordered_submissions:
                    submission_time = datetime.datetime.fromtimestamp(sub_timestamp).strftime("%Y-%m-%d %H.%M.%S")
                    submission_content += f"""<div><h4>Submission Time: {submission_time}</h4>
                    <pre class="question__default_code">{code}</pre></div>"""

        # question = convert_display_math_to_inline2(question)
        question = markdown_with_math(question)
        
        # solution = convert_display_math_to_inline2(solution)
        if solution:
            solution = markdown_with_iframe(solution)
            solution = replace_iframes_with_codes(solution, question_id)
            solution = wrap_slides_with_p_tags(solution)

        default_code_html = """"""
        if CONFIG.include_default_code:
            default_code_html = f"""
                        <div><h3>Default Code</h3>
                        <pre class="question__default_code">{default_code}</pre></div>
            """

        hint_content_html = """"""
        if hint_content:
            hint_content_html = f"""
                    <div><h3>Hints</h3>
                    <md-block class="question__hints">{hint_content}</md-block></div>
            """

        submission_content_html = """"""
        if submission_content:
            submission_content_html = f"""
                    <div><h3>Accepted Submissions</h3>
                    {submission_content}</div>
            """
        
        solution_html = """"""
        if solution:
            solution_html = f"""
                    <div><h3>Solution</h3>
                    <md-block class="question__solution">{solution}</md-block></div>
            """

        return f""" <h2 class="question__url"><a target="_blank" href="{question_url}">{question_id}. {question_title}</a></h2><p> Difficulty: {difficulty}</p>
                    <div><h3>Question</h3>
                    <md-block class="question__content">{question}</md-block></div>
                    {hint_content_html}
                    {default_code_html}
                    {solution_html}
                    <div>{company_tag_stats}</div>
                    <div>{similar_questions}</div>
                    {submission_content_html}
                """, question_title
    return """""", ""


def create_card_index_html(chapters, card_slug):
    logger.info("Creating index.html")

    data_path = get_cache_path("cards", f"{card_slug}.json")
    query = {
        "operationName": "GetExtendedCardDetail",
        "variables": {
            "cardSlug": card_slug
        },
        "query": "query GetExtendedCardDetail($cardSlug: String!) {\n  card(cardSlug: $cardSlug) {\n title\n  introduction\n}\n}\n"
    }

    selector = ['data', 'card']

    introduction = cached_query(
        data_path=data_path,
        query=query,
        selector=selector)

    body = ""
    for chapter in chapters:
        body += f"""
                    <br>
                    <h3>{chapter['title']}</h3>
                    {chapter['description']}
                    <br>
        """
        for item in chapter['items']:
            item['title'] = re.sub(r'[:?|></\\]', replace_filename, item['title'])
            item_fname = question_html(item['id'], item['title'])
            body += f"""<a href="{item_fname}">{item['id']}-{item['title']}</a><br>"""
    with open("index.html", 'w') as f:
        f.write(f"""<!DOCTYPE html>
                <html lang="en">
                {attach_header_in_html()}
                <body>
                    <div class="mode">
                    Dark mode:  <span class="change">OFF</span>
                    </div>"
                    <h1 class="card-title">{introduction['title']}</h1>
                    <p class="card-text">{introduction['introduction']}</p>
                    <br>
                    {body}
                </body>
                </html>""")


def scrape_selected_company_questions(choice):
    all_comp_dir = os.path.join(CONFIG.save_path, "all_company_questions")
    os.makedirs(all_comp_dir, exist_ok=True)
    os.chdir(all_comp_dir)
    
    final_company_tags = []

    with open(CONFIG.company_tag_save_path, 'r') as f:
        company_tags = f.readlines()
        for company_tag in company_tags:
            company_tag = company_tag.replace("\n", "").split("/")[-2]

            final_company_tags.append({
                'name': company_tag,
                'slug': company_tag
            })

    if choice == 9:
        create_all_company_index_html(final_company_tags)
    elif choice == 10:
        for company in final_company_tags:
            company_slug = company['slug']
            scrape_question_data(company_slug)
            os.chdir("..")
    os.chdir("..")

def get_next_data_id():
    data_path = get_cache_path("qdata", "nextdataid.html")

    next_data = cached_query(
        data_path=data_path,
        method="get",
        url="https://leetcode.com/problemset/",
        headers=DEFAULT_HEADERS)

    if next_data:
        next_data_soup = BeautifulSoup(next_data, "html.parser")
        next_data_tag = next_data_soup.find('script', {'id': '__NEXT_DATA__'})
        next_data_json = json.loads(next_data_tag.text)
        next_data_id = next_data_json['props']['buildId']

    return next_data_id

def scrape_all_company_questions(choice):
    logger.info("Scraping all company questions")

    data_path = get_cache_path("companies", "allcompanyquestions.json")
    query = {
        "operationName": "questionCompanyTags",
        "variables": {},
        "query": "query questionCompanyTags {\n  companyTags {\n    name\n    slug\n    questionCount\n  }\n}\n"
    }

    selector = ['data', 'companyTags']

    company_tags = cached_query(
        data_path=data_path,
        query=query,
        selector=selector)            

    all_comp_dir = os.path.join(CONFIG.save_path, "all_company_questions")
    os.makedirs(all_comp_dir, exist_ok=True)  
    os.chdir(all_comp_dir)

    if choice == 7:
        create_all_company_index_html(company_tags)
    elif choice == 8:
        for company in company_tags:
            company_slug = company['slug']
            scrape_question_data(company_slug)
            os.chdir("..")
    os.chdir('..')

def get_categories_slugs_for_company(company_slug):
    data_path = get_cache_path("companies", f"{company_slug}-favdetails.json")

    query = {
        "operationName": "favoriteDetailV2ForCompany",
        "variables": {
            "favoriteSlug": company_slug
        },
        "query": "query favoriteDetailV2ForCompany($favoriteSlug: String!) {\n  favoriteDetailV2(favoriteSlug: $favoriteSlug) {\n    questionNumber\n    collectCount\n    generatedFavoritesInfo {\n      defaultFavoriteSlug\n      categoriesToSlugs {\n        categoryName\n        favoriteSlug\n        displayName\n      }\n    }\n  }\n}\n    "
    }

    selector = ['data', 'favoriteDetailV2']

    favoriteDetails = cached_query(
        data_path=data_path,
        query=query,
        selector=selector)            

    return favoriteDetails


def create_all_company_index_html(company_tags):
    logger.info("Creating company index.html")
    cols = 10
    rows = len(company_tags)//10 + 1
    html = ''
    company_idx = 0
    with open(CONFIG.company_tag_save_path, 'w') as f:
        for _ in range(rows):
            html += '<tr>'
            for _ in range(cols):
                if company_idx < len(company_tags):
                    html += f'''<td><a href="{company_tags[company_idx]['slug']}/index.html">{company_tags[company_idx]['slug']}</a></td>'''
                    f.write(f"https://leetcode.com/company/{company_tags[company_idx]['slug']}/\n")
                    company_idx += 1
            html += '</tr>'

    with open(os.path.join(CONFIG.save_path, "all_company_questions", "index.html"), 'w') as f:
        f.write(f"""<!DOCTYPE html>
                <html lang="en">
                <head> </head>
                <body>
                    '<table>{html}</table>'
                </body>
                </html>""")
    
    for company in company_tags:
        company_slug = company['slug']

        favoriteDetails = get_categories_slugs_for_company(company_slug)
        if not favoriteDetails:
            continue
        favoriteSlugs = {item["favoriteSlug"]: item["displayName"] for item in favoriteDetails['generatedFavoritesInfo']['categoriesToSlugs']}
        total_questions = favoriteDetails['questionNumber']

        company_root_dir = os.path.join(CONFIG.save_path, "all_company_questions", company_slug)
        os.makedirs(company_root_dir, exist_ok=True)

        if not CONFIG.force_download and "index.html" in os.listdir(company_root_dir):
            logger.info(f"Already Scraped {company_slug}")
            continue
        logger.info(f"Scrapping Index for {company_slug}")

        data_dir = os.path.join(CONFIG.save_path, "cache", "companies")
        os.makedirs(data_dir, exist_ok=True)

        overall_html = ''

        for favoriteSlug in favoriteSlugs:

            data_path = get_cache_path("companies", f"{favoriteSlug}.json")

            query = {
                "operationName": "favoriteQuestionList",
                "variables": {
                    "favoriteSlug": favoriteSlug,
                    "filter": {
                        "positionRoleTagSlug": "",
                        "skip": 0,
                        "limit": total_questions
                    }
                },
                "query": "\n    query favoriteQuestionList($favoriteSlug: String!, $filter: FavoriteQuestionFilterInput) {\n  favoriteQuestionList(favoriteSlug: $favoriteSlug, filter: $filter) {\n    questions {\n      difficulty\n      id\n      paidOnly\n      questionFrontendId\n      status\n      title\n      titleSlug\n      translatedTitle\n      isInMyFavorites\n      frequency\n      topicTags {\n        name\n        nameTranslated\n        slug\n      }\n    }\n    totalLength\n    hasMore\n  }\n}\n    "
            }

            selector = ['data', 'favoriteQuestionList', 'questions']

            company_questions = cached_query(
                data_path=data_path,
                query=query,
                selector=selector)

            html = ''
            for question in company_questions:
                questionFrontEndId = int(question['questionFrontendId'])
                question['title'] = re.sub(r'[:?|></\\]', replace_filename, question['title'])

                frequency = round(float(question['frequency']), 1)            
                frequency_label = '{:.1f}'.format(frequency)
                question_title_format = question_id_title(questionFrontEndId, question['title'])
                question_fname = question_html(questionFrontEndId, question['title'])
                html += f'''<tr>
                            <td><a slug="{question['titleSlug']}" title="{question_title_format}" href="{question_fname}">{question_title_format}</a></td>
                            <td>Difficulty: {question['difficulty']} </td><td>Frequency: {frequency_label}</td>
                            <td><a target="_blank" href="https://leetcode.com/problems/{question['titleSlug']}">Leet</a></td>
                            </tr>'''
            # Write each favorite slug
            with open(os.path.join(company_root_dir, f"{favoriteSlug}.html"), 'w') as f:
                f.write(f"""<!DOCTYPE html>
                    <html lang="en">
                    <head> </head>
                    <body>
                        <table>{html}</table>
                    </body>
                    </html>""")
            
            overall_html += f"""
                <h1>{favoriteSlugs[favoriteSlug]}</h1>
                <table>{html}</table>"""

        # Write index html
        with open(os.path.join(company_root_dir, "index.html"), 'w') as f:
            f.write(f"""<!DOCTYPE html>
                <html lang="en">
                <head> </head>
                <body>{overall_html}</body>
                </html>""")
        os.chdir("..")


def scrape_question_data(company_slug):
    logger.info("Scraping question data")

    questions_dir = os.path.join(CONFIG.save_path, "questions")
    questions_pdf_dir = os.path.join(CONFIG.save_path, "questions_pdf")
    company_root_dir = os.path.join(CONFIG.save_path, "all_company_questions", company_slug)
    data_dir = os.path.join(CONFIG.save_path, "cache", "companies")
    os.makedirs(questions_dir, exist_ok=True)
    os.makedirs(questions_pdf_dir, exist_ok=True)
    os.makedirs(company_root_dir, exist_ok=True)

    questions_seen = set()
    
    categoriesToSlug = get_categories_slugs_for_company(company_slug)
    if not categoriesToSlug:
        return

    favoriteSlugs = [item["favoriteSlug"] for item in categoriesToSlug['generatedFavoritesInfo']['categoriesToSlugs']]

    for favoriteSlug in favoriteSlugs:
        data_path = os.path.join(data_dir, f"{favoriteSlug}.json")

        if not os.path.exists(data_path):
            raise Exception(f"Company data not found {data_path}")

        with open(data_path, 'r') as f:
            questions = json.loads(f.read())

        company_fav_dir  = os.path.join(company_root_dir, favoriteSlug)
        os.makedirs(company_fav_dir, exist_ok=True)

        # sort by frequency, high frequency first
        questions = sorted(questions, key=lambda x: x['frequency'], reverse=True)
        
        for question in questions:
            question_id = int(question['questionFrontendId'])

            # skip already processed questions
            if question_id in questions_seen:
                continue
            questions_seen.add(question_id)
            
            question_title = question['title']
            question_slug = question['titleSlug']
       
            if CONFIG.force_download:
                create_question_html(question_id, question_slug, question_title)
            
            copied = copy_question_file(question_id, question_title, company_fav_dir)

            # if copy failed retry
            if not copied:
                logger.warning("Copy failed downloading again and retrying copy")
                create_question_html(question_id, question_slug, question_title)
                copy_question_file(question_id, question_title, company_fav_dir)


def replace_filename(str):
    numDict = {':': ' ', '?': ' ', '|': ' ', '>': ' ', '<': ' ', '/': ' ', '\\': ' '}
    return numDict[str.group()]


def manual_convert_images_to_base64():
    root_dir = input("Enter path of the folder where html are located: ")
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.html'):
                with open(os.path.join(root, file), "r") as f:
                    soup = BeautifulSoup(f.read(), 'html.parser')
                    question_id, question_title = html_toquestion(file)
                    res_soup = fix_image_urls(soup, question_id)
                with open(os.path.join(root, file), "w") as f:
                    f.write(res_soup.prettify())
    

if __name__ == '__main__':
    current_os = sys.platform
    REQ_SESSION = requests.Session()
    CLOUD_SCRAPER = cloudscraper.create_scraper()

    global selected_config
    selected_config = "0"

    DEFAULT_CONFIG = load_default_config()
    CONFIG = load_config(DEFAULT_CONFIG)

    parser = argparse.ArgumentParser(description='Leetcode Scraper Options')
    parser.add_argument('--non-stop', type=bool,
                        help='True/False - Will run non stop, will retry if any error occurs',
                        required=False)
    parser.add_argument('--proxy', type=str,
                        help='Add rotating or static proxy username:password@ip:port',
                        required=False)
    clear()
    args = parser.parse_args()
    previous_choice = 0
    if args.proxy:
        os.environ['http_proxy'] = "http://"+args.proxy
        os.environ['https_proxy'] = "http://"+args.proxy
        response = REQ_SESSION.get("https://httpbin.org/ip")
        logger.info("Proxy set", response.content)

    while True:
        # logger.info("Proxy set", SESSION.get(
        #     "https://httpbin.org/ip").content)
        try:
            print("""Leetcode-Scraper v1.5-stable
1: To setup config
2: To select config[Default: 0]
3: To get all cards url
4: To get all question url
5: To scrape card url
6: To scrape question url
7: To scrape all company questions indexes
8: To scrape all company questions
9: To scrape selected company questions indexes
10: To scrape selected company questions
11: To convert images to base64 using os.walk
12: To save submissions in files
                  
Press any to quit
                """)
            if previous_choice != 0:
                print("Previous Choice: ", previous_choice)
            else:
                choice = input("Enter your choice: ")

            try:
                choice = int(choice)
            except Exception:
                break

            if choice > 2:
                CONFIG = load_config()
                LEETCODE_HEADERS = create_headers(CONFIG.leetcode_cookie)

            if choice == 1:
                generate_config()
            elif choice == 2:
                select_config()
            elif choice == 3:
                get_all_cards_url()
            elif choice == 4:
                get_all_questions_url(force_download=True)
            elif choice == 5:
                scrape_card_url()
            elif choice == 6:
                scrape_question_url()
            elif choice == 7 or choice == 8:
                scrape_all_company_questions(choice)
            elif choice == 9 or choice == 10:
                scrape_selected_company_questions(choice)
            elif choice == 11:
                manual_convert_images_to_base64()
            elif choice == 12:
                get_all_submissions()
            else:
                break

            if previous_choice != 0:
                break
        except KeyboardInterrupt:
            if args.non_stop:
                print("Keyboard Interrupt, Exiting")
                break
        except Exception as e:
            print("""
            Error Occured, Possible Causes:
            1. Check your internet connection
            2. Leetcode Session Cookie might have expired 
            3. Check your config file
            4. Too many requests, try again after some time or use proxies
            5. Leetcode might have changed their api queries (Create an issue on github)
            """)
            lineNumber = e.__traceback__.tb_lineno
            raise Exception(f"Exception on line {lineNumber}: {e}")
            if args.non_stop:
                print("Retrying")
                previous_choice = choice
                continue
            input("Press Enter to continue")
