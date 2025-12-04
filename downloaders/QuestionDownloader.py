import datetime
import os

from logging import Logger
from bs4 import BeautifulSoup

from ai.AISolution import AISolution
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
        ai_solution_generator: AISolution):
        
        self.config = config
        self.logger = logger
        self.lc = leetapi
        self.submissiondownloader = submissiondownloader
        self.solutiondownloader = solutiondownloader
        self.imagedownloader = imagedownloader
        self.ai_solution_generator = ai_solution_generator
    
    def get_question_folder(self, question_id: int) -> str:
        """Get the folder name for a question based on its ID (grouped by hundreds)"""
        folder_number = ((question_id - 1) // 100 + 1) * 100
        return f"{folder_number:04d}"
    
    def get_question_directory(self, question_id: int) -> str:
        """Get the full directory path for a question"""
        folder_name = self.get_question_folder(question_id)
        return os.path.join(self.config.questions_directory, folder_name)
    
    def create_question_index(self, questions):
        os.makedirs(self.config.questions_directory, exist_ok=True)
        
        # Group questions by subdirectory
        questions_by_folder = {}
        for question in questions:
            folder_name = self.get_question_folder(question.id)
            if folder_name not in questions_by_folder:
                questions_by_folder[folder_name] = []
            questions_by_folder[folder_name].append(question)
        
        # Create index.html in each subdirectory
        subdirectory_info = []
        for folder_name in sorted(questions_by_folder.keys()):
            folder_questions = sorted(questions_by_folder[folder_name], key=lambda q: int(q.id))
            folder_path = os.path.join(self.config.questions_directory, folder_name)
            os.makedirs(folder_path, exist_ok=True)
            
            # Generate HTML for this folder's index
            folder_html = f"""<tr><th>Id</th><th style="width:70%">Title</th><th>Difficulty</th></tr>"""
            for question in folder_questions:
                filename = Util.qhtml(question.id, question.title)
                
                folder_html += f'''<tr>
                            <td><a target="_blank" href="{Constants.LEETCODE_URL}/problems/{question.slug}">{question.id}</a></td>
                            <td><a slug="{question.slug}" title="{question.title}" href="{filename}">{question.title}</a></td>
                            <td>{question.difficulty}</td>
                            </tr>'''
            
            # Write subdirectory index.html
            folder_index_path = os.path.join(folder_path, "index.html")
            folder_html_full = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>Questions {folder_name}</title></head>
                                  <body><h1>Questions {folder_name}</h1>
                                  <p><a href="../index.html">← Back to All Questions</a></p>
                                  <p>Total questions: {len(folder_questions)}</p>
                                  <table border="1" cellpadding="5" cellspacing="0">{folder_html}</table>
                                  </body></html>"""
            with open(folder_index_path, 'w') as f:
                f.write(folder_html_full)
            
            # Track info for root index
            subdirectory_info.append((folder_name, len(folder_questions)))
        
        # Create root index.html with links to subdirectories
        root_index_path = os.path.join(self.config.questions_directory, "index.html")
        
        # Generate table with subdirectory links
        subdirs_html = f"""<tr><th>Folder</th><th>Question Range</th><th>Count</th></tr>"""
        total_count = 0
        for folder_name, count in subdirectory_info:
            total_count += count
            # Extract range from folder name (e.g., "0100" -> "1-199")
            folder_num = int(folder_name)
            range_start = folder_num
            range_end = folder_num + 99
            subdirs_html += f'''<tr>
                        <td><a href="{folder_name}/index.html">{folder_name}/</a></td>
                        <td>{range_start}-{range_end}</td>
                        <td>{count}</td>
                        </tr>'''
        
        root_html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>All Questions</title></head>
                       <body><h1>All Questions</h1>
                       <p>Total questions: {total_count}</p>
                       <h2>Browse by Range</h2>
                       <table border="1" cellpadding="5" cellspacing="0">{subdirs_html}</table>
                       </body></html>"""
        with open(root_index_path, 'w') as f:
            f.write(root_html)

    def download_selected_question(self, question_id: int):
        questions = self.lc.get_all_questions()

        questions = [question for question in questions if question.id == question_id]
        if len(questions) == 0:
            self.logger.error(f"Question id not found {question_id}")
            return
        
        question_dir = self.get_question_directory(questions[0].id)
        self.create_question_html(questions[0], question_dir)

        self.create_question_index(questions)


    def download_all_questions(self):
        questions = self.lc.get_all_questions()

        not_downloaded_questions, _ = self.filter_out_downloaded(questions)
        
        for question in not_downloaded_questions:
            question_dir = self.get_question_directory(question.id)
            self.create_question_html(question, question_dir)

        self.create_question_index(questions)

    def filter_out_downloaded(self, questions):
        # If download_questions is "always", download everything (skip nothing)
        if self.config.download_questions == "always":
            return questions, []  # Not downloaded: everything, downloaded: nothing

        downloaded = []
        not_downloaded = []

        for question in questions:
            question_dir = self.get_question_directory(question.id)
            filepath = os.path.join(question_dir, Util.qhtml(question.id, question.title))
            
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
    def create_question_html(self, question: Question, root_dir):           
        self.logger.debug(f"Scraping question {question.id}")
        
        # Ensure the directory exists
        os.makedirs(root_dir, exist_ok=True)

        question_html = self.get_question_html(question, root_dir)
        content = f"""{Constants.HTML_HEADER}<body>{question_html}</body>"""
        content_soup = BeautifulSoup(content, 'html.parser')
        content_soup = self.imagedownloader.fix_image_urls(content_soup, question.id, root_dir)

        question_path = os.path.join(root_dir, Util.qhtml(question.id, question.title))
        with open(question_path, 'w', encoding="utf-8") as file:
            file.write(content_soup.prettify())

    def get_similar_questions_html(self, similar_questions):
        self.logger.debug("Generating similar questions")
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

    def get_question_html(self, question: Question, root_dir):
        self.logger.debug("Getting question data")
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
        elif self.ai_solution_generator:
            generated_solution = self.ai_solution_generator.get_solution(question, question_content)
            if generated_solution:
                solution_html = Util.markdown_with_math(generated_solution)
                solution_html = f"""
                    <div><h3>AI Generated Solution ({self.config.ai_solution_generator})</h3>
                    <md-block class="question__solution">{solution_html}</md-block></div>"""

        community_solution_html = ""
        if not question_content.solution and self.config.include_community_solution_count > 0:
            community_solutions = self.lc.get_all_community_solutions(question.slug)
        
            for idx, community_solution in enumerate(community_solutions, start=1):
                if idx > self.config.include_community_solution_count:
                    break

                community_solution_content = self.lc.get_community_solution_content(int(community_solution['id']))
                if community_solution_content:
                    community_solution_content = Util.markdown_with_math(community_solution_content)
                    community_solution_html += f"""<div><h4>{community_solution['title']}</h4>
                    <md-block class="question__solution">{community_solution_content}</md-block></div>"""

            if community_solution_html:
                community_solution_html = f"""
                        <div><h3>Community Solutions</h3>
                        {community_solution_html}</div>"""


        question_header_html = f"""<h2 class="question__url"><a target="_blank" href="{question_content.url}">{question.id}. {question_content.title}</a></h2>"""
        question_difficulty_html = f"""Difficulty: {question_content.difficulty}"""
        question_full_html = f"""{question_header_html}{question_difficulty_html}{question_html}{hint_html}{default_code_html}{solution_html}{company_tag_stats}{similar_questions}{submission_html}"""

        question_full_html = f""" {question_header_html}
                        {question_html}
                        {hint_html}
                        {default_code_html}
                        {solution_html}
                        {community_solution_html}
                        {company_tag_stats}
                        {similar_questions}
                        {submission_html}
                    """
        return question_full_html

    #endregion html generation