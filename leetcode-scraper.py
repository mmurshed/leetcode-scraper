import requests
import json
from requests.structures import CaseInsensitiveDict
from bs4 import BeautifulSoup, NavigableString
import markdown2
import re
import base64
import os
import sys
import shutil
import argparse
import csv
import hashlib
import validators
from typing import Dict, Iterator
import datetime
from time import sleep
from dataclasses import dataclass
from dataclasses_json import dataclass_json
from PyPDF2 import PdfMerger
from urllib.parse import urlparse, urlsplit
import time
import random
from PIL import Image

import logging
from logging.handlers import RotatingFileHandler

# Set up logging
log_file = 'conversion_errors.log'
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('ConversionLogger')
handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=5)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


# Define default config with all necessary keys
default_config = {
    "leetcode_cookie": "",
    "cards_url_path": "",
    "questions_url_path": "",
    "save_path": "",
    "company_tag_save_path": "",
    "cache_downloads": False,
    "overwrite": False,
    "preferred_language_order": "csharp,cpp,python3,java,c,golang",
    "include_submissions_count": 100
}

OS_ROOT = os.path.expanduser('~')
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))


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
    if ".leetcode-scraper" not in os.listdir(OS_ROOT):
        os.mkdir(base_config_path)
    return base_config_path


def create_folder(path):
    if not os.path.exists(path):
        os.mkdir(path)
    os.chdir(path)


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
    config = default_config
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
        "cache_downloads": "Cache images and json locally T/F? (T/F): ",
        "overwrite": "Overwrite existing files T/F? (T/F): ",
        "preferred_language_order": "Enter order of the preferred solution language (all or a command separate list of languages c, cpp, csharp, java, python3, javascript, typescript, golang): ",
        "include_submissions_count": "How many of your own submissions should be incldued (0 for none, a large integer for all): "
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


def load_config_dict():
    global selected_config
    config_path = os.path.join(OS_ROOT, ".leetcode-scraper")
    config_file_path = os.path.join(config_path, f"config_{selected_config}.json")

    # Check if config file exists
    if not os.path.exists(config_file_path):
        raise Exception("No config found, please create one")

    # Load the JSON config file
    with open(config_file_path, "r") as config_file:
        config = json.load(config_file)

    # Use the default config for missing fields
    for key in default_config:
        config[key] = config.get(key, default_config[key])

    return config

def load_config(config = None):
    if not config:
        config = load_config_dict()
    
    # Dynamically create an anonymous class with attributes from config
    config_class = type('Config', (object,), config)
    return config_class()

CONFIG = load_config(default_config)

