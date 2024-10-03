from utils.Constants import Constants

class Company:
    def __init__(self, slug: str):
        self.slug = slug
        self.url = f"{Constants.LEETCODE_URL}/company/{slug}/"

    @staticmethod
    def from_json(data: dict) -> 'Company':
        """
        Creates a Card instance from a JSON-like dictionary.
        """
        slug = data.get('slug', '')
        return Company(slug)

    def __repr__(self):
        return f"Company(slug={self.slug})"