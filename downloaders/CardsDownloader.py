import os

from logging import Logger
from typing import List
from bs4 import BeautifulSoup

from models.Card import Card
from models.Question import Question

from utils.Constants import Constants
from utils.Util import Util
from utils.Config import Config

from api.ApiManager import ApiManager

from downloaders.ImageDownloader import ImageDownloader
from downloaders.SolutionDownloader import SolutionDownloader
from downloaders.QuestionDownloader import QuestionDownloader

class CardsDownloader:
    def __init__(
        self, 
        config: Config,
        logger: Logger,
        leetapi: ApiManager,
        questiondownloader: QuestionDownloader,
        solutiondownloader: SolutionDownloader,
        imagehdownloader: ImageDownloader):

        self.config = config
        self.logger = logger
        self.lc = leetapi
        self.questiondownloader = questiondownloader
        self.solutiondownloader = solutiondownloader
        self.imagedownloader = imagehdownloader

    #region card urls
    def get_cards(self) -> List[Card]:
        categories_data = self.lc.get_categories()
        cards = []
        for card_category in categories_data:
            if card_category['slug'] != "featured":
                for card in card_category['cards']:
                    cards.append(Card.from_json(card))

        return cards

    #endregion card urls
    def create_card_index(self, chapters, card_slug, cards_chapter_dir):
        self.logger.info("Creating index.html")

        card_details = self.lc.get_card_details(card_slug)

        body = ""
        for chapter in chapters:
            body += f"""<br><h3>{chapter['title']}</h3>{chapter['description']}<br>"""

            for item in chapter['items']:
                item['title'] = Util.sanitize_title(item['title'])
                item_fname = Util.qhtml(item['id'], item['title'])
                
                body += f"""<a href="{item_fname}">{item_fname}</a><br>"""

        html = f"""<!DOCTYPE html><html lang="en">{Constants.HTML_HEADER}<body>
                    <div class="mode">Dark mode:  <span class="change">OFF</span></div>"
                    <h1 class="card-title">{card_details['title']}</h1>
                    <p class="card-text">{card_details['introduction']}</p><br>
                    {body}</body></html>"""

        filepath = os.path.join(cards_chapter_dir, "index.html")
        with open(filepath, 'w') as file: 
            file.write(html)

    def create_cards_main_index(self, cards: List[Card]):
        os.makedirs(self.config.cards_directory, exist_ok=True)

        # Creating Index for Card Folder
        filepath = os.path.join(self.config.cards_directory, "index.html")
        with open(filepath, 'w') as main_index:
            main_index_html = ""
            for card in cards:
                main_index_html += f"<a href={card.slug}/index.html>{card.slug}</a><br>"
            main_index.write(main_index_html)

    def download_selected_card(self, card_slug):
        cards = self.get_cards()
        self.create_cards_main_index(cards)

        card_slugs = {card.slug for card in cards}
        if not cards or card_slug not in card_slugs:
            self.logger.error(f"Card index not found {card_slug}")
            return

        # Creating HTML for each cards topics
        self.logger.info(f"Scraping card url: {card_slug}")
        chapters = self.lc.get_chapters_with_items(card_slug)

        if chapters:
            self.create_chapters(card_slug, chapters)

    def download_all_cards(self):
        cards = self.get_cards()
        self.create_cards_main_index(cards)

        # Creating HTML for each cards topics
        for card in cards:
            self.logger.info(f"Scraping card url: {card.slug}")
            chapters = self.lc.get_chapters_with_items(card.slug)

            if chapters:
                self.create_chapters(card.slug, chapters)

    def create_chapters(self, card_slug, chapters):
        cards_chapter_dir = os.path.join(self.config.cards_directory, card_slug)
        os.makedirs(cards_chapter_dir, exist_ok=True)
        
        self.create_card_index(chapters, card_slug, cards_chapter_dir)

        for chapter in chapters:
            chapter_items = {item['id']: Util.sanitize_title(item['title']) for item in chapter['items']}
            chapter_items = self.filter_out_downloaded(chapter_items, cards_chapter_dir)

            for item_id, item_title in chapter_items.items():
                item_content = self.lc.get_chapter_items(card_slug, item_id)
                if item_content:
                    self.create_card_html(item_content, item_title, item_id, cards_chapter_dir)


    def filter_out_downloaded(self, items, root_dir):
        if self.config.overwrite:
            return items

        downloaded = {}
        not_downloaded = {}

        for id, title in items.items():
            filepath = os.path.join(root_dir, Util.qhtml(id, title))
            if os.path.exists(filepath):
                downloaded[id] = title
            else:
                not_downloaded[id] = title

        if downloaded and len(downloaded) > 0:
            self.logger.info(f"Already downloaded")
            for id, title in downloaded:
                self.logger.info(f"Item id: {id}")
        return not_downloaded

    def create_card_html(self, item_content, item_title, item_id, cards_chapter_dir):
        self.logger.info(f"Scraping chapter item: {item_title}")
        
        content = ""

        if item_content['question']:
            question = Question.from_json(item_content['question'])
            question_html = self.questiondownloader.get_question_html(question, cards_chapter_dir)
            content += question_html

        if item_content['article']:
            content += self.get_article_html(item_content['article']['id'], cards_chapter_dir)
        
        if item_content['htmlArticle']:
            content += self.get_html_article_html(item_content['htmlArticle']['id'], item_title, item_id)

        content = f"""<body>{content}</body>"""

        content = self.solutiondownloader.replace_slides_json(content, item_id)

        content = Constants.HTML_HEADER + content

        content_soup = BeautifulSoup(content, 'html.parser')

        content_soup = self.imagedownloader.fix_image_urls(content_soup, item_id, cards_chapter_dir)

        card_path = os.path.join(cards_chapter_dir, Util.qhtml(item_id, item_title))
        with open(card_path, "w", encoding="utf-8") as file:
            file.write(content_soup.prettify())

    def get_article_html(self, article_id, item_title, item_id):
        self.logger.info("Getting article data")
        article_content = self.lc.get_article(item_id, article_id)
        article_content = Util.markdown_with_math(article_content)
        article_html = f"""<h3>{item_title}</h3><md-block class="article__content">{article_content}</md-block>"""
        return article_html

    def get_html_article_html(self, html_article_id, item_title, item_id):
        self.logger.info("Getting html article data")
        html_article = self.lc.get_html_article(item_id, html_article_id)
        html_article = Util.markdown_with_math(html_article)
        html_article_html = f"""<h3>{item_title}</h3><md-block class="html_article__content">{html_article}</md-block>"""
        return html_article_html

