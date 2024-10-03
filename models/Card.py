from utils.Constants import Constants


class Card:
    def __init__(self, category_slug: str, slug: str):
        self.category_slug = category_slug
        self.slug = slug
        self.url = f"{Constants.LEETCODE_URL}/explore/{self.category_slug}/card/{self.slug}/"

    @staticmethod
    def from_json(data: dict) -> 'Card':
        """
        Creates a Card instance from a JSON-like dictionary.
        """
        category_slug = data.get('categorySlug', '')
        slug = data.get('slug', '')
        return Card(category_slug, slug)

    def __repr__(self):
        return f"Card(category_slug={self.category_slug}, slug={self.slug})"