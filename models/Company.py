from utils.Constants import Constants

class Company:
    def __init__(self, slug: str, name: str = None):
        self.slug = slug
        self.name = name if name else slug  # Use slug as name if name not provided
        self.url = f"{Constants.LEETCODE_URL}/company/{slug}/"

    @staticmethod
    def from_json(data: dict) -> 'Company':
        """
        Creates a Company instance from a JSON-like dictionary.
        """
        slug = data.get('slug', '')
        name = data.get('name', slug)  # Use slug as fallback if name not provided
        return Company(slug, name)

    def __repr__(self):
        return f"Company(slug={self.slug}, name={self.name})"