def create_headers(leetcode_cookie=""):
    headers = CaseInsensitiveDict()
    headers["content-type"] = "application/json"
    headers['cookie'] = "LEETCODE_SESSION=" + \
        leetcode_cookie if leetcode_cookie != "" else ""
    headers["referer"] = "https://leetcode.com/"
    headers["user-agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0"
    headers["accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"
    # headers["accept-encoding"] = "gzip, deflate, br, zstd"
    return headers


def get_all_cards_url():
    logger.info("Getting all cards url")
    headers = create_headers()
    cards_data = {"operationName": "GetCategories", "variables": {
        "num": 1000}, "query": "query GetCategories($categorySlug: String, $num: Int) {\n  categories(slug: $categorySlug) {\n  slug\n    cards(num: $num) {\n ...CardDetailFragment\n }\n  }\n  }\n\nfragment CardDetailFragment on CardNode {\n   slug\n  categorySlug\n  }\n"}
    cards = json.loads(SESSION.post(url=LEETCODE_GRAPHQL_URL, headers=headers,
                                     json=cards_data).content)['data']['categories']
    with open(CONFIG.cards_url_path, "w") as f:
        for category_card in cards:
            if category_card['slug'] != "featured":
                for card in category_card['cards']:
                    card_url = "https://leetcode.com/explore/" + \
                        card['categorySlug'] + "/card/" + card['slug'] + "/\n"
                    f.write(card_url)


def get_all_questions_url(self_function=True):
    logger.info("Getting all questions url")
    headers = create_headers()
    question_count_data = {
        "query": "\n query getQuestionsCount {allQuestionsCount {\n    difficulty\n    count\n }} \n    "}
    all_questions_count = json.loads(SESSION.post(
        url=LEETCODE_GRAPHQL_URL, headers=headers, json=question_count_data).content)['data']['allQuestionsCount'][0]['count']
    logger.info("Total no of questions: ", all_questions_count)

    question_data = {"query": "\n query problemsetQuestionList($categorySlug: String, $limit: Int, $skip: Int, $filters: QuestionListFilterInput) {\n  problemsetQuestionList: questionList(\n    categorySlug: $categorySlug\n    limit: $limit\n    skip: $skip\n    filters: $filters\n  ) {\n  questions: data {\n title\n titleSlug\n frontendQuestionId: questionFrontendId\n }\n  }\n}\n    ", "variables": {
        "categorySlug": "", "skip": 0, "limit": int(all_questions_count), "filters": {}}}
    all_questions = json.loads(SESSION.post(
        url=LEETCODE_GRAPHQL_URL, headers=headers, json=question_data).content)['data']['problemsetQuestionList']['questions']
    if not self_function:
        return all_questions
    write_questions_to_file(all_questions, CONFIG.questions_url_path)


def write_questions_to_file(all_questions, questions_url_path):
    with open(questions_url_path, "w") as f:
        for question in all_questions:
            frontendQuestionId = question['frontendQuestionId']
            question_url = "https://leetcode.com/problems/" + \
                question['titleSlug'] + "/\n"
            f.write(f"{frontendQuestionId},{question_url}")


def scrape_question_url():
    headers = create_headers(CONFIG.leetcode_cookie)
    all_questions = get_all_questions_url(self_function=False)

    create_folder(os.path.join(CONFIG.save_path, "questions"))

    with open(CONFIG.questions_url_path) as f:
        for row in csv.reader(f):
            question_id = int(row[0])
            question_url = row[1]
            question_url = question_url.strip()
            question_slug = question_url.split("/")[-2]

            for question in all_questions:
                if question['titleSlug'] == question_slug:
                    question_title = re.sub(r'[:?|></\\]', replace_filename, question['title'])
                    break

            question_file = f"{question_id:04}-{question_title}.html"
            question_path = os.path.join(CONFIG.save_path, "questions", question_file)
            if os.path.exists(question_path) and CONFIG.overwrite == False:
                logger.info(f"Already scraped {question_file}")
                continue
            logger.info(f"Scraping question {question_id} url: {question_url}")
            create_question_html(question_id, question_slug, question_title, headers)

            sleepfor = random.randint(5, 15)
            logger.info(f"Waiting for {sleepfor} seconds")
            time.sleep(sleepfor)
            
    with open(os.path.join(CONFIG.save_path, "questions", "index.html"), 'w') as main_index:
        main_index_html = ""
        for idx, files in enumerate(os.listdir(os.path.join(CONFIG.save_path, "questions")),start=1):
            if "index.html" not in files:
                main_index_html += f"""<a href="{files}">{idx}-{files}</a><br>"""
        main_index.write(main_index_html)
    os.chdir('..')


def create_question_html(question_id, question_slug, question_title, headers):
    item_content = {"question": {'titleSlug': question_slug, 'frontendQuestionId': question_id, 'title': question_title}}
    content = """<body>"""
    question_content, question_title = get_question_data(item_content, headers)
    content += question_content
    content += """</body>"""
    slides_json = find_slides_json2(content)
    content = markdown2.markdown(content)
    content = attach_header_in_html() + content
    content_soup = BeautifulSoup(content, 'html.parser')
    content_soup = replace_iframes_with_codes(content_soup, headers, question_id)
    content_soup = place_solution_slides(content_soup, slides_json)
    content_soup = fix_image_urls(content_soup)
    content_soup = convert_display_math_to_inline(content_soup)
    with open(f"{question_id:04}-{question_title}.html", 'w', encoding="utf-8") as f:
        f.write(content_soup.prettify())


def scrape_card_url():
    headers = create_headers(CONFIG.leetcode_cookie)
    create_folder(os.path.join(CONFIG.save_path, "cards"))
    if "questions" not in os.listdir(CONFIG.save_path):
        os.mkdir(os.path.join(CONFIG.save_path, "questions"))

    # Creating Index for Card Folder
    with open(os.path.join(CONFIG.save_path, "cards", "index.html"), 'w') as main_index:
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
            card_data = {"operationName": "GetChaptersWithItems", "variables": {"cardSlug": card_slug},
                        "query": "query GetChaptersWithItems($cardSlug: String!) {\n  chapters(cardSlug: $cardSlug) {\n    ...ExtendedChapterDetail\n   }\n}\n\nfragment ExtendedChapterDetail on ChapterNode {\n  id\n  title\n  slug\n description\n items {\n    id\n    title\n  }\n }\n"}
            chapters = json.loads(SESSION.post(url=LEETCODE_GRAPHQL_URL, headers=headers,
                                                json=card_data).content)['data']['chapters']
            if chapters:
                create_folder(os.path.join(CONFIG.save_path, "cards", card_slug))
                create_card_index_html(chapters, card_slug, headers)
                for subcategory in chapters:
                    logger.info("Scraping subcategory: ", subcategory['title'])
                    for item in subcategory['items']:
                        logger.info("Scraping Item: ", item['title'])
                        item_id = item['id']
                        item_title = re.sub(r'[:?|></\\]', replace_filename, item['title'])

                        if f"{item_id}-{item_title}.html" in os.listdir(os.path.join(CONFIG.save_path, "cards", card_slug)) and overwrite == False:
                            logger.info(f"Already scraped {item_id}-{item_title}.html")
                            if f"{item_title}.html" in os.path.join(CONFIG.save_path, "questions"):
                                if os.path.getsize(os.path.join(CONFIG.save_path, "questions", f"{item_title}.html")) > os.path.getsize(os.path.join(
                                    CONFIG.save_path, "cards", card_slug, f"{item_id}-{item_title}.html")):
                                    shutil.copy(os.path.join(CONFIG.save_path, "questions", f"{item_title}.html"), os.path.join(
                                    CONFIG.save_path, "cards", card_slug))
                                    try:
                                        os.remove(os.path.join(
                                            CONFIG.save_path, "cards", card_slug, f"{item_id}-{item_title}.html"))
                                    except:
                                        pass
                                    os.rename(os.path.join(CONFIG.save_path, "cards", card_slug, f"{item_title}.html"), os.path.join(
                                    CONFIG.save_path, "cards", card_slug, f"{item_id}-{item_title}.html"))
                                elif os.path.getsize(os.path.join(CONFIG.save_path, "questions", f"{item_title}.html")) < os.path.getsize(os.path.join(
                                    CONFIG.save_path, "cards", card_slug, f"{item_id}-{item_title}.html")):
                                    shutil.copy(os.path.join(CONFIG.save_path, "cards", card_slug, f"{item_id}-{item_title}.html"), os.path.join(save_path, "questions"))
                                    try:
                                        os.remove(os.path.join(CONFIG.save_path, "questions", f"{item_title}.html"))
                                    except:
                                        pass
                                    os.rename(os.path.join(CONFIG.save_path, "questions", f"{item_id}-{item_title}.html"), os.path.join(
                                    CONFIG.save_path, "questions", f"{item_title}.html"))
                            continue
                        if f"{item_title}.html" in os.listdir(os.path.join(CONFIG.save_path, "questions")) and CONFIG.overwrite == False:
                            logger.info("Copying from questions folder", item_title)
                            shutil.copy(os.path.join(CONFIG.save_path, "questions", f"{item_title}.html"), os.path.join(
                                CONFIG.save_path, "cards", card_slug))
                            os.rename(os.path.join(CONFIG.save_path, "cards", card_slug, f"{item_title}.html"), os.path.join(
                                CONFIG.save_path, "cards", card_slug, f"{item_id}-{item_title}.html"))
                            continue
                        item_data = {"operationName": "GetItem", "variables": {"itemId": f"{item_id}"},
                                    "query": "query GetItem($itemId: String!) {\n  item(id: $itemId) {\n    id\n title\n  question {\n questionId\n frontendQuestionId: questionFrontendId\n   title\n  titleSlug\n }\n  article {\n id\n title\n }\n  htmlArticle {\n id\n  }\n  webPage {\n id\n  }\n  }\n }\n"}
                        item_content = json.loads(SESSION.post(url=LEETCODE_GRAPHQL_URL, headers=headers,
                                                                json=item_data).content)['data']['item']
                        if item_content == None:
                            break
                        create_card_html(
                            item_content, item_title, item_id, headers)
                os.chdir("..")
    os.chdir('..')


def create_card_html(item_content, item_title, item_id, headers):
    content = """<body>"""
    question_content, question_title = get_question_data(item_content, headers)
    content += question_content
    content += get_article_data(item_content, item_title, headers, item_id)
    content += get_html_article_data(item_content, item_title, headers)
    content += """</body>"""
    slides_json = find_slides_json2(content)
    content = markdown2.markdown(content)
    content = attach_header_in_html() + content
    content_soup = BeautifulSoup(content, 'html.parser')
    content_soup = replace_iframes_with_codes(content_soup, headers, item_id)
    content_soup = place_solution_slides(content_soup, slides_json)
    content_soup = fix_image_urls(content_soup)
    with open(f"{item_id}-{item_title}.html", "w", encoding="utf-8") as f:
        f.write(content_soup.prettify())

def is_valid_image(image_path):
    try:
        # Open the image file
        with Image.open(image_path) as img:
            # Verify the image (this doesn't load the entire image into memory)
            img.verify()
        return True
    except (IOError, SyntaxError, Image.UnidentifiedImageError) as e:
        print(f"Invalid image: {image_path}. Error: {e}")
        return False

def decompose_gif(gif_path, filename_no_ext, output_folder):
    # Open the GIF file
    gif = Image.open(gif_path)
    
    frames = []

    # Iterate over each frame in the GIF
    frame_number = 0
    while True:
        try:
            # Save each frame as a separate image
            frame_path = os.path.join(output_folder, f"{filename_no_ext}_{frame_number:03d}.png")
            gif.seek(frame_number)
            gif.save(frame_path, 'PNG')
            frame_number += 1
            frames.append(frame_path)
        except EOFError:
            break
    return frames


def convert_to_uncompressed_png(img_path, img_ext):
    # Open the PNG file
    try:
        if img_ext == 'png':
            with Image.open(img_path) as img:
                # Save the image without compression
                img.save(img_path, 'PNG', compress_level=0)
                logger.info(f"Decompressed PNG saved at {img_path}")
    except Exception as e:
        logger.error(f"Error reading file {img_path}\n{e}")
        return None


def load_image_in_b64(img_url, decompose_gif_frames):
    if not validators.url(img_url):
        logger.error(f"Invalid image url: {img_url}")
        return
    
    hostname = urlparse(img_url).hostname
    if hostname == "127.0.0.1" or hostname == "localhost":
        logger.info(f"localhost detected: {img_url}")
        return

    images_dir = os.path.join(CONFIG.save_path, "cache", "images")
    os.makedirs(images_dir, exist_ok=True)
    
    parsed_url = urlsplit(img_url)
    image_file_name = os.path.basename(parsed_url.path)    

    img_ext = str.lower(image_file_name.split('.')[-1])

    url_hash = hashlib.md5(img_url.encode()).hexdigest()
    image_local_file_name = f"{url_hash}.{img_ext}"
    image_local_path = os.path.join(images_dir, image_local_file_name)

    if img_ext == "svg":
        img_ext = "svg+xml"

    encoded_string = None

    if not CONFIG.cache_downloads or not os.path.exists(image_local_path):
        try:
            img_data = SESSION.get(url=img_url, headers=create_headers()).content

            with open(image_local_path, 'wb') as img_file:
                img_file.write(img_data)

            convert_to_uncompressed_png(image_local_path, img_ext)

        except Exception as e:
            raise Exception(f"Error loading image url: {img_url}")

    if decompose_gif_frames and img_ext == "gif":
        frames = decompose_gif(image_local_path, url_hash, images_dir)
    else:
        frames = [image_local_path]

    imgs_decoded = []
    for frame in frames:
        if not is_valid_image(frame):
            imgs_decoded.append(None)
            continue

        with open(frame, "rb") as img_file:
            img_data = img_file.read()

        if img_data:
            encoded_string = base64.b64encode(img_data)

        if not encoded_string:
            logger.error(f"Error loading image url: {img_url}")
            return None

        decoded_string = encoded_string.decode('utf-8')
        decoded_image = f"data:image/{img_ext};base64,{decoded_string}"
        imgs_decoded.append(decoded_image)

    return imgs_decoded



def fix_image_urls(content_soup):
    logger.info("Fixing image urls")
    images = content_soup.select('img')
    for image in images:
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

            image['src'] = img_url
            if CONFIG.cache_downloads:
                frames = load_image_in_b64(img_url, False)
                if frames:
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
    return content_soup


def convert_display_math_to_inline(content_soup):
    logger.info("Converting display math $$ to inline math $")
    for element in content_soup.find_all(string=True):
        text = element.string.strip()
        if text:
            # Replace double $$ with single $
            new_text = re.sub(r'\$\$(.*?)\$\$', r'$\1$', text)
            element.replace_with(new_text)
    return content_soup

def place_solution_slides(content_soup, slides_json):
    logger.info("Placing solution slides")
    slide_p_tags = content_soup.select("p:-soup-contains('/Documents/')")
    temp = []
    for slide_p_tag in slide_p_tags:
        if len(slide_p_tag.find_all("p")) == 0 and ".json" in str(slide_p_tag) and slide_p_tag not in temp:
            # logger.debug(slide_p_tag, type(slide_p_tag))
            temp.append(slide_p_tag)
    slide_p_tags = temp
    
    for slide_idx, slide_p_tag in enumerate(slide_p_tags):
        if slides_json[slide_idx] == []:
            continue
        slides_html = f"""<div id="carouselExampleControls-{slide_idx}" class="carousel slide" data-bs-ride="carousel">
                        <div  class="carousel-inner">"""
        for img_idx, img_links in enumerate(slides_json[slide_idx]):
            slides_html += f"""<div class="carousel-item {'active' if img_idx == 0 else ''}">
                                <img src="{img_links['image']}" class="d-block" alt="...">
                            </div>"""
        
        slides_html += f"""</div>
                            <button class="carousel-control-prev" type="button" data-bs-target="#carouselExampleControls-{slide_idx}" data-bs-slide="prev">
                                <span class="carousel-control-prev-icon" aria-hidden="true"></span>
                                <span class="visually-hidden">Previous</span>
                            </button>
                            <button class="carousel-control-next" type="button" data-bs-target="#carouselExampleControls-{slide_idx}" data-bs-slide="next">
                                <span class="carousel-control-next-icon" aria-hidden="true"></span>
                                <span class="visually-hidden">Next</span>
                            </button>
                            </div>"""
        slide_p_tag.replace_with(BeautifulSoup(
            slides_html, 'html.parser'))
    return content_soup


def replace_iframes_with_codes(content_soup, headers, question_id):
    iframes = content_soup.find_all('iframe')
    for if_idx, iframe in enumerate(iframes, start=1):
        src_url = iframe['src']
        if "playground" in src_url:
            uuid = src_url.split('/')[-2]

            question_code_root_dir = os.path.join(CONFIG.save_path, "cache", "code")
            os.makedirs(question_code_root_dir, exist_ok=True)

            question_code_data_json_file = f"{question_id:04}-{uuid}.json"
            question_code_json_path = os.path.join(question_code_root_dir, question_code_data_json_file)

            if CONFIG.cache_downloads and os.path.exists(question_code_json_path):
                with open(question_code_json_path, "r") as file:
                    playground_content = json.load(file)
            else:
                playground_data = {"operationName": "allPlaygroundCodes",
                                "query": f"""query allPlaygroundCodes {{\n allPlaygroundCodes(uuid: \"{uuid}\") {{\n    code\n    langSlug\n }}\n}}\n"""}
                playground_object = SESSION.post(url=LEETCODE_GRAPHQL_URL, headers=headers, json=playground_data).content

                try:
                    playground_content = json.loads(playground_object)
                    playground_content = playground_content['data']['allPlaygroundCodes']
                except:
                    raise Exception(f"Error in getting code data from source url {src_url}")

                with open(question_code_json_path, "w") as outfile:
                    outfile.write(json.dumps(playground_content))

            if not playground_content:
                raise Exception(f"Error in getting code data from source url {src_url}")

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
    return content_soup


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
                                            inlineMath: [["$", "$"], ["\\(", "\\)"], ["$$", "$$"], ["\\[", "\\]"]],
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
                    </style>
 """

def find_slides_json(content):
    logger.info("Finding slides json")

    slides_root_dir = os.path.join(CONFIG.save_path, "cache", "slides")
    os.makedirs(slides_root_dir, exist_ok=True)

    word = "/Documents/"
    all_slides_json_list = re.compile(
        fr".*{word}.*", re.MULTILINE).findall(content)
    slides_json_list = [x for x in all_slides_json_list if ".json" in x]
    slides_json = []
    for links in slides_json_list:
        slide_img_url = "https://leetcode.com/explore/" + \
            "/".join(links.strip().split(".json")[-2].split("/")[1:]) + ".json"
        logger.info(slide_img_url)

        file_hash = hashlib.md5(slide_img_url.encode()).hexdigest()
        slides_data_json_file = f"{file_hash}.json"
        slides_data_json_path = os.path.join(slides_root_dir, slides_data_json_file)

        if CONFIG.cache_downloads and os.path.exists(slides_data_json_path):
            logger.info(f"Loading from {slides_data_json_file}")
            with open(slides_data_json_path, "r") as file:
                slides_json_content = json.load(file)
        else:
            try:
                slides_data = SESSION.get(url=slide_img_url, headers=create_headers())
                slides_json_content = json.loads(slides_data.content)['timeline']
            except Exception as e:
                raise Exception("Error in getting slide json: ", e)

            with open(slides_data_json_path, "w") as outfile:
                outfile.write(json.dumps(slides_json_content))
        
        slides_json.append(slides_json_content)

    return slides_json

def find_slides_json2(content):
    logger.info("Finding slides json")

    slides_root_dir = os.path.join(CONFIG.save_path, "cache", "slides")
    os.makedirs(slides_root_dir, exist_ok=True)

    word = "/Documents/"
    all_slides_json_list = re.compile(fr"!?!.*{word}.*!?!", re.MULTILINE).findall(content)
    
    slides_json_list = [x for x in all_slides_json_list if ".json" in x]

    slides_json = []
    for links in slides_json_list:
        json_split = links.strip().split(".json")
        json_name = json_split[-2]
        
        json_split = json_name.split("/")
        drop_dots = json_split[1:]
        
        documents = drop_dots[0] # Documents
        rest_after_documents = drop_dots[1:] # 01_LIS.json
        file = "/".join(rest_after_documents)
        file_var1 = f"{str.lower(documents)}/{str.lower(file)}" # variation 1: all lower
        file_var2 = f"{str.lower(documents)}/{file}" # variation 2: only documents/ lower
    
        file_hash = hashlib.md5(file_var1.encode()).hexdigest()
        slides_data_json_file = f"{file_hash}.json"
        slides_data_json_path = os.path.join(slides_root_dir, slides_data_json_file)

        if CONFIG.cache_downloads and os.path.exists(slides_data_json_path):
            with open(slides_data_json_path, "r") as file:
                slides_json_content = json.load(file)
        else:
            slide_img_url = f"https://assets.leetcode.com/static_assets/media/{file_var1}.json"

            try:
                slides_json_obj = SESSION.get(url=slide_img_url, headers=create_headers())
                if slides_json_obj.status_code == 404:
                    # if not found try second variation
                    slide_img_url = f"https://assets.leetcode.com/static_assets/media/{file_var2}.json"
                    slides_json_obj = SESSION.get(url=slide_img_url, headers=create_headers())

                slides_json_content = json.loads(slides_json_obj.content)
                slides_json_content = slides_json_content['timeline']
            except:
                raise Exception(f"Error in getting slides data {slide_img_url}")                

            with open(slides_data_json_path, "w") as outfile:
                outfile.write(json.dumps(slides_json_content))

        slides_json.append(slides_json_content)

    return slides_json


def get_article_data(item_content, item_title, headers, question_id):
    logger.info("Getting article data")
    if item_content['article']:
        articles_root_dir = os.path.join(CONFIG.save_path, "cache", "articles")
        os.makedirs(articles_root_dir, exist_ok=True)
        
        article_id = item_content['article']['id']
        articles_data_json_file = f"{question_id:04}-{article_id}.json"
        articles_data_json_path = os.path.join(articles_root_dir, articles_data_json_file)

        if CONFIG.cache_downloads and os.path.exists(articles_data_json_path):
            with open(articles_data_json_path, "r") as file:
                article_content = json.load(file)
        else:            
            article_data = {"operationName": "GetArticle", "variables": {
                "articleId": f"{article_id}"}, "query": "query GetArticle($articleId: String!) {\n  article(id: $articleId) {\n    id\n    title\n    body\n  }\n}\n"}
            article_object = SESSION.post(url=LEETCODE_GRAPHQL_URL, headers=headers, json=article_data).content
            
            try:
                article_content = json.loads(article_object)
                article_content = article_content['data']['article']['body']
            except:
                raise Exception("Error in getting submission data")

            with open(articles_data_json_path, "w") as outfile:
                outfile.write(json.dumps(article_content))            

        return f"""<h3>{item_title}</h3>
                    <md-block class="article__content">{article_content}</md-block>
                """
    return ""


def get_html_article_data(item_content, item_title, headers):
    logger.info("Getting html article data")
    if item_content['htmlArticle']:
        html_article_id = item_content['htmlArticle']['id']
        html_article_data = {"operationName": "GetHtmlArticle", "variables": {
            "htmlArticleId": f"{html_article_id}"}, "query": "query GetHtmlArticle($htmlArticleId: String!) {\n  htmlArticle(id: $htmlArticleId) {\n    id\n    html\n      }\n}\n"}
        html_article_content = json.loads(SESSION.post(
            url=LEETCODE_GRAPHQL_URL, headers=headers, json=html_article_data).content)['data']['htmlArticle']
        html_article = html_article_content['html']
        return f"""<h3>{item_title}</h3>
                    <md-block class="html_article__content">{html_article}</md-block>
                """
    return ""


def generate_similar_questions(similar_questions):
    logger.info("Generating similar questions")
    similar_questions_html = ""
    if similar_questions:
        similar_questions = json.loads(similar_questions)
        if similar_questions != []:
            similar_questions_html += f"""<div style="background: white;"><h3>Similar Questions</h3>"""
            for idx, similar_question in enumerate(similar_questions, start=1):
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

def get_all_submissions():
    headers = create_headers(CONFIG.leetcode_cookie)
    all_questions = get_all_questions_url(self_function=False)
    for question in all_questions:
        item_content = {"question": {'titleSlug': question['titleSlug'], 'frontendQuestionId': question['frontendQuestionId'], 'title': question['title']}}
        get_submission_data(item_content, headers, False)

def get_submission_data(item_content, headers, save_submission_as_file):

    list_of_submissions = {}

    if item_content['question']:
        question_frontend_id = int(item_content['question']['frontendQuestionId']) if item_content['question']['frontendQuestionId'] else 0
        question_title_slug = item_content['question']['titleSlug']

        submissions_root_dir = os.path.join(CONFIG.save_path, "cache", "submissions")
        os.makedirs(submissions_root_dir, exist_ok=True)
        
        submission_data_json_file = f"{question_frontend_id:04}.json"
        submission_data_json_path = os.path.join(submissions_root_dir, submission_data_json_file)

        if CONFIG.cache_downloads and os.path.exists(submission_data_json_path):
            with open(submission_data_json_path, "r") as file:
                submission_content = json.load(file)
        else:
            submission_data = {
                "query": "\n    query submissionList($offset: Int!, $limit: Int!, $lastKey: String, $questionSlug: String!, $lang: Int, $status: Int) {\n  questionSubmissionList(\n    offset: $offset\n    limit: $limit\n    lastKey: $lastKey\n    questionSlug: $questionSlug\n    lang: $lang\n    status: $status\n  ) {\n    lastKey\n    hasNext\n    submissions {\n      id\n      title\n      titleSlug\n      status\n      statusDisplay\n      lang\n      langName\n      runtime\n      timestamp\n      url\n      isPending\n      memory\n      hasNotes\n      notes\n      flagType\n      topicTags {\n        id\n      }\n    }\n  }\n}\n    ",
                "variables": {
                    "questionSlug": question_title_slug,
                    "offset": 0,
                    "limit": 20,
                    "lastKey": None
                },
                "operationName": "submissionList"
            }

            submission_object = SESSION.post(url=LEETCODE_GRAPHQL_URL, headers=headers, json=submission_data).content

            try:
                submission_content = json.loads(submission_object)
                submission_content = submission_content['data']['questionSubmissionList']['submissions']
            except:
                raise Exception("Error in getting submission data")

            with open(submission_data_json_path, "w") as outfile:
                outfile.write(json.dumps(submission_content))
            
        if not submission_content or len(submission_content) == 0:
            return

        for i, submission in enumerate(submission_content):
            submission_id = submission['id']
            if submission["statusDisplay"] != "Accepted":
                continue
            
            submission_detail_data = {
                "query":"\n    query submissionDetails($submissionId: Int!) {\n  submissionDetails(submissionId: $submissionId) {\n    runtime\n    runtimeDisplay\n    runtimePercentile\n    runtimeDistribution\n    memory\n    memoryDisplay\n    memoryPercentile\n    memoryDistribution\n    code\n    timestamp\n    statusCode\n    user {\n      username\n      profile {\n        realName\n        userAvatar\n      }\n    }\n    lang {\n      name\n      verboseName\n    }\n    question {\n      questionId\n      titleSlug\n      hasFrontendPreview\n    }\n    notes\n    flagType\n    topicTags {\n      tagId\n      slug\n      name\n    }\n    runtimeError\n    compileError\n    lastTestcase\n    totalCorrect\n    totalTestcases\n    fullCodeOutput\n    testDescriptions\n    testBodies\n    testInfo\n  }\n}\n    ",
                "variables":{
                    "submissionId": submission_id
                },
                "operationName":"submissionDetails"
            }
            submission_detail_object = SESSION.post(url=LEETCODE_GRAPHQL_URL, headers=headers, json=submission_detail_data).content
            submission_detail_content = json.loads(submission_detail_object)

            submission_detail_content = submission_detail_content['data']['submissionDetails']

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

def get_solution_content(question_id, question_title_slug, headers):
    logger.info("Getting solution data")

    question_data_root_dir = os.path.join(CONFIG.save_path, "cache", "soldata")
    os.makedirs(question_data_root_dir, exist_ok=True)

    sol_data_json_file = f"{question_id:04}.json"
    sol_data_json_path = os.path.join(question_data_root_dir, sol_data_json_file)

    if CONFIG.cache_downloads and os.path.exists(sol_data_json_path):
        with open(sol_data_json_path, "r") as file:
            sol_content = json.load(file)
    else:
        sol_query = {"query":"\n    query officialSolution($titleSlug: String!) {\n  question(titleSlug: $titleSlug) {\n    solution {\n      id\n      title\n      content\n      contentTypeId\n      paidOnly\n      hasVideoSolution\n      paidOnlyVideo\n      canSeeDetail\n      rating {\n        count\n        average\n        userRating {\n          score\n        }\n      }\n      topic {\n        id\n        commentCount\n        topLevelCommentCount\n        viewCount\n        subscribed\n        solutionTags {\n          name\n          slug\n        }\n        post {\n          id\n          status\n          creationDate\n          author {\n            username\n            isActive\n            profile {\n              userAvatar\n              reputation\n            }\n          }\n        }\n      }\n    }\n  }\n}\n    ",
                     "variables":{"titleSlug":question_title_slug},"operationName":"officialSolution"}
        sol_object = SESSION.post(url=LEETCODE_GRAPHQL_URL, headers=headers, json=sol_query).content

        try:
            sol_content = json.loads(sol_object)
            sol_content = sol_content['data']['question']['solution']
        except:
            raise Exception("Error in getting solution data")

        with open(sol_data_json_path, "w") as outfile:
            outfile.write(json.dumps(sol_content))

    solution = None
    if sol_content:
        solution = sol_content['content']
    return solution


def get_question_data(item_content, headers):
    logger.info("Getting question data")
    if item_content['question']:
        question_id = int(item_content['question']['frontendQuestionId']) if item_content['question']['frontendQuestionId'] else 0
        question_title_slug = item_content['question']['titleSlug']
        question_title = item_content['question']['title'] if item_content['question']['title'] else question_title_slug

        question_data_root_dir = os.path.join(CONFIG.save_path, "cache", "qdata")
        os.makedirs(question_data_root_dir, exist_ok=True)

        question_data_json_file = f"{question_id:04}.json"
        question_data_json_path = os.path.join(question_data_root_dir, question_data_json_file)

        if CONFIG.cache_downloads and os.path.exists(question_data_json_path):
            with open(question_data_json_path, "r") as file:
                question_content = json.load(file)
        else:
            question_data = {"operationName": "GetQuestion", "variables": {"titleSlug": question_title_slug},
                         "query": "query GetQuestion($titleSlug: String!) {\n  question(titleSlug: $titleSlug) {\n title\n submitUrl\n similarQuestions\n difficulty\n  companyTagStats\n codeDefinition\n    content\n    hints\n    solution {\n      content\n   }\n   }\n }\n"}
            question_object = SESSION.post(url=LEETCODE_GRAPHQL_URL, headers=headers, json=question_data).content

            try:
                question_content = json.loads(question_object)
                question_content = question_content['data']['question']
            except:
                raise Exception("Error in getting question data")

            with open(question_data_json_path, "w") as outfile:
                outfile.write(json.dumps(question_content))

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
        else:
            solution = "No Solution"
        hints = question_content['hints']

        if hints:
            hint_content = ""
            for hint in hints:
                hint_content += f"<div> > {hint}</div>"
        else:
            hint_content = "No Hints"

        submission_content = "No accepted submissions."

        if CONFIG.include_submissions_count > 0:
            item_content = {"question": {'titleSlug': question_title_slug, 'frontendQuestionId': question_id, 'title': question_title}}
            submissions = get_submission_data(item_content, headers, True)
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

 
        return f""" <h2 class="question__url"><a target="_blank" href="{question_url}">{question_id}. {question_title}</a></h2><p> Difficulty: {difficulty}</p>
                    <div>{company_tag_stats}</div>
                    <div>{similar_questions}</div>
                    <div><h3>Question</h3>
                    <md-block class="question__content">{question}</md-block></div>
                    <div><h3>Default Code</h3>
                    <pre class="question__default_code">{default_code}</pre></div>
                    <div><h3>Hints</h3>
                    <md-block class="question__hints">{hint_content}</md-block></div>
                    <div><h3>Solution</h3>
                    <md-block class="question__solution">{solution}</md-block></div>
                    <div><h3>Accepted Submissions</h3>{submission_content}</div>
                """, question_title
    return """""", ""


def create_card_index_html(chapters, card_slug, headers):
    logger.info("Creating index.html")
    intro_data = {"operationName": "GetExtendedCardDetail", "variables": {"cardSlug": card_slug},
                  "query": "query GetExtendedCardDetail($cardSlug: String!) {\n  card(cardSlug: $cardSlug) {\n title\n  introduction\n}\n}\n", }
    introduction = json.loads(SESSION.post(url=LEETCODE_GRAPHQL_URL, headers=headers,
                                            json=intro_data).content)['data']['card']
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
            body += f"""<a href="{item['id']}-{item['title']}.html">{item['id']}-{item['title']}</a><br>"""
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
    create_folder(os.path.join(CONFIG.save_path, "all_company_questions"))
    headers = create_headers(CONFIG.leetcode_cookie)
    final_company_tags = []

    with open(CONFIG.company_tag_save_path, 'r') as f:
        company_tags = f.readlines()
        for company_tag in company_tags:
            company_tag = company_tag.replace("\n", "").split("/")[-2]
            final_company_tags.append(
                {"name": company_tag,
                 'slug': company_tag})

    if choice == 9:
        create_all_company_index_html(final_company_tags, headers)
    elif choice == 10:
        for company in final_company_tags:
            company_slug = company['slug']
            scrape_question_data(company_slug, headers)
            os.chdir("..")
    os.chdir("..")

def get_next_data_id():
    next_data = SESSION.get(url="https://leetcode.com/problemset/", headers=create_headers()).content
    next_data_soup = BeautifulSoup(next_data, "html.parser")
    next_data_tag = next_data_soup.find('script', {'id': '__NEXT_DATA__'})
    next_data_json = json.loads(next_data_tag.text)
    next_data_id = next_data_json['props']['buildId']
    return next_data_id

def scrape_all_company_questions(choice):
    logger.info("Scraping all company questions")
    create_folder(os.path.join(CONFIG.save_path, "all_company_questions"))
    

    headers = create_headers(CONFIG.leetcode_cookie)
    company_data = {"operationName": "questionCompanyTags", "variables": {},
                        "query": "query questionCompanyTags {\n  companyTags {\n    name\n    slug\n    questionCount\n  }\n}\n"}
    company_tags = json.loads(SESSION.post(url=LEETCODE_GRAPHQL_URL, headers=headers,
                                                json=company_data).content)['data']['companyTags']

    if choice == 7:
        create_all_company_index_html(company_tags, headers)
    elif choice == 8:
        for company in company_tags:
            company_slug = company['slug']
            scrape_question_data(company_slug, headers)
            os.chdir("..")
    os.chdir('..')

def get_categories_slugs_for_company(company_slug, headers):
    companies_data_root_dir = os.path.join(CONFIG.save_path, "cache", "companies")
    os.makedirs(companies_data_root_dir, exist_ok=True)
    comapny_fav_data_json_file = f"{company_slug}-favdetails.json"
    company_fav_data_json_path = os.path.join(companies_data_root_dir, comapny_fav_data_json_file)

    if CONFIG.cache_downloads and os.path.exists(company_fav_data_json_path):
        with open(company_fav_data_json_path, "r") as file:
            favoriteDetails = json.load(file)
    else:
        try:
            company_fav_data = {"operationName": "favoriteDetailV2ForCompany", "variables": {"favoriteSlug": company_slug},
                    "query": "query favoriteDetailV2ForCompany($favoriteSlug: String!) {\n  favoriteDetailV2(favoriteSlug: $favoriteSlug) {\n    questionNumber\n    collectCount\n    generatedFavoritesInfo {\n      defaultFavoriteSlug\n      categoriesToSlugs {\n        categoryName\n        favoriteSlug\n        displayName\n      }\n    }\n  }\n}\n    "}

            response = SESSION.post(url=LEETCODE_GRAPHQL_URL, headers=headers, json=company_fav_data)
            response.raise_for_status()

            response_content = json.loads(response.content)
            favoriteDetails = response_content['data']['favoriteDetailV2']

            with open(company_fav_data_json_path, 'w') as f:
                f.write(json.dumps(favoriteDetails))

        except:
            raise Exception("Error in getting question data")
    
    return favoriteDetails


def create_all_company_index_html(company_tags, headers):
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

        favoriteDetails = get_categories_slugs_for_company(company_slug, headers)
        if not favoriteDetails:
            continue
        favoriteSlugs = {item["favoriteSlug"]: item["displayName"] for item in favoriteDetails['generatedFavoritesInfo']['categoriesToSlugs']}
        total_questions = favoriteDetails['questionNumber']

        company_root_dir = os.path.join(CONFIG.save_path, "all_company_questions", company_slug)
        os.makedirs(company_root_dir, exist_ok=True)

        if CONFIG.overwrite == False and "index.html" in os.listdir(company_root_dir):
            logger.info(f"Already Scraped {company_slug}")
            continue
        logger.info(f"Scrapping Index for {company_slug}")

        companies_data_root_dir = os.path.join(CONFIG.save_path, "cache", "companies")
        os.makedirs(companies_data_root_dir, exist_ok=True)

        overall_html = ''

        for favoriteSlug in favoriteSlugs:
            comapny_data_json_file = f"{favoriteSlug}.json"
            company_data_json_path = os.path.join(companies_data_root_dir, comapny_data_json_file)

            if CONFIG.cache_downloads and os.path.exists(company_data_json_path):
                with open(company_data_json_path, "r") as file:
                    company_questions = json.load(file)
            else:
                try:
                    company_data = {
                        "operationName": "favoriteQuestionList",
                        "variables": {
                            "favoriteSlug": favoriteSlug,
                            "filter": {
                                "positionRoleTagSlug": "",
                                "skip": 0,
                                "limit": total_questions
                            }
                        },
                        "query": "\n    query favoriteQuestionList($favoriteSlug: String!, $filter: FavoriteQuestionFilterInput) {\n  favoriteQuestionList(favoriteSlug: $favoriteSlug, filter: $filter) {\n    questions {\n      difficulty\n      id\n      paidOnly\n      questionFrontendId\n      status\n      title\n      titleSlug\n      translatedTitle\n      isInMyFavorites\n      frequency\n      topicTags {\n        name\n        nameTranslated\n        slug\n      }\n    }\n    totalLength\n    hasMore\n  }\n}\n    "}

                    response = SESSION.post(url=LEETCODE_GRAPHQL_URL, headers=headers, json=company_data)
                    response.raise_for_status()

                    company_response_content = json.loads(response.content)
                    company_questions = company_response_content['data']['favoriteQuestionList']['questions']
                    with open(company_data_json_path, 'w') as f:
                        f.write(json.dumps(company_questions))

                except:
                    raise Exception("Error in getting question data")


            html = ''
            for question in company_questions:
                questionFrontEndId = int(question['questionFrontendId'])
                question['title'] = re.sub(r'[:?|></\\]', replace_filename, question['title'])

                frequency = round(float(question['frequency']), 1)            
                frequency_label = '{:.2f}'.format(frequency)
                html += f'''<tr>
                            <td><a slug="{question['titleSlug']}" title="{questionFrontEndId:04}-{question['title']}.html" href="{questionFrontEndId:04}-{question['title']}.html">{questionFrontEndId:04}-{question['title']}.html</a></td>
                            <td> Difficulty: {question['difficulty']} </td><td>Frequency: {frequency_label}</td>
                            <td><a target="_blank" href="https://leetcode.com/problems/{question['titleSlug']}">Leetcode Url</a></td>
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


def scrape_question_data(company_slug, headers):
    logger.info("Scraping question data")

    questions_dir = os.path.join(CONFIG.save_path, "questions")
    questions_pdf_dir = os.path.join(questions_dir, "pdf")
    company_root_dir = os.path.join(CONFIG.save_path, "all_company_questions", company_slug)
    companies_data_root_dir = os.path.join(CONFIG.save_path, "cache", "companies")
    os.makedirs(questions_dir, exist_ok=True)
    os.makedirs(questions_pdf_dir, exist_ok=True)
    os.makedirs(company_root_dir, exist_ok=True)

    questions_seen = set()
    
    categoriesToSlug = get_categories_slugs_for_company(company_slug, headers)
    if not categoriesToSlug:
        return

    favoriteSlugs = [item["favoriteSlug"] for item in categoriesToSlug['generatedFavoritesInfo']['categoriesToSlugs']]

    for favoriteSlug in favoriteSlugs:
        company_data_json_path = os.path.join(companies_data_root_dir, f"{favoriteSlug}.json")

        if not os.path.exists(company_data_json_path):
            raise Exception(f"Company data not found {company_data_json_path}")

        with open(company_data_json_path, 'r') as f:
            questions = json.loads(f.read())

        company_fav_dir  = os.path.join(company_root_dir, favoriteSlug)
        os.makedirs(company_fav_dir, exist_ok=True)

        # sort by frequency, high frequency first
        questions = sorted(questions, key=lambda x: x['frequency'], reverse=True)

        question_sort_order_idx = 0
        
        for question in questions:
            question_id = int(question['questionFrontendId'])

            # skip already processed questions
            if question_id in questions_seen:
                continue
            questions_seen.add(question_id)

            question_sort_order_idx = question_sort_order_idx + 1

            
            question_title = question['title']
            question_slug = question['titleSlug']
            question_filename = re.sub(r'[:?|></\\]', replace_filename, question_title)

            question_filename = f"{question_id:04}-{question_title}"
            question_html_filename = f"{question_filename}.html"
            question_pdf_filename = f"{question_filename}.pdf"
       
            questions_html_path   = os.path.join(questions_dir, question_html_filename)
            questions_pdf_path   = os.path.join(questions_dir, "pdf", question_pdf_filename)

            company_html_path = os.path.join(company_fav_dir, question_html_filename)
            company_pdf_path = os.path.join(company_fav_dir, question_pdf_filename)

            if CONFIG.overwrite:
                create_question_html(question_id, question_slug, question_filename, headers)
                shutil.copy(company_html_path, questions_html_path)
            else:
                if os.path.exists(questions_html_path):
                    shutil.copy(questions_html_path, company_html_path)
                if os.path.exists(questions_pdf_path):
                    shutil.copy(questions_pdf_path, company_pdf_path)

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
                    res_soup = fix_image_urls(soup, True)
                with open(os.path.join(root, file), "w") as f:
                    f.write(res_soup.prettify())
    

if __name__ == '__main__':
    current_os = sys.platform
    SUBMISSIONS_API_URL = "https://leetcode.com/api/submissions/?offset={}&limit={}"
    LEETCODE_GRAPHQL_URL = "https://leetcode.com/graphql"
    SESSION = requests.Session()

    selected_config = "0"
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
        logger.info("Proxy set", SESSION.get(
            "https://httpbin.org/ip").content)

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

            if choice == 1:
                generate_config()
            elif choice == 2:
                select_config()
            elif choice == 3:
                get_all_cards_url()
            elif choice == 4:
                get_all_questions_url()
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
