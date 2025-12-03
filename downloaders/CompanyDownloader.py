import os

from logging import Logger
from typing import List

from models.Company import Company
from models.Question import Question

from utils.Util import Util
from utils.Constants import Constants
from utils.Config import Config

from api.ApiManager import ApiManager

from downloaders.QuestionDownloader import QuestionDownloader

class CompanyDownloader:
    def __init__(
        self, 
        config: Config,
        logger: Logger,
        leetapi: ApiManager,
        questiondownloader: QuestionDownloader):

        self.config = config
        self.logger = logger
        self.lc = leetapi
        self.questiondownloader = questiondownloader
        
    def get_company_slugs(self) -> List[Company]:
        company_data = self.lc.get_question_company_tags()
        companies = [Company.from_json(company) for company in company_data]
        return companies
    

    def download_selected_company_questions(self, company_slug):
        companies = self.get_company_slugs()

        company_slugs = {company.slug for company in companies}
        if not companies or company_slug not in company_slugs:
            self.logger.error(f"Company not valid {company_slug}")
            return

        favorite_details = self.get_company_question_data(company_slug)
        self.create_company_directories(company_slug, favorite_details)
        self.create_company_indices(company_slug, favorite_details)
        self.download_all_company_questions(company_slug, favorite_details)

    def download_favorite_company_questions(self, company_slug, fav_slug):
        companies = self.get_company_slugs()

        company_slugs = {company.slug for company in companies}
        if not companies or company_slug not in company_slugs:
            self.logger.error(f"Company not valid {company_slug}")
            return
        
        favorite_details = self.get_company_question_data(company_slug)

        if not favorite_details or fav_slug not in favorite_details.keys():
            self.logger.error(f"Company favorite slug not valid for company: {company_slug} favorite: {fav_slug}")
            return
        
        _, questions = favorite_details[fav_slug]

        self.create_company_directories(company_slug, favorite_details)
        self.create_company_indices(company_slug, favorite_details)
        self.download_all_favorite_company_questions(company_slug, fav_slug, questions)

    def download_all_company_questions(self):
        self.logger.debug("Scraping all company questions")

        companies = self.get_company_slugs()
        self.create_all_company_index(companies)

        for company in companies:
            favorite_details = self.get_company_question_data(company.slug)
            self.create_company_directories(company.slug, favorite_details)
            self.create_company_indices(company.slug, favorite_details)
            self.download_all_company_questions(company.slug, favorite_details)
    
    def create_all_company_index(self, companies: List[Company]):
        self.logger.debug("Creating company index.html")
        cols = 10
        rows = len(companies)//10 + 1
        html = ''
        company_idx = 0

        for _ in range(rows):
            html += '<tr>'
            for _ in range(cols):
                if company_idx < len(companies):
                    company = companies[company_idx]
                    html += f'''<td><a href="{company.slug}/index.html">{company.slug}</a></td>'''
                    company_idx += 1
            html += '</tr>'

        filepath = os.path.join(self.config.companies_directory, "index.html")
        with open(filepath, 'w') as file:
            file.write(f"""<!DOCTYPE html><html lang="en"><head></head><body><table>{html}</table></body></html>""")
    
    def get_company_favorite_slugs(self, company_slug):
        favorite_details_data = self.lc.get_favorite_details_for_company(company_slug)

        if not favorite_details_data:
            self.logger.error(f"Company favorite details not found {company_slug}")
            return

        favorite_slugs = [ (item["favoriteSlug"], item["displayName"]) for item in favorite_details_data['generatedFavoritesInfo']['categoriesToSlugs']]
        
        return favorite_slugs


    def get_company_question_data(self, company_slug):
        favorite_details_data = self.lc.get_favorite_details_for_company(company_slug)

        if not favorite_details_data:
            self.logger.error(f"Company favorite details not found {company_slug}")
            return

        favorite_details = {}
        favorite_slugs = {item["favoriteSlug"]: item["displayName"] for item in favorite_details_data['generatedFavoritesInfo']['categoriesToSlugs']}
        total_questions = favorite_details_data['questionNumber']
        
        for favorite_slug, display_name in favorite_slugs.items():
            questions_data = self.lc.get_favorite_question_list_for_company(favorite_slug, total_questions)
            questions = [Question.from_json(question_data) for question_data in questions_data]

            favorite_details[favorite_slug] = (display_name, questions)
        
        return favorite_details
    
    def create_company_directories(self, company_slug, favorite_details):
        company_root_dir = os.path.join(self.config.companies_directory, company_slug)
        os.makedirs(company_root_dir, exist_ok=True)

        for favorite_slug, _ in favorite_details.items():
            company_fav_dir  = os.path.join(self.config.companies_directory, company_slug, favorite_slug)
            os.makedirs(company_fav_dir, exist_ok=True)

    def create_company_indices(self, company_slug, favorite_details):
        company_root_dir = os.path.join(self.config.companies_directory, company_slug)
        root_index_file = os.path.join(company_root_dir, "index.html")

        overall_html = ''
        questions_seen = set()

        for favorite_slug, (display_name, questions) in favorite_details.items():
            company_fav_dir  = os.path.join(self.config.companies_directory, company_slug, favorite_slug)
            html = f"""<tr><th>Id</th><th style="width:70%">Title</th><th>Difficulty</th><th>Solved</th></tr>"""
            
            count = 0
            solved_count = 0
            for question in questions:
                if question.id in questions_seen:
                    continue

                questions_seen.add(question.id)
                if question.solved:
                    solved_count += 1
                count += 1

                # frequency_label = '{:.1f}'.format(round(question.frequency, 1))
                question_fname = Util.qhtml(question.id, question.title)
                solved_label = 'Y' if question.solved else '-'
                html += f'''<tr>
                            <td><a target="_blank" href="{Constants.LEETCODE_URL}/problems/{question.slug}">{question.id}</a></td>
                            <td><a slug="{question.slug}" title="{question.title}" href="{question_fname}">{question.title}</a></td>
                            <td>{question.difficulty} </td>
                            <td>{solved_label}</td>
                            </tr>'''

            # Write each favorite slug
            fav_file = os.path.join(company_fav_dir, f"{favorite_slug}.html")
            with open(fav_file, 'w') as file:
                file.write(f"""<!DOCTYPE html><html lang="en"><head></head><body><h1>{company_slug} {display_name}</h1><p>Solved {solved_count} out of total {count} questions. Most frequent questions first.</p><table>{html}</table></body></html>""")
            
            overall_html += f"""<h1>{display_name}</h1><table>{html}</table>"""

        # Write index html
        with open(root_index_file, 'w') as file:
            file.write(f"""<!DOCTYPE html>
                <html lang="en">
                <head> </head>
                <body>{overall_html}</body>
                </html>""")

    def download_all_company_questions(self, company_slug, favorite_details):
        self.logger.debug("Scraping question data")

        questions_seen = set()
        
        for favorite_slug, (_, questions) in favorite_details.items():
            self.download_all_favorite_company_questions(company_slug, favorite_slug, questions, questions_seen)

    def download_all_favorite_company_questions(self, company_slug, favorite_slug, questions, questions_seen=set()):
        self.logger.debug("Scraping question data")
        
        company_fav_dir  = os.path.join(self.config.companies_directory, company_slug, favorite_slug)
        
        # Check which questions are already downloaded in the company directory
        downloaded_questions = []
        not_downloaded_questions = []
        
        for question in questions:
            question_filepath = os.path.join(company_fav_dir, Util.qhtml(question.id, question.title))
            # Check if exists: if "always", download anyway; if "new", skip if exists
            if os.path.exists(question_filepath) and self.config.download_questions != "always":
                downloaded_questions.append(question)
            else:
                not_downloaded_questions.append(question)

        # skip already processed questions
        questions_seen.update([question.id for question in downloaded_questions])
        
        for question in not_downloaded_questions:
            # skip already processed questions
            if question.id in questions_seen:
                continue
            questions_seen.add(question.id)

            self.download_company_question(question, company_fav_dir)


    def download_company_question(self, question: Question, company_fav_dir):
        # If "always", recreate the question HTML directly
        if self.config.download_questions == "always":
            self.questiondownloader.create_question_html(
                question=question,
                root_dir=company_fav_dir)
            return

        # Otherwise, try to copy from questions directory
        copied = Util.copy_question_file(
            question_id=question.id,
            question_title=question.title,
            dest_dir=company_fav_dir,
            questions_dir=self.config.questions_directory)

        # if copy failed just download
        if not copied:
            self.logger.warning(f"Copy failed {question.id}")
            self.questiondownloader.create_question_html(
                question=question,
                root_dir=company_fav_dir)


