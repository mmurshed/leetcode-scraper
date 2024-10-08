import datetime
import os

from logging import Logger
from typing import List
from bs4 import BeautifulSoup

from ai.OpenAISolutionGenerator import OpenAISolutionGenerator
from utils.Constants import Constants
from utils.Util import Util
from utils.Config import Config

from api.ApiManager import ApiManager

from models.Question import Question
from models.QuestionContent import QuestionContent

from downloaders.ImageDownloader import ImageDownloader
from downloaders.SolutionDownloader import SolutionDownloader
from downloaders.SubmissionDownloader import SubmissionDownloader

class QuestionDownloader:
    def __init__(
        self, 
        config: Config,
        logger: Logger,
        leetapi: ApiManager,
        solutiondownloader: SolutionDownloader,
        imagedownloader: ImageDownloader,
        submissiondownloader: SubmissionDownloader,
        ai_solution_generator: OpenAISolutionGenerator):
        
        self.config = config
        self.logger = logger
        self.lc = leetapi
        self.submissiondownloader = submissiondownloader
        self.solutiondownloader = solutiondownloader
        self.imagedownloader = imagedownloader
        self.ai_solution_generator = ai_solution_generator
    
    def create_question_index(self, questions):
        os.makedirs(self.config.questions_directory, exist_ok=True)
        filepath = os.path.join(self.config.questions_directory, "index.html")

        count = 0
        html = f"""<tr><th>Id</th><th style="width:70%">Title</th><th>Difficulty</th></tr>"""
        for question in questions:
            count += 1
            filename = Util.qhtml(question.id, question.title)

            html += f'''<tr>
                        <td><a target="_blank" href="{Constants.LEETCODE_URL}/problems/{question.slug}">{question.id}</a></td>
                        <td><a slug="{question.slug}" title="{question.title}" href="{filename}">{question.title}</a></td>
                        <td>{question.difficulty}</td>
                        </tr>'''

        html = f"""<!DOCTYPE html><html lang="en"><head></head><body><h1>All Questions</h1><p>Total questions {count}</p><table>{html}</table></body></html>"""
        with open(filepath, 'w') as ifile:
            ifile.write(html)

    def download_selected_question(self, question_id: int):
        questions = self.lc.get_all_questions()

        questions = [question for question in questions if question.id == question_id]
        if len(questions) == 0:
            self.logger.error(f"Question id not found {question_id}")
            return
        self.create_question_html(questions[0], self.config.questions_directory, True)

        self.create_question_index(questions)


    def download_all_questions(self):
        questions = self.lc.get_all_questions()

        not_downloaded_questions, _ = self.filter_out_downloaded(questions, self.config.questions_directory)
        
        for question in not_downloaded_questions:
            self.create_question_html(question, self.config.questions_directory, False)

        self.create_question_index(questions)

    def filter_out_downloaded(self, questions, root_dir):
        if self.config.overwrite:
            return questions

        downloaded = []
        not_downloaded = []

        for question in questions:
            filepath = os.path.join(root_dir, Util.qhtml(question.id, question.title))
            
            if os.path.exists(filepath):
                downloaded.append(question)
            else:
                not_downloaded.append(question)

        if downloaded and len(downloaded) > 0:
            self.logger.info(f"Already downloaded")
            for question in downloaded:
                self.logger.info(f"Question id: {question.id}")
        return not_downloaded, downloaded

    #region html generation
    def create_question_html(self, question: Question, root_dir, generate_ai_solution=False):           
        self.logger.info(f"Scraping question {question.id}")

        question_html = self.get_question_html(question, root_dir, generate_ai_solution)
        content = f"""{Constants.HTML_HEADER}<body>{question_html}</body>"""
        content_soup = BeautifulSoup(content, 'html.parser')
        content_soup = self.imagedownloader.fix_image_urls(content_soup, question.id, root_dir)

        question_path = os.path.join(root_dir, Util.qhtml(question.id, question.title))
        with open(question_path, 'w', encoding="utf-8") as file:
            file.write(content_soup.prettify())

    def get_similar_questions_html(self, similar_questions):
        self.logger.info("Generating similar questions")
        similar_questions_html = """"""

        if not similar_questions or similar_questions == []:
            return similar_questions_html

        similar_questions_html += f"""<div style="background: white;"><h3>Similar Questions</h3>"""
        for idx, similar_question in enumerate(similar_questions, start=1):
            # similar_question = question_html(similar_question['title'], similar_question['title'])
            similar_questions_html += f"""<div class="similar-questions-container"><div>{idx}. <a target="_blank" href="https://leetcode.com/problems/{similar_question['titleSlug']}">{similar_question['title']}</a> ({similar_question['difficulty']}) <a target="_blank" href="./{similar_question['title']}.html">Local</a></div></div>"""
        similar_questions_html += f"""</div>"""

        return similar_questions_html

    def get_company_tag_stats_html(self, company_tag_stats):
        company_tag_stats_html = ""

        if not company_tag_stats or company_tag_stats == {}:
            return company_tag_stats_html

        company_tag_stats =  {int(k): v for k, v in sorted(company_tag_stats.items(), key=lambda item: int(item[0]))}

        company_tag_stats_html += f"""<div style="background: white;"><h3>Company Tag Stats</h3>"""

        for key, value in company_tag_stats.items():
            company_tag_stats_html += f"""<h4>Years: {str(key-1)}-{str(key)}</h4><div>"""

            for idx, company_tag_stat in enumerate(value):
                if idx != 0:
                    company_tag_stats_html += ", "
                company_tag_stats_html += f"""{company_tag_stat['name']}"""
                company_tag_stats_html += f""": {company_tag_stat['timesEncountered']}"""

            company_tag_stats_html += """</div>"""

        company_tag_stats_html += """</div>"""

        return company_tag_stats_html

    def get_question_html(self, question: Question, root_dir, generate_ai_solution=False):
        self.logger.info("Getting question data")
        question_content_data = self.lc.get_question(question.id, question.slug)
        question_content = QuestionContent.from_json(question_content_data)

        company_tag_stats = self.get_company_tag_stats_html(question_content.company_tag_stats)
        similar_questions = self.get_similar_questions_html(question_content.similar_questions)

        question_html = ""
        if question_content.content:
            question_html = Util.markdown_with_math(question_content.content)
            question_html = f"""
                        <div><h3>Question</h3>
                        <md-block class="question__content">{question_html}</md-block></div>
            """
        
        hint_html = ""
        if question_content.hints:
            for hint in question_content.hints:
                hint = str.strip(hint)
                hint = Util.markdown_with_math(hint)
                hint = str.strip(hint)
                hint_html += f"""<li>{hint}</li>"""
            
            hint_html += f"""<div><ul>{hint_html}</ul></div>"""
            hint_html = f"""<div><h3>Hints</h3><md-block class="question__hints">{hint_html}</md-block></div>"""

        submission_html = ""
        if self.config.include_submissions_count > 0:
            submissions = self.submissiondownloader.get_submission_data(question.id, question.slug, False, self.config.include_submissions_count)
            if submissions and len(submissions) > 0:
                for timestamp, code in submissions.items():
                    submission_time = datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H.%M.%S")
                    submission_html += f"""<div><h4>Submission Time: {submission_time}</h4>
                    <pre class="question__default_code">{code}</pre></div>"""

                submission_html = f"""
                        <div><h3>Accepted Submissions</h3>
                        {submission_html}</div>"""
        
        default_code_html = """"""
        if self.config.include_default_code:
            default_code_html = f"""
                            <div><h3>Default Code</h3>
                            <pre class="question__default_code">{question_content.default_code}</pre></div>
                """            

        solution_html = """"""
        if question_content.solution:
            solution_html = Util.markdown_with_math(question_content.solution)
            solution_html = self.solutiondownloader.replace_iframes_with_content(solution_html, question.id, root_dir)
            solution_html = self.solutiondownloader.replace_slides_json(solution_html, question.id)
            solution_html = f"""
                <div><h3>Solution</h3>
                <md-block class="question__solution">{solution_html}</md-block></div>"""
        elif generate_ai_solution and self.config.open_ai_api_key:
            generated_solution = self.ai_solution_generator.cached_generate(question, question_content)
            if generated_solution:
                solution_html = Util.markdown_with_math(generated_solution)
                solution_html = f"""
                    <div><h3>AI Generated Solution</h3>
                    <md-block class="question__solution">{solution_html}</md-block></div>"""

        question_header_html = f"""<h2 class="question__url"><a target="_blank" href="{question_content.url}">{question.id}. {question_content.title}</a></h2>"""
        question_difficulty_html = f"""Difficulty: {question_content.difficulty}"""
        question_full_html = f"""{question_header_html}{question_difficulty_html}{question_html}{hint_html}{default_code_html}{solution_html}{company_tag_stats}{similar_questions}{submission_html}"""

        question_full_html = f""" {question_header_html}
                        {question_html}
                        {hint_html}
                        {default_code_html}
                        {solution_html}
                        {company_tag_stats}
                        {similar_questions}
                        {submission_html}
                    """
        return question_full_html

    #endregion html generation