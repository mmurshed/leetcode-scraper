import os
import re

from logging import Logger
from bs4 import BeautifulSoup

from LeetcodeConstants import LeetcodeConstants
from LeetcodeUtility import LeetcodeUtility
from LeetcodeImage import LeetcodeImage
from LeetcodeSolution import LeetcodeSolution
from LeetcodeConfig import LeetcodeConfig
from LeetcodeApi import LeetcodeApi
from LeetcodeQuestion import LeetcodeQuestion
from LeetcodeArticle import LeetcodeArticle

class LeetcodeCards:
    def __init__(
        self, 
        config: LeetcodeConfig,
        logger: Logger,
        leetapi: LeetcodeApi,
        questionhandler: LeetcodeQuestion,
        solutionhandler: LeetcodeSolution,
        imagehandler: LeetcodeImage):

        self.config = config
        self.logger = logger
        self.lc = leetapi
        self.article = LeetcodeArticle(config, logger, leetapi)
        self.question = questionhandler
        self.solution = solutionhandler
        self.imagehandler = imagehandler

    def get_cards_dir(self):
        dir = os.path.join(self.config.save_directory, "cards")
        os.makedirs(dir, exist_ok=True)
        return dir

    def get_all_cards_url(self):
        self.logger.info("Getting all cards url")

        cards = self.lc.get_categories()

        with open(self.config.cards_filepath, "w") as file:
            for category_card in cards:
                if category_card['slug'] != "featured":
                    for card in category_card['cards']:
                        card_url = f"{LeetcodeConstants.LEETCODE_URL}/explore/{card['categorySlug']}/card/{card['slug']}/\n"
                        file.write(card_url)


    def scrape_card_url(self):
        cards_dir = self.get_cards_dir()
        os.chdir(cards_dir)

        # Creating Index for Card Folder
        with open(os.path.join(cards_dir, "index.html"), 'w') as main_index:
            main_index_html = ""
            with open(self.config.cards_filepath, "r") as file:
                card_urls = file.readlines()
                for card_url in card_urls:
                    card_url = card_url.strip()
                    card_slug = card_url.split("/")[-2]
                    main_index_html += f"""<a href={card_slug}/index.html>{card_slug}</a><br>"""        
            main_index.write(main_index_html)

        # Creating HTML for each cards topics
        with open(self.config.cards_filepath, "r") as file:
            card_urls = file.readlines()
            for card_url in card_urls:
                card_url = card_url.strip()

                self.logger.info(f"Scraping card url: {card_url}")

                card_slug = card_url.split("/")[-2]

                chapters = self.lc.get_chapter_with_items(card_slug)

                if chapters:
                    cards_dir = os.path.join(self.get_cards_dir(), card_slug)
                    os.makedirs(cards_dir, exist_ok=True)
                    
                    self.create_card_index_html(chapters, card_slug)
                    for subcategory in chapters:
                        self.logger.info(f"Scraping subcategory: {subcategory['title']}")

                        for item in subcategory['items']:
                            self.logger.info(f"Scraping Item: {item['title']}")

                            item_id = item['id']
                            item_title = re.sub(r'[:?|></\\]', LeetcodeUtility.replace_filename, item['title'])

                            filename = LeetcodeUtility.qhtml(item_id, item_title)
                            
                            cards_filepath = os.path.join(cards_dir, filename)

                            if not self.config.overwrite and os.path.exists(cards_filepath):
                                self.logger.info(f"Already scraped {cards_filepath}")
                                continue

                            if self.config.overwrite or not LeetcodeUtility.copy_question_file(self.config.SAVE_PATH, item_id, item_title, cards_dir):
                                item_content = self.lc.get_chapter_items(card_slug, item_id)

                                if item_content:
                                    self.create_card_html(item_content, item_title, item_id)
                    os.chdir("..")
        os.chdir('..')


    def create_card_html(self, item_content, item_title, item_id):
        content = """<body>"""
        question_content, _ = self.question.get_question_data(item_content)
        content += question_content
        content += self.article.get_article_data(item_content, item_title, item_id)
        content += self.article.get_html_article_data(item_content, item_title)
        content += """</body>"""
        slides_json = self.solution.find_slides_json(content, item_id)
        content = LeetcodeConstants.HTML_HEADER + content
        content_soup = BeautifulSoup(content, 'html.parser')
        content_soup = self.solution.place_solution_slides(content_soup, slides_json)
        content_soup = self.imagehandler.fix_image_urls(content_soup, item_id)

        card_path = os.path.join(self.get_cards_dir(), LeetcodeUtility.qhtml(item_id, item_title))
        with open(card_path, "w", encoding="utf-8") as f:
            f.write(content_soup.prettify())

    def create_card_index_html(self, chapters, card_slug):
        self.logger.info("Creating index.html")

        introduction = self.lc.get_card_details(card_slug)

        body = ""
        for chapter in chapters:
            body += f"""
                        <br>
                        <h3>{chapter['title']}</h3>
                        {chapter['description']}
                        <br>
            """
            for item in chapter['items']:
                item['title'] = re.sub(r'[:?|></\\]', LeetcodeUtility.replace_filename, item['title'])
                item_fname = LeetcodeUtility.qhtml(item['id'], item['title'])
                body += f"""<a href="{item_fname}">{item['id']}-{item['title']}</a><br>"""
        with open("index.html", 'w') as f:
            f.write(f"""<!DOCTYPE html>
                    <html lang="en">
                    {LeetcodeConstants.HTML_HEADER}
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
