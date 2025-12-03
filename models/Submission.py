class Submission:
    def __init__(self, id: int, timestamp: int, lang: str):
        self.id = id
        self.timestamp = timestamp
        self.lang = lang

    @staticmethod
    def from_json(data: dict) -> 'Submission':
        """
        Creates a QuestionUrl instance from a JSON-like dictionary.
        """
        id = data.get('id', None)
        timestamp = data.get('timestamp', None)
        lang = data.get('lang', '')

        id = int(id) if id not in [None, ''] else 0
        timestamp = int(timestamp) if timestamp not in [None, ''] else 0

        return Submission(id, timestamp, lang)

    def __repr__(self):
        return f"Submission(id={self.id}, timestamp={self.timestamp}, lang={self.lang})"