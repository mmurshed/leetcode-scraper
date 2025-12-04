class SubmissionProgress:
    """Model for user's submission progress on a question."""
    
    def __init__(
        self,
        frontend_id: str,
        title: str,
        title_slug: str,
        difficulty: str,
        question_status: str,
        last_result: str,
        last_submitted_at: str,
        num_submitted: int,
        translated_title: str = None,
        topic_tags: list = None
    ):
        self.frontend_id = frontend_id
        self.title = title
        self.title_slug = title_slug
        self.difficulty = difficulty
        self.question_status = question_status
        self.last_result = last_result
        self.last_submitted_at = last_submitted_at
        self.num_submitted = num_submitted
        self.translated_title = translated_title
        self.topic_tags = topic_tags or []
    
    @staticmethod
    def from_json(data: dict) -> 'SubmissionProgress':
        """Creates a SubmissionProgress instance from a JSON-like dictionary.
        
        Expected data format from API:
        {
            "translatedTitle": null,
            "frontendId": "1526",
            "title": "Minimum Number of Increments...",
            "titleSlug": "minimum-number-of-increments...",
            "difficulty": "HARD",
            "lastSubmittedAt": "2024-10-07T23:57:20+00:00",
            "numSubmitted": 1,
            "questionStatus": "SOLVED",
            "lastResult": "AC",
            "topicTags": [{"name": "Array", "nameTranslated": "", "slug": "array"}, ...]
        }
        """
        frontend_id = data.get('frontendId', '')
        title = data.get('title', '')
        title_slug = data.get('titleSlug', '')
        difficulty = data.get('difficulty', '')
        question_status = data.get('questionStatus', '')
        last_result = data.get('lastResult', '')
        last_submitted_at = data.get('lastSubmittedAt', '')
        num_submitted = int(data.get('numSubmitted', 0))
        translated_title = data.get('translatedTitle')
        topic_tags = data.get('topicTags', [])
        
        return SubmissionProgress(
            frontend_id=frontend_id,
            title=title,
            title_slug=title_slug,
            difficulty=difficulty,
            question_status=question_status,
            last_result=last_result,
            last_submitted_at=last_submitted_at,
            num_submitted=num_submitted,
            translated_title=translated_title,
            topic_tags=topic_tags
        )
    
    def __repr__(self):
        return f"SubmissionProgress(id={self.frontend_id}, title={self.title}, status={self.question_status}, result={self.last_result})"

