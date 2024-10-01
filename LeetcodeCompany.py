import os
import json
from bs4 import BeautifulSoup

from LeetcodeUtility import LeetcodeUtility

class LeetcodeCompany:
    def __init__(self, config, logger, leetapi, question):
        self.config = config
        self.logger = logger
        self.lc = leetapi
        self.question = question

    def scrape_selected_company_questions(self, choice):
        all_comp_dir = os.path.join(self.configsave_path, "all_company_questions")
        os.makedirs(all_comp_dir, exist_ok=True)
        os.chdir(all_comp_dir)
        
        final_company_tags = []

        with open(self.configcompany_tag_save_path, 'r') as f:
            company_tags = f.readlines()
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

    def get_next_data_id(self):
        data_path = LeetcodeUtility.get_cache_path("company", "nextdataid.html")

        next_data = self.lc.cached_query(
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

    def scrape_all_company_questions(self, choice):
        self.logger.info("Scraping all company questions")

        company_tags = self.lc.get_question_company_tags()

        all_comp_dir = os.path.join(self.configsave_path, "all_company_questions")
        os.makedirs(all_comp_dir, exist_ok=True)  
        os.chdir(all_comp_dir)

        if choice == 7:
            self.create_all_company_index_html(company_tags)
        elif choice == 8:
            for company in company_tags:
                company_slug = company['slug']
                self.question.scrape_question_data(company_slug)
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
        with open(self.configcompany_tag_save_path, 'w') as f:
            for _ in range(rows):
                html += '<tr>'
                for _ in range(cols):
                    if company_idx < len(company_tags):
                        html += f'''<td><a href="{company_tags[company_idx]['slug']}/index.html">{company_tags[company_idx]['slug']}</a></td>'''
                        f.write(f"https://leetcode.com/company/{company_tags[company_idx]['slug']}/\n")
                        company_idx += 1
                html += '</tr>'

        with open(os.path.join(self.configsave_path, "all_company_questions", "index.html"), 'w') as f:
            f.write(f"""<!DOCTYPE html>
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

            company_root_dir = os.path.join(self.configsave_path, "all_company_questions", company_slug)
            os.makedirs(company_root_dir, exist_ok=True)

            if not self.configforce_download and "index.html" in os.listdir(company_root_dir):
                self.logger.info(f"Already Scraped {company_slug}")
                continue
            self.logger.info(f"Scrapping Index for {company_slug}")

            data_dir = os.path.join(self.configsave_path, "cache", "companies")
            os.makedirs(data_dir, exist_ok=True)

            overall_html = ''

            for favoriteSlug in favoriteSlugs:
                company_questions = self.lc.get_favorite_question_list_for_company(favoriteSlug, total_questions)

                html = ''
                for question in company_questions:
                    questionFrontEndId = int(question['questionFrontendId'])
                    question['title'] = re.sub(r'[:?|></\\]', replace_filename, question['title'])

                    frequency = round(float(question['frequency']), 1)            
                    frequency_label = '{:.1f}'.format(frequency)
                    question_title_format = LeetcodeUtility.qbasename(questionFrontEndId, question['title'])
                    question_fname = LeetcodeUtility.qhtml(questionFrontEndId, question['title'])
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

    def scrape_question_data(self, company_slug):
        self.logger.info("Scraping question data")

        questions_dir = os.path.join(self.configsave_path, "questions")
        questions_pdf_dir = os.path.join(self.configsave_path, "questions_pdf")
        company_root_dir = os.path.join(self.configsave_path, "all_company_questions", company_slug)
        data_dir = os.path.join(self.configsave_path, "cache", "companies")
        os.makedirs(questions_dir, exist_ok=True)
        os.makedirs(questions_pdf_dir, exist_ok=True)
        os.makedirs(company_root_dir, exist_ok=True)

        questions_seen = set()
        
        categoriesToSlug = self.get_categories_slugs_for_company(company_slug)
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
        
                if self.configforce_download:
                    self.create_question_html(question_id, question_slug, question_title)
                
                copied = LeetcodeUtility.copy_question_file(self.config.SAVE_PATH, question_id, question_title, company_fav_dir)

                # if copy failed retry
                if not copied:
                    self.logger.warning("Copy failed downloading again and retrying copy")
                    self.create_question_html(question_id, question_slug, question_title)
                    LeetcodeUtility.copy_question_file(self.config.SAVE_PATH, question_id, question_title, company_fav_dir)
