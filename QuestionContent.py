import json
import re
from typing import List, Optional

from Constants import Constants
from Util import Util

class QuestionContent:
    def __init__(self, title: str, content: str, difficulty: str, company_tag_stats: str, similar_questions: str, submit_url: str, default_code: str, solution: Optional[str], hints: List[str]):
        self.title = title
        self.content = content
        self.difficulty = difficulty
        self.company_tag_stats = company_tag_stats
        self.similar_questions = similar_questions
        self.submit_url = submit_url
        self.code_definition = default_code
        self.solution = solution
        self.hints = hints
        self.url = Constants.LEETCODE_URL + self.submit_url[:-7]

    @staticmethod
    def from_json(data: dict) -> 'QuestionContent':
        title = data.get('title', '')
        title = Util.sanitize_title(title)
        content = data.get('content', '')
        difficulty = data.get('difficulty', '')
        company_tag_stats = data.get('companyTagStats', '')
        similar_questions = data.get('similarQuestions', '')
        submit_url = data.get('submitUrl', '')
        default_code = json.loads(data.get('codeDefinition', '[]'))[0]['defaultCode'] if data.get('codeDefinition') else ''
        
        solution = None
        if data.get('solution') and data['solution'].get('content'):
            solution = re.sub(r'\[TOC\]', '', data['solution']['content'])
        
        hints = data.get('hints', [])

        if company_tag_stats:
            company_tag_stats = json.loads(company_tag_stats)
        if similar_questions:
            similar_questions = json.loads(similar_questions)
        
        return QuestionContent(
            title=title,
            content=content,
            difficulty=difficulty,
            company_tag_stats=company_tag_stats,
            similar_questions=similar_questions,
            submit_url=submit_url,
            default_code=default_code,
            solution=solution,
            hints=hints
        )

    def __repr__(self):
        return f"Question(title={self.title}, difficulty={self.difficulty})"