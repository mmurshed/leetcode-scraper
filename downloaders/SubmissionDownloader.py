import os

from logging import Logger

from utils.Constants import Constants
from utils.Util import Util
from utils.Config import Config

from api.ApiManager import ApiManager

from models.Submission import Submission

class SubmissionDownloader:
    def __init__(
        self,
        config: Config,
        logger: Logger,
        leetapi: ApiManager):

        self.config = config
        self.logger = logger
        self.lc = leetapi

    def get_selected_submissions(self, question_id: int):
        questions = self.lc.get_all_questions()
        
        questions = [question for question in questions if question.id == question_id]
        if len(questions) == 0:
            self.logger.error(f"Question id not found {question_id}")
            return

        self.get_submission_data(questions[0].id, questions[0].slug, True)


    def get_all_submissions(self):
        submissions = self.lc.get_all_submissions()

        for submission in submissions:
            self.get_submission_data(question_id=submission.id, question_slug=submission.slug, save_submission_as_file=True, accepted_only=False, limit=None)

    def get_submission_data(self, question_id, question_slug, save_submission_as_file, limit = None, accepted_only = True):

        submissions_code = {}

        question_id = int(question_id)

        submissions_data = self.lc.get_submission_list(question_id, question_slug)
        if not submissions_data or len(submissions_data) == 0:
            self.logger.debug(f"Submission wasn't downloaded {question_id}")
            return
        
        if accepted_only:
            submissions = [Submission.from_json(submission) for submission in submissions_data if submission['statusDisplay'] == "Accepted"]
        else:
            submissions = [Submission.from_json(submission) for submission in submissions_data]
        
        limit = limit or len(submissions)        
        
        # Sorted by timestamp in descending order, take n
        submissions = sorted(submissions, key=lambda item: item.timestamp, reverse=True)[:limit]

        submissions_code = {}

        for i, submission in enumerate(submissions):
            submission_detail_content = self.lc.get_submission_details(question_id, submission.id)
            if not submission_detail_content:
                self.logger.error(f"Submission detail wasn't downloaded {question_id} submission {submission.id}")
                continue
            
            submissions_code[submission.timestamp] = submission_detail_content['code']
            
            if save_submission_as_file:
                submissions_dir = os.path.join(self.config.submissions_directory, Util.qstr(question_id))
                os.makedirs(submissions_dir, exist_ok=True)

                file_extension = Constants.FILE_EXTENSIONS[submission.lang]
                submission_file_name = f"{i+1:02}-{submission.id}.{file_extension}"
                submission_file_path = os.path.join(submissions_dir, submission_file_name)

                if not os.path.exists(submission_file_path):
                    with open(submission_file_path, "w") as outfile:
                        outfile.write(submission_detail_content['code'])                
            
        return submissions_code
