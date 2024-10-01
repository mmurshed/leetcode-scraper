import os
import csv
import re
import json
from bs4 import BeautifulSoup

from LeetcodeUtility import LeetcodeUtility
from LeetcodeImage import LeetcodeImage
from LeetcodePdfConverter import LeetcodePdfConverter

class LeetcodeQuestion:
    def __init__(self, config, logger, leetapi):
        self.config = config
        self.logger = logger
        self.lc = leetapi

    def get_all_questions_url(self, force_download):
        self.logger.info("Getting all questions url")

        all_questions_count = self.lc.get_questions_count()
        all_questions_count = int(all_questions_count)

        self.logger.info(f"Total no of questions: {all_questions_count}")

        all_questions = self.lc.get_all_questions(all_questions_count)

        if force_download:
            self.write_questions_to_file(all_questions, self.configquestions_url_path)

        return all_questions


    def write_questions_to_file(self, all_questions, questions_url_path):
        with open(questions_url_path, "w") as f:
            for question in all_questions:
                frontendQuestionId = question['frontendQuestionId']
                question_url = "https://leetcode.com/problems/" + \
                    question['titleSlug'] + "/\n"
                f.write(f"{frontendQuestionId},{question_url}")


    def scrape_question_url(self, selected_question_id = None):
        all_questions = self.get_all_questions_url(force_download=self.configforce_download)
        questions_dir = os.path.join(self.configsave_path, "questions")
        os.makedirs(questions_dir, exist_ok=True)
        os.chdir(questions_dir)

        # Convert the list of questions to a dictionary using titleSlug as the key
        questions_dict = {question['titleSlug']: question for question in all_questions}

        with open(self.configquestions_url_path) as f:
            for row in csv.reader(f):
                question_id = int(row[0])
                question_url = row[1]
                question_url = question_url.strip()
                question_slug = question_url.split("/")[-2]

                if selected_question_id and question_id != selected_question_id:
                    continue

                if question_slug in questions_dict:
                    question = questions_dict[question_slug]
                    question_title = re.sub(r'[:?|></\\]', LeetcodeUtility.replace_filename, question['title'])
                else:
                    raise Exception(f"Question id {question_id}, slug {question_slug} not found")

                question_file = LeetcodeUtility.question_html(question_id, question_title)
                question_path = os.path.join(questions_dir, question_file)
                
                if self.configforce_download or not os.path.exists(question_path):            
                    self.logger.info(f"Scraping question {question_id} url: {question_url}")
                    self.create_question_html(question_id, question_slug, question_title)
                else:
                    self.logger.info(f"Already scraped {question_file}")

            if self.configconvert_to_pdf:
                for row in csv.reader(f):
                    converted = LeetcodePdfConverter.convert_file(question_id, question_title, overwrite=self.configforce_download)
                    if not converted:
                        self.logger.info(f"Compressing images and retrying pdf convert")
                        LeetcodeImage.recompress_images(question_id)
                        converted = LeetcodePdfConverter.convert_file(question_id, question_title, overwrite=True)
                
        with open(os.path.join(questions_dir, "index.html"), 'w') as main_index:
            main_index_html = ""
            for idx, files in enumerate(os.listdir(questions_dir),start=1):
                if "index.html" not in files:
                    main_index_html += f"""<a href="{files}">{idx}-{files}</a><br>"""
            main_index.write(main_index_html)
        os.chdir('..')


    def create_question_html(self, question_id, question_slug, question_title):
        item_content = {
            "question": {
                'titleSlug': question_slug,
                'frontendQuestionId': question_id,
                'title': question_title
            }
        }
        content = """<body>"""
        question_content, question_title = self.get_question_data(item_content)
        content += question_content
        content += """</body>"""
        slides_json = find_slides_json2(content, question_id)
        content = self.attach_header_in_html() + content
        content_soup = BeautifulSoup(content, 'html.parser')
        content_soup = place_solution_slides(content_soup, slides_json)
        content_soup = fix_image_urls(content_soup, question_id)

        question_path = os.path.join(self.configsave_path, "questions", question_html(question_id, question_title))
        with open(question_path, 'w', encoding="utf-8") as f:
            f.write(content_soup.prettify())

    def generate_similar_questions(self, similar_questions):
        self.logger.info("Generating similar questions")
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

    def get_question_company_tag_stats(self, company_tag_stats):
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


    def get_question_data(self, item_content):
        self.logger.info("Getting question data")
        if item_content['question']:
            question_id = int(item_content['question']['frontendQuestionId']) if item_content['question']['frontendQuestionId'] else 0
            question_title_slug = item_content['question']['titleSlug']
            question_title = item_content['question']['title'] if item_content['question']['title'] else question_title_slug

            question_content = self.lc.get_question(question_id_title(question_id, 'qdat'), question_title_slug)

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
                    hint = convert_display_math_to_inline(hint)
                    hint = str.strip(hint)
                    hint = markdown_with_math(hint)
                    hint = str.strip(hint)
                    hint_content += f"<li>{hint}</li>"
                hint_content += f"<div><ul>{hint_content}</ul></div>"
                

            submission_content = None

            if self.configinclude_submissions_count > 0:
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
                    ordered_submissions = ordered_submissions[:self.configinclude_submissions_count]

                    submission_content = ""
                    for sub_timestamp, code in ordered_submissions:
                        submission_time = datetime.datetime.fromtimestamp(sub_timestamp).strftime("%Y-%m-%d %H.%M.%S")
                        submission_content += f"""<div><h4>Submission Time: {submission_time}</h4>
                        <pre class="question__default_code">{code}</pre></div>"""

            question = convert_display_math_to_inline(question)
            question = markdown_with_math(question)
            
            solution = convert_display_math_to_inline(solution)
            if solution:
                solution = markdown_with_iframe(solution)
                solution = replace_iframes_with_codes(solution, question_id)
                solution = wrap_slides_with_p_tags(solution)

            default_code_html = """"""
            if self.configinclude_default_code:
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
        
                if self.configforce_download:
                    self.create_question_html(question_id, question_slug, question_title)
                
                copied = copy_question_file(question_id, question_title, company_fav_dir)

                # if copy failed retry
                if not copied:
                    self.logger.warning("Copy failed downloading again and retrying copy")
                    self.create_question_html(question_id, question_slug, question_title)
                    copy_question_file(question_id, question_title, company_fav_dir)
