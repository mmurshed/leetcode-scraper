from utils.Constants import Constants

class Company:
    def __init__(self, slug: str, name: str = None, question_count: int = 0):
        self.slug = slug
        self.name = name if name else slug  # Use slug as name if name not provided
        self.url = f"{Constants.LEETCODE_URL}/company/{slug}/"
        self.question_count = question_count

    @staticmethod
    def from_json(data: dict) -> 'Company':
        """
        Creates a Company instance from a JSON-like dictionary.
        """
        slug = data.get('slug', '')
        name = data.get('name', slug)  # Use slug as fallback if name not provided
        question_count = data.get('questionCount', 0)
        return Company(slug, name, question_count)

    def __repr__(self):
        return f"Company(slug={self.slug}, name={self.name}, question_count={self.question_count})"