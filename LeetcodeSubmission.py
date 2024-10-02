import os

from logging import Logger

from LeetcodeConstants import LeetcodeConstants
from LeetcodeUtility import LeetcodeUtility
from LeetcodeConfig import LeetcodeConfig
from LeetcodeApi import LeetcodeApi

class LeetcodeSubmission:
    def __init__(
        self,
        config: LeetcodeConfig,
        logger: Logger,
        leetapi: LeetcodeApi):

        self.config = config
        self.logger = logger
        self.lc = leetapi

    def get_selected_submissions(self, questionhandler, question_id):
        all_questions = questionhandler.get_all_questions_url(force_download=self.config.overwrite)
        
        selected_question = None
        for question in all_questions:
            if question['frontendQuestionId'] == question_id:
                selected_question = question
                break

        if selected_question is None:
            self.logger.error(f"Question id not found {question_id}")
            return

        item_content = {
            "question": {
                'titleSlug': selected_question['titleSlug'],
                'frontendQuestionId': selected_question['frontendQuestionId'],
                'title': selected_question['title']
            }
        }

        self.get_submission_data(item_content, False)


    def get_all_submissions(self, questionhandler):
        all_questions = questionhandler.get_all_questions_url(force_download=self.config.overwrite)

        for question in all_questions:
            item_content = {
                "question": {
                    'titleSlug': question['titleSlug'],
                    'frontendQuestionId': question['frontendQuestionId'],
                    'title': question['title']
                }
            }
            self.get_submission_data(item_content, False)

    def get_submission_data(self, item_content, save_submission_as_file):

        list_of_submissions = {}

        if item_content['question']:
            question_frontend_id = int(item_content['question']['frontendQuestionId']) if item_content['question']['frontendQuestionId'] else 0
            question_title_slug = item_content['question']['titleSlug']

            submission_content = self.lc.get_submission_list(question_frontend_id, question_title_slug)
            if not submission_content or len(submission_content) == 0:
                return

            for i, submission in enumerate(submission_content):
                submission_id = submission['id']
                if submission["statusDisplay"] != "Accepted":
                    continue

                submission_detail_content = self.lc.get_submission_details(question_frontend_id, submission_id)
                if not submission_detail_content:
                    continue
                
                if save_submission_as_file:
                    list_of_submissions[int(submission["timestamp"])] = submission_detail_content['code']
                else:
                    submissions_download_dir = os.path.join(self.config.save_directory, "questions", "submissions")
                    os.makedirs(submissions_download_dir, exist_ok=True)

                    file_extension = LeetcodeConstants.FILE_EXTENSIONS[submission["lang"]]
                    submission_file_name = f"{question_frontend_id:04}-{i+1:02}-{submission_id}.{file_extension}"
                    submission_file_path = os.path.join(submissions_download_dir, submission_file_name)

                    with open(submission_file_path, "w") as outfile:
                        outfile.write(submission_detail_content['code'])
        return list_of_submissions
