from logging import Logger

from LeetcodeUtility import LeetcodeUtility
from LeetcodeConfig import LeetcodeConfig
from LeetcodeApi import LeetcodeApi

class LeetcodeArticle:
    def __init__(
        self, 
        config: LeetcodeConfig,
        logger: Logger,
        leetapi: LeetcodeApi):

        self.config = config
        self.logger = logger
        self.lc = leetapi

    def get_article_data(self, item_content, item_title, question_id):
        self.logger.info("Getting article data")

        article_data = ""

        if item_content['article']:
            article_id = item_content['article']['id']

            article_content = self.lc.get_article(question_id, article_id)

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

            html_article_data = f"""<h3>{item_title}</h3>
                        <md-block class="html_article__content">{html_article}</md-block>
                    """
        return html_article_data

