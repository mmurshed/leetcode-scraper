import os
import json
import re

from logging import Logger
from bs4 import BeautifulSoup

from LeetcodeUtility import LeetcodeUtility
from LeetcodeConstants import LeetcodeConstants
from LeetcodeConfig import LeetcodeConfig
from LeetcodeApi import LeetcodeApi
from LeetcodeQuestion import LeetcodeQuestion

class LeetcodeCompany:
    def __init__(
        self, 
        config: LeetcodeConfig,
        logger: Logger,
        leetapi: LeetcodeApi,
        questionhandler: LeetcodeQuestion):

        self.config = config
        self.logger = logger
        self.lc = leetapi
        self.questionhandler = questionhandler

    def scrape_selected_company_questions(self, choice):
        all_comp_dir = os.path.join(self.config.save_directory, "all_company_questions")
        os.makedirs(all_comp_dir, exist_ok=True)
        os.chdir(all_comp_dir)
        
        final_company_tags = []

        with open(self.config.company_filepath, 'r') as file:
            company_tags = file.readlines()
            for company_tag in company_tags:
                company_tag = company_tag.replace("\n", "").split("/")[-2]

                final_company_tags.append({
                    'name': company_tag,
                    'slug': company_tag
                })

        if choice == 9:
            self.create_all_company_index_html(final_company_tags)
        elif choice == 10:
            for company in final_company_tags:
                company_slug = company['slug']
                self.scrape_question_data(company_slug)
                os.chdir("..")
        os.chdir("..")

    def scrape_all_company_questions(self, choice):
        self.logger.info("Scraping all company questions")

        company_tags = self.lc.get_question_company_tags()

        all_comp_dir = os.path.join(self.config.save_directory, "all_company_questions")
        os.makedirs(all_comp_dir, exist_ok=True)  
        os.chdir(all_comp_dir)

        if choice == 7:
            self.create_all_company_index_html(company_tags)
        elif choice == 8:
            for company in company_tags:
                company_slug = company['slug']
                self.questionhandler.scrape_question_data(company_slug)
                os.chdir("..")
        os.chdir('..')

    def get_categories_slugs_for_company(self, company_slug):
        favoriteDetails = self.lc.get_favorite_details_for_company(company_slug)
        return favoriteDetails

    def create_all_company_index_html(self, company_tags):
        self.logger.info("Creating company index.html")
        cols = 10
        rows = len(company_tags)//10 + 1
        html = ''
        company_idx = 0
        with open(self.config.company_filepath, 'w') as file:
            for _ in range(rows):
                html += '<tr>'
                for _ in range(cols):
                    if company_idx < len(company_tags):
                        html += f'''<td><a href="{company_tags[company_idx]['slug']}/index.html">{company_tags[company_idx]['slug']}</a></td>'''
                        file.write(f"{LeetcodeConstants.LEETCODE_URL}/company/{company_tags[company_idx]['slug']}/\n")
                        company_idx += 1
                html += '</tr>'

        with open(os.path.join(self.config.save_directory, "all_company_questions", "index.html"), 'w') as file:
            file.write(f"""<!DOCTYPE html>
                    <html lang="en">
                    <head> </head>
                    <body>
                        '<table>{html}</table>'
                    </body>
                    </html>""")
        
        for company in company_tags:
            company_slug = company['slug']

            favoriteDetails = self.get_categories_slugs_for_company(company_slug)
            if not favoriteDetails:
                continue
            favoriteSlugs = {item["favoriteSlug"]: item["displayName"] for item in favoriteDetails['generatedFavoritesInfo']['categoriesToSlugs']}
            total_questions = favoriteDetails['questionNumber']

            company_root_dir = os.path.join(self.config.save_directory, "all_company_questions", company_slug)
            os.makedirs(company_root_dir, exist_ok=True)

            if not self.config.overwrite and "index.html" in os.listdir(company_root_dir):
                self.logger.info(f"Already Scraped {company_slug}")
                continue
            self.logger.info(f"Scrapping Index for {company_slug}")

            data_dir = os.path.join(self.config.save_directory, "cache", "companies")
            os.makedirs(data_dir, exist_ok=True)

            overall_html = ''

            for favoriteSlug in favoriteSlugs:
                company_questions = self.lc.get_favorite_question_list_for_company(favoriteSlug, total_questions)

                html = ''
                for question in company_questions:
                    questionFrontEndId = int(question['questionFrontendId'])
                    question['title'] = re.sub(r'[:?|></\\]',LeetcodeUtility.replace_filename, question['title'])

                    frequency = round(float(question['frequency']), 1)            
                    frequency_label = '{:.1f}'.format(frequency)
                    question_title_format = LeetcodeUtility.qbasename(questionFrontEndId, question['title'])
                    question_fname = LeetcodeUtility.qhtml(questionFrontEndId, question['title'])
                    html += f'''<tr>
                                <td><a slug="{question['titleSlug']}" title="{question_title_format}" href="{question_fname}">{question_title_format}</a></td>
                                <td>Difficulty: {question['difficulty']} </td><td>Frequency: {frequency_label}</td>
                                <td><a target="_blank" href="{LeetcodeConstants.LEETCODE_URL}/problems/{question['titleSlug']}">Leet</a></td>
                                </tr>'''
                # Write each favorite slug
                with open(os.path.join(company_root_dir, f"{favoriteSlug}.html"), 'w') as file:
                    file.write(f"""<!DOCTYPE html>
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
            with open(os.path.join(company_root_dir, "index.html"), 'w') as file:
                file.write(f"""<!DOCTYPE html>
                    <html lang="en">
                    <head> </head>
                    <body>{overall_html}</body>
                    </html>""")
            os.chdir("..")

    def scrape_question_data(self, company_slug):
        self.logger.info("Scraping question data")

        questions_dir = os.path.join(self.config.save_directory, "questions")
        questions_pdf_dir = os.path.join(self.config.save_directory, "questions_pdf")
        company_root_dir = os.path.join(self.config.save_directory, "all_company_questions", company_slug)
        os.makedirs(questions_dir, exist_ok=True)
        os.makedirs(questions_pdf_dir, exist_ok=True)
        os.makedirs(company_root_dir, exist_ok=True)

        questions_seen = set()
        
        categoriesToSlug = self.get_categories_slugs_for_company(company_slug)
        if not categoriesToSlug:
            return

        favoriteSlugs = [item["favoriteSlug"] for item in categoriesToSlug['generatedFavoritesInfo']['categoriesToSlugs']]
        total_questions = categoriesToSlug['questionNumber']
        
        for favoriteSlug in favoriteSlugs:
            questions = self.lc.get_favorite_question_list_for_company(favoriteSlug, total_questions)

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
        
                if self.config.overwrite:
                    self.questionhandler.create_question_html(question_id, question_slug, question_title)
                
                copied = LeetcodeUtility.copy_question_file(self.config.save_directory, question_id, question_title, company_fav_dir)

                # if copy failed retry
                if not copied:
                    self.logger.error("Copy failed")
