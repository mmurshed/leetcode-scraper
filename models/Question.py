from utils.Constants import Constants
from utils.Util import Util

class Question:
    def __init__(self, id: int, title_slug: str, title: str, frequency: float, difficulty: str):
        self.id = id
        self.slug = title_slug
        self.title = Util.sanitize_title(title)
        self.frequency = frequency
        self.difficulty = difficulty
        self.url = f"{Constants.LEETCODE_URL}/problems/{self.slug}/"

    @staticmethod
    def from_json(data: dict) -> 'Question':
        """
        Creates a QuestionUrl instance from a JSON-like dictionary.
        """
        id = data.get('frontendQuestionId', data.get('questionFrontendId', None))
        slug = data.get('titleSlug', '')
        title = data.get('title', '')
        frequency = data.get('frequency', None)
        
        id = int(id) if id not in [None, ''] else 0
        frequency = float(frequency) if frequency not in [None, ''] else 0.0
        difficulty = data.get('difficulty', '')

        return Question(id, slug, title, frequency, difficulty)

    def __repr__(self):
        return f"Question(id={self.id}, slug={self.slug}, title={self.title}, frequency={self.frequency}, difficulty={self.difficulty})"