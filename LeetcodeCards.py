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
        self.question = questionhandler
        self.solution = solutionhandler
        self.imagehandler = imagehandler

    def get_all_cards_urls(self):
        if not os.path.exists(self.config.cards_filepath):
            self.download_all_cards_urls()

        return self.load_all_cards_urls()

    def load_all_cards_urls(self):
        cards = {}
        if os.path.exists(self.config.cards_filepath):
            with open(self.config.cards_filepath, "r") as file:
                card_urls = file.readlines()
                for card_url in card_urls:
                    card_url = card_url.strip()
                    card_slug = card_url.split("/")[-2]
                    cards[card_slug] = card_url
        return cards

    def download_all_cards_urls(self):
        self.logger.info("Getting all cards url")

        cards = self.lc.get_categories()

        with open(self.config.cards_filepath, "w") as file:
            for category_card in cards:
                if category_card['slug'] != "featured":
                    for card in category_card['cards']:
                        card_url = f"{LeetcodeConstants.LEETCODE_URL}/explore/{card['categorySlug']}/card/{card['slug']}/\n"
                        file.write(card_url)


    def create_cards_top_index(self, cards):
        # Creating Index for Card Folder
        filepath = os.path.join(self.config.cards_directory, "index.html")
        with open(filepath, 'w') as main_index:
            main_index_html = ""
            for card_slug, _ in cards.items():
                main_index_html += f"""<a href={card_slug}/index.html>{card_slug}</a><br>"""
            main_index.write(main_index_html)

    def scrape_selected_card(self, card_slug):
        os.makedirs(self.config.cards_directory, exist_ok=True)
        os.chdir(self.config.cards_directory)

        cards = self.get_all_cards_urls()
        self.create_cards_top_index(cards)

        if card_slug not in cards.keys():
            self.logger.error(f"Card index not found {card_slug}")
            return

        # Creating HTML for each cards topics
        self.logger.info(f"Scraping card url: {cards[card_slug]}")
        chapters = self.lc.get_chapters_with_items(card_slug)

        if chapters:
            self.create_chapters(card_slug, chapters)
            os.chdir("..")
        os.chdir('..')

    def scrape_card_url(self):
        os.makedirs(self.config.cards_directory, exist_ok=True)
        os.chdir(self.config.cards_directory)

        cards = self.get_all_cards_urls()
        self.create_cards_top_index(cards)

        # Creating HTML for each cards topics
        for card_slug, card_url in cards.items():
            self.logger.info(f"Scraping card url: {card_url}")
            chapters = self.lc.get_chapters_with_items(card_slug)

            if chapters:
                self.create_chapters(card_slug, chapters)
                os.chdir("..")
        os.chdir('..')

    def create_chapters(self, card_slug, chapters):
        cards_chapter_dir = os.path.join(self.config.cards_directory, card_slug)
        os.makedirs(cards_chapter_dir, exist_ok=True)
        
        self.create_card_index_html(chapters, card_slug, cards_chapter_dir)
        for subcategory in chapters:
            self.logger.info(f"Scraping chapter subcategory: {subcategory['title']}")

            for item in subcategory['items']:
                self.logger.info(f"Scraping Item: {item['title']}")

                item_id = item['id']
                item_title = re.sub(r'[:?|></\\]', LeetcodeUtility.replace_filename, item['title'])

                filename = LeetcodeUtility.qhtml(item_id, item_title)
                
                cards_filepath = os.path.join(cards_chapter_dir, filename)

                if not self.config.overwrite and os.path.exists(cards_filepath):
                    self.logger.info(f"Already scraped {cards_filepath}")
                    continue
                
                copied = False
                if not self.config.overwrite:
                    copied = LeetcodeUtility.copy_question_file(
                        save_path=self.config.save_directory,
                        question_id=item_id,
                        question_title=item_title,
                        dest_dir=cards_chapter_dir,
                        questions_dir=self.config.questions_directory)
                
                if self.config.overwrite or not copied:
                    item_content = self.lc.get_chapter_items(card_slug, item_id)

                    if item_content:
                        self.create_card_html(item_content, item_title, item_id, cards_chapter_dir)


    def create_card_html(self, item_content, item_title, item_id, cards_chapter_dir):
        content = """<body>"""
        question_content, _ = self.question.get_question_data(item_content)
        content += question_content
        content += self.get_article_data(item_content, item_title, item_id)
        content += self.get_html_article_data(item_content, item_title)
        content += """</body>"""
        slides_json = self.solution.find_slides_json(content, item_id)
        content = LeetcodeConstants.HTML_HEADER + content
        content_soup = BeautifulSoup(content, 'html.parser')
        content_soup = self.solution.place_solution_slides(content_soup, slides_json)
        content_soup = self.imagehandler.fix_image_urls(content_soup, item_id, cards_chapter_dir)

        card_path = os.path.join(cards_chapter_dir, LeetcodeUtility.qhtml(item_id, item_title))
        with open(card_path, "w", encoding="utf-8") as f:
            f.write(content_soup.prettify())

    def create_card_index_html(self, chapters, card_slug, cards_chapter_dir):
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

        filepath = os.path.join(cards_chapter_dir, "index.html")
        with open(filepath, 'w') as file: 
            file.write(f"""<!DOCTYPE html>
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

    def get_article_data(self, item_content, item_title, question_id):
        self.logger.info("Getting article data")

        article_data = ""

        if item_content['article']:
            article_id = item_content['article']['id']

            article_content = self.lc.get_article(question_id, article_id)

            article_content = LeetcodeUtility.markdown_with_math(article_content)

            article_data = f"""<h3>{item_title}</h3>
                        <md-block class="article__content">{article_content}</md-block>
                    """
        return article_data

    def get_html_article_data(self, item_content, item_title):
        self.logger.info("Getting html article data")

        html_article_data = ""
        if item_content['htmlArticle']:
            html_article_id = item_content['htmlArticle']['id']

            html_article = self.lc.get_html_article(html_article_id)

            html_article = LeetcodeUtility.markdown_with_math(html_article)

            html_article_data = f"""<h3>{item_title}</h3>
                        <md-block class="html_article__content">{html_article}</md-block>
                    """
        return html_article_data

