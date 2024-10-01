import os

from LeetcodeUtility import LeetcodeUtility

class LeetcodeSubmission:
    def __init__(self, config, logger, leetapi):
        self.config = config
        self.logger = logger
        self.lc = leetapi

    def get_all_submissions(self, question):
        all_questions = question.get_all_questions_url(force_download=self.config.force_download)

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

            submission_content = self.lc.get_submission_list(LeetcodeUtility.qbasename(question_frontend_id, 'subm'), question_title_slug)
            if not submission_content or len(submission_content) == 0:
                return

            for i, submission in enumerate(submission_content):
                submission_id = submission['id']
                if submission["statusDisplay"] != "Accepted":
                    continue

                submission_detail_content = self.lc.get_submission_details(LeetcodeUtility.qbasename(question_frontend_id, submission_id), submission_id)
                if not submission_detail_content:
                    continue
                
                if save_submission_as_file:
                    list_of_submissions[int(submission["timestamp"])] = submission_detail_content['code']
                else:
                    submissions_download_dir = os.path.join(self.config.save_path, "questions", "submissions")
                    os.makedirs(submissions_download_dir, exist_ok=True)

                    file_extension = LeetcodeUtility.FILE_EXTENSIONS[submission["lang"]]
                    submission_file_name = f"{question_frontend_id:04}-{i+1:02}-{submission_id}.{file_extension}"
                    submission_file_path = os.path.join(submissions_download_dir, submission_file_name)

                    with open(submission_file_path, "w") as outfile:
                        outfile.write(submission_detail_content['code'])
        return list_of_submissions
