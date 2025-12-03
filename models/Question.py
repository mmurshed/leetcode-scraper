from utils.Constants import Constants
from utils.Util import Util

class Question:
    def __init__(self, id: int, title_slug: str, title: str, frequency: float, difficulty: str, solved: bool):
        self.id = id
        self.slug = title_slug
        self.title = Util.sanitize_title(title)
        self.frequency = frequency
        self.difficulty = difficulty
        self.solved = solved
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
        solved = data.get('status', '')
        
        id = int(id) if id not in [None, ''] else 0
        frequency = float(frequency) if frequency not in [None, ''] else 0.0
        difficulty = data.get('difficulty', '')
        solved = True if str.upper(solved) == 'SOLVED' else False

        return Question(id, slug, title, frequency, difficulty, solved)

    def __repr__(self):
        return f"Question(id={self.id}, slug={self.slug}, title={self.title}, frequency={self.frequency}, difficulty={self.difficulty}, solved={self.solved})"