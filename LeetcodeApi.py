import os
import json
from bs4 import BeautifulSoup
import requests

from diskcache import Cache
from logging import Logger

from LeetcodeConfig import LeetcodeConfig
from LeetcodeConstants import LeetcodeConstants

class LeetcodeApi:
    def __init__(
        self,
        config: LeetcodeConfig,
        logger: Logger,
        default_headers:str = None,
        leetcode_headers:str = None):
        
        self.config = config
        self.logger = logger
        self.default_headers = default_headers or LeetcodeConstants.DEFAULT_HEADERS
        self.leetcode_headers = leetcode_headers or LeetcodeConstants.LEETCODE_HEADERS
        
        self.session = requests.Session()
        self.cache = Cache(self.config.cache_directory)

    def cache_key(*args):
        # Convert all arguments to strings and join them with '-'
        return '-'.join(map(str, args))
    
    #region basic method
    def extract_by_selector(self, response_content, selector):
        """
        Navigate through the response_content using the keys and/or indices in the selector.
        The selector can contain both dictionary keys (strings) and list indices (integers).
        """
        data = response_content

        for key in selector:
            # Check if the current element is a dictionary and the key is a string
            if isinstance(data, dict) and isinstance(key, str):
                if key in data:
                    data = data[key]
                else:
                    raise KeyError(f"Key '{key}' not found in response_content")
            # Check if the current element is a list and the key is an integer (index)
            elif isinstance(data, list) and isinstance(key, int):
                try:
                    data = data[key]
                except IndexError:
                    raise IndexError(f"Index '{key}' out of range in response_content list")
            else:
                raise ValueError(f"Unexpected type for key: {key}. Expected str for dict or int for list.")

        return data


    def query(self, method="post", query=None, selector=None, url=None, headers=None):
        headers = headers or self.leetcode_headers
        url = url or LeetcodeConstants.LEETCODE_GRAPHQL_URL

        response = self.session.request(
            method=method,
            url=url,
            headers=headers,
            json=query
        )

        response.raise_for_status()

        content_type = response.headers.get('Content-Type', '').lower()
        is_json = 'application/json' in content_type

        if is_json:
            response_content = json.loads(response.content)
            data = response_content

            # Check if the selector is callable (a method) or a list of keys
            if callable(selector):
                # Apply the selector function to the response content
                data = selector(response_content)
            elif isinstance(selector, list):
                # Use the selector as a list of keys
                data = self.extract_by_selector(response_content, selector)
        else:
            data = response.text

        return data
    
    def cached_query(self, cache_key, method="post", query=None, selector=None, url=None, headers=None):
        """
        This function caches and performs a query if data is not already cached.
        Optionally uses a selector to filter out the required part of the response.
        """
        headers = headers or self.leetcode_headers
        url = url or LeetcodeConstants.LEETCODE_GRAPHQL_URL

        if not self.config.cache_api_calls:
            # make direct calls
            data = self.query(
                method=method,
                query=query,
                selector=selector,
                url=url,
                headers=headers)
            return data

        # Check if data exists in the cache and retrieve it
        data = self.cache.get(cache_key)

        if data is None:
            # If cache miss, make the request
            data = self.query(
                method=method,
                query=query,
                selector=selector,
                url=url,
                headers=headers)

            # Store data in the cache
            self.cache.set(cache_key, data)

        return data
    
    #endregion

    #region cards api

    def get_categories(self):
        cache_key = "allcards"

        query = {
            "operationName": "GetCategories",
            "variables": {
                "num": 1000
            },
            "query": "query GetCategories($categorySlug: String, $num: Int) {\n  categories(slug: $categorySlug) {\n  slug\n    cards(num: $num) {\n ...CardDetailFragment\n }\n  }\n  }\n\nfragment CardDetailFragment on CardNode {\n   slug\n  categorySlug\n  }\n"
        }
        selector = ['data', 'categories']

        data = self.cached_query(
            cache_key=cache_key,
            query=query,
            selector=selector)
        
        return data

    def get_card_details(self, card_slug):
        query = {
            "operationName": "GetExtendedCardDetail",
            "variables": {
                "cardSlug": card_slug
            },
            "query": "query GetExtendedCardDetail($cardSlug: String!) {\n  card(cardSlug: $cardSlug) {\n title\n  introduction\n}\n}\n"
        }

        selector = ['data', 'card']

        data = self.cached_query(
            cache_key=card_slug,
            query=query,
            selector=selector)
        
        return data

    def get_chapters_with_items(self, card_slug):
        cache_key = self.cache_key(card_slug, "detail")

        query = {
            "operationName": "GetChaptersWithItems",
            "variables": {
                "cardSlug": card_slug
            },
            "query": "query GetChaptersWithItems($cardSlug: String!) {\n  chapters(cardSlug: $cardSlug) {\n    ...ExtendedChapterDetail\n   }\n}\n\nfragment ExtendedChapterDetail on ChapterNode {\n  id\n  title\n  slug\n description\n items {\n    id\n    title\n  }\n }\n"
        }
        selector = ['data', 'chapters']

        data = self.cached_query(
            cache_key=cache_key,
            query=query,
            selector=selector)
        
        return data

    def get_chapter_items(self, card_slug, item_id):
        cache_key = self.cache_key(card_slug, item_id)

        query = {
            "operationName": "GetItem",
            "variables": {
                "itemId": item_id
            },
            "query": "query GetItem($itemId: String!) {\n  item(id: $itemId) {\n    id\n title\n  question {\n questionId\n frontendQuestionId: questionFrontendId\n   title\n  titleSlug\n }\n  article {\n id\n title\n }\n  htmlArticle {\n id\n  }\n  webPage {\n id\n  }\n  }\n }\n"
        }
        selector = ['data', 'item']

        data = self.cached_query(
            cache_key=cache_key,
            query=query,
            selector=selector)
        
        return data

    #endregion cards api

    #region questions api
    def get_questions_count(self):
        cache_key = "allquestioncount"

        query = {
            "query": "\n query getQuestionsCount {allQuestionsCount {\n    difficulty\n    count\n }} \n    "
        }
        selector = ['data', 'allQuestionsCount', 0,'count']

        data = self.cached_query(
            cache_key=cache_key,
            query=query,
            selector=selector)
        
        return data
    
    def get_all_questions(self, all_questions_count):
        cache_key = "allquestions"

        query = {
            "query": "\n query problemsetQuestionList($categorySlug: String, $limit: Int, $skip: Int, $filters: QuestionListFilterInput) {\n  problemsetQuestionList: questionList(\n    categorySlug: $categorySlug\n    limit: $limit\n    skip: $skip\n    filters: $filters\n  ) {\n  questions: data {\n title\n titleSlug\n frontendQuestionId: questionFrontendId\n }\n  }\n}\n    ",
            "variables": {
                "categorySlug": "",
                "skip": 0,
                "limit": all_questions_count,
                "filters": {}
            }
        }

        selector = ['data', 'problemsetQuestionList', 'questions']

        data = self.cached_query(
            cache_key=cache_key,
            query=query,
            selector=selector)
        
        return data

    def get_question(self, question_id, question_title_slug):
        cache_key = self.cache_key(question_id, "qdat")

        query = {
            "operationName": "GetQuestion",
            "variables": {
                "titleSlug": question_title_slug
            },
            "query": "query GetQuestion($titleSlug: String!) {\n  question(titleSlug: $titleSlug) {\n title\n submitUrl\n similarQuestions\n difficulty\n  companyTagStats\n codeDefinition\n    content\n    hints\n    solution {\n      content\n   }\n   }\n }\n"
        }

        selector = ['data', 'question']

        data = self.cached_query(
            cache_key=cache_key,
            query=query,
            selector=selector)
        return data
   
    #endregion questions api

    #region playground codes api

    def get_all_playground_codes(self, question_id, uuid):
        cache_key = self.cache_key(question_id, uuid)

        query = {
            "operationName": "allPlaygroundCodes",
            "query": f"""query allPlaygroundCodes {{\n allPlaygroundCodes(uuid: \"{uuid}\") {{\n    code\n    langSlug\n }}\n}}\n"""
        }
        selector = ['data', 'allPlaygroundCodes']

        data = self.cached_query(
            cache_key=cache_key,
            query=query,
            selector=selector)
        
        return data
    
    def get_slides_json(self, hash, slide_url):
        cache_key = hash
        selector = ['timeline']

        data = self.cached_query(
            cache_key=cache_key,
            method="get",
            selector=selector,
            url=slide_url,
            headers=self.default_headers)
        
        return data

    def get_slide_content(self, question_id, file_hash, filename_var1, filename_var2):
        cache_key = self.cache_key(question_id, file_hash)

        slide_url1 = f"https://assets.leetcode.com/static_assets/media/{filename_var1}.json"
        slide_url2 = f"https://assets.leetcode.com/static_assets/media/{filename_var2}.json"
        selector = ['timeline']
        
        try:
            self.logger.debug(f"Slide url1: {slide_url1}")
            data = self.cached_query(
                cache_key=cache_key,
                method="get",
                url=slide_url1,
                selector=selector,
                headers=self.default_headers)
        except:
            self.logger.error(f"Slide url1 failed: {slide_url1}")
            self.logger.debug(f"Slide url2: {slide_url2}")

            try:
                data = self.cached_query(
                    cache_key=cache_key,
                    method="get",
                    url=slide_url2,
                    selector=selector,
                    headers=self.default_headers)
            except:
                self.logger.error(f"Slide url2 failed: {slide_url2}")
                pass

        return data

    #endregion playground codes api
    
    #region articles api
    def get_article(self, question_id, article_id):
        cache_key = self.cache_key(question_id, article_id)

        query = {
            "operationName": "GetArticle",
            "variables": {
                "articleId": article_id
            },
            "query": "query GetArticle($articleId: String!) {\n  article(id: $articleId) {\n    id\n    title\n    body\n  }\n}\n"
        }
        selector = ['data', 'article', 'body']

        data = self.cached_query(
            cache_key=cache_key,
            query=query,
            selector=selector)
        
        return data

    def get_html_article(self, html_article_id):
        cache_key = self.cache_key(html_article_id, "data")

        query = {
            "operationName": "GetHtmlArticle",
            "variables": {
                "htmlArticleId": html_article_id
            },
            "query": "query GetHtmlArticle($htmlArticleId: String!) {\n  htmlArticle(id: $htmlArticleId) {\n    id\n    html\n      }\n}\n"
        }
        selector = ['data', 'htmlArticle', 'html']

        data = self.cached_query(
            cache_key=cache_key,
            query=query,
            selector=selector)
        
        return data

    #endregion articles api 

    #region submissions api
    def get_submission_list(self, question_id, question_title_slug):
        cache_key = self.cache_key(question_id, "subm")

        query = {
            "operationName": "submissionList",
            "variables": {
                "questionSlug": question_title_slug,
                "offset": 0,
                "limit": 20,
                "lastKey": None
            },
            "query": "\n    query submissionList($offset: Int!, $limit: Int!, $lastKey: String, $questionSlug: String!, $lang: Int, $status: Int) {\n  questionSubmissionList(\n    offset: $offset\n    limit: $limit\n    lastKey: $lastKey\n    questionSlug: $questionSlug\n    lang: $lang\n    status: $status\n  ) {\n    lastKey\n    hasNext\n    submissions {\n      id\n      title\n      titleSlug\n      status\n      statusDisplay\n      lang\n      langName\n      runtime\n      timestamp\n      url\n      isPending\n      memory\n      hasNotes\n      notes\n      flagType\n      topicTags {\n        id\n      }\n    }\n  }\n}\n    "
        }
        selector = ['data', 'questionSubmissionList', 'submissions']

        data = self.cached_query(
            cache_key=cache_key,
            query=query,
            selector=selector)
        
        return data

    def get_submission_details(self, question_id, submission_id):
        cache_key = self.cache_key(question_id, "detail")

        query = {
            "operationName": "submissionDetails",
            "variables": {
                "submissionId": submission_id
            },                
            "query":"\n    query submissionDetails($submissionId: Int!) {\n  submissionDetails(submissionId: $submissionId) {\n    runtime\n    runtimeDisplay\n    runtimePercentile\n    runtimeDistribution\n    memory\n    memoryDisplay\n    memoryPercentile\n    memoryDistribution\n    code\n    timestamp\n    statusCode\n    user {\n      username\n      profile {\n        realName\n        userAvatar\n      }\n    }\n    lang {\n      name\n      verboseName\n    }\n    question {\n      questionId\n      titleSlug\n      hasFrontendPreview\n    }\n    notes\n    flagType\n    topicTags {\n      tagId\n      slug\n      name\n    }\n    runtimeError\n    compileError\n    lastTestcase\n    totalCorrect\n    totalTestcases\n    fullCodeOutput\n    testDescriptions\n    testBodies\n    testInfo\n  }\n}\n    "
        }
        selector = ['data', 'submissionDetails']

        data = None
        try:
            data = self.cached_query(
                cache_key=cache_key,
                query=query,
                selector=selector)
        except:
            pass

        return data

    #endregion submissions api

    #region solutions api
    def get_official_solution(self, question_id, question_title_slug):
        cache_key = self.cache_key(question_id, "sol")

        query = {
            "operationName": "officialSolution",
            "variables": {
                "titleSlug": question_title_slug
            },
            "query": "\n    query officialSolution($titleSlug: String!) {\n  question(titleSlug: $titleSlug) {\n    solution {\n      id\n      title\n      content\n      contentTypeId\n      paidOnly\n      hasVideoSolution\n      paidOnlyVideo\n      canSeeDetail\n      rating {\n        count\n        average\n        userRating {\n          score\n        }\n      }\n      topic {\n        id\n        commentCount\n        topLevelCommentCount\n        viewCount\n        subscribed\n        solutionTags {\n          name\n          slug\n        }\n        post {\n          id\n          status\n          creationDate\n          author {\n            username\n            isActive\n            profile {\n              userAvatar\n              reputation\n            }\n          }\n        }\n      }\n    }\n  }\n}\n    "
        }
        selector = ['data', 'question', 'solution', 'content']

        data = self.cached_query(
            cache_key=cache_key,
            query=query,
            selector=selector)
        
        return data

    #endregion solutions api
    
    #region company api
    def get_question_company_tags(self):
        cache_key = "allcompanyquestions"

        query = {
            "operationName": "questionCompanyTags",
            "variables": {},
            "query": "query questionCompanyTags {\n  companyTags {\n    name\n    slug\n    questionCount\n  }\n}\n"
        }

        selector = ['data', 'companyTags']

        data = self.cached_query(
            cache_key=cache_key,
            query=query,
            selector=selector)
        
        return data

    def get_favorite_details_for_company(self, company_slug):
        cache_key = self.cache_key(company_slug, "favdetails")

        query = {
            "operationName": "favoriteDetailV2ForCompany",
            "variables": {
                "favoriteSlug": company_slug
            },
            "query": "query favoriteDetailV2ForCompany($favoriteSlug: String!) {\n  favoriteDetailV2(favoriteSlug: $favoriteSlug) {\n    questionNumber\n    collectCount\n    generatedFavoritesInfo {\n      defaultFavoriteSlug\n      categoriesToSlugs {\n        categoryName\n        favoriteSlug\n        displayName\n      }\n    }\n  }\n}\n    "
        }

        selector = ['data', 'favoriteDetailV2']

        data = self.cached_query(
            cache_key=cache_key,
            query=query,
            selector=selector)
        
        return data
    
    def get_favorite_question_list_for_company(self, favoriteSlug, total_questions):
        cache_key = favoriteSlug

        query = {
            "operationName": "favoriteQuestionList",
            "variables": {
                "favoriteSlug": favoriteSlug,
                "filter": {
                    "positionRoleTagSlug": "",
                    "skip": 0,
                    "limit": total_questions
                }
            },
            "query": "\n    query favoriteQuestionList($favoriteSlug: String!, $filter: FavoriteQuestionFilterInput) {\n  favoriteQuestionList(favoriteSlug: $favoriteSlug, filter: $filter) {\n    questions {\n      difficulty\n      id\n      paidOnly\n      questionFrontendId\n      status\n      title\n      titleSlug\n      translatedTitle\n      isInMyFavorites\n      frequency\n      topicTags {\n        name\n        nameTranslated\n        slug\n      }\n    }\n    totalLength\n    hasMore\n  }\n}\n    "
        }

        selector = ['data', 'favoriteQuestionList', 'questions']

        data = self.cached_query(
            cache_key=cache_key,
            query=query,
            selector=selector)
        return data
    

    def get_next_data_id(self):
        cache_key = "companynextdataid"

        def selector(data):
            next_data_soup = BeautifulSoup(data, "html.parser")
            next_data_tag = next_data_soup.find('script', {'id': '__NEXT_DATA__'})
            next_data_json = json.loads(next_data_tag.text)
            next_data_id = next_data_json['props']['buildId']
            return next_data_id

        data = self.cached_query(
            cache_key=cache_key,
            selector=selector,
            method="get",
            url=f"{LeetcodeConstants.LEETCODE_URL}/problemset/",
            headers=self.default_headers)

        return data

    #endregion company api