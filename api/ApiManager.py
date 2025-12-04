import json
from typing import List
from bs4 import BeautifulSoup

from logging import Logger

from models.Question import Question
from utils.Config import Config
from utils.Constants import Constants

class ApiManager:
    def __init__(
        self,
        config: Config,
        logger: Logger,
        requesth):
        
        self.config = config
        self.logger = logger
        self.reqh = requesth


    #region cards api

    def get_categories(self):
        key = self.reqh.key("card", "categories")

        request = {
            "operationName": "GetCategories",
            "variables": {
                "num": 1000
            },
            "query": "query GetCategories($categorySlug: String, $num: Int) {\n  categories(slug: $categorySlug) {\n  slug\n    cards(num: $num) {\n ...CardDetailFragment\n }\n  }\n  }\n\nfragment CardDetailFragment on CardNode {\n   slug\n  categorySlug\n  }\n"
        }
        selector = ['data', 'categories']

        data = self.reqh.request(
            key=key,
            request=request,
            selector=selector)
        
        return data

    def get_card_details(self, card_slug):
        key = self.reqh.key("card", "detail", card_slug)

        request = {
            "operationName": "GetExtendedCardDetail",
            "variables": {
                "cardSlug": card_slug
            },
            "query": "query GetExtendedCardDetail($cardSlug: String!) {\n  card(cardSlug: $cardSlug) {\n title\n  introduction\n}\n}\n"
        }

        selector = ['data', 'card']

        data = self.reqh.request(
            key=key,
            request=request,
            selector=selector)
        
        return data

    def get_chapters_with_items(self, card_slug):
        key = self.reqh.key("card", card_slug, "chapters")

        request = {
            "operationName": "GetChaptersWithItems",
            "variables": {
                "cardSlug": card_slug
            },
            "query": "query GetChaptersWithItems($cardSlug: String!) {\n  chapters(cardSlug: $cardSlug) {\n    ...ExtendedChapterDetail\n   }\n}\n\nfragment ExtendedChapterDetail on ChapterNode {\n  id\n  title\n  slug\n description\n items {\n    id\n    title\n  }\n }\n"
        }
        selector = ['data', 'chapters']

        data = self.reqh.request(
            key=key,
            request=request,
            selector=selector)
        
        return data

    def get_chapter_items(self, card_slug, item_id):
        key = self.reqh.key("card", card_slug, "item", item_id)

        request = {
            "operationName": "GetItem",
            "variables": {
                "itemId": item_id
            },
            "query": "query GetItem($itemId: String!) {\n  item(id: $itemId) {\n    id\n title\n  question {\n questionId\n frontendQuestionId: questionFrontendId\n   title\n  titleSlug\n }\n  article {\n id\n title\n }\n  htmlArticle {\n id\n  }\n  webPage {\n id\n  }\n  }\n }\n"
        }
        selector = ['data', 'item']

        data = self.reqh.request(
            key=key,
            request=request,
            selector=selector)
        
        return data

    #endregion cards api

    #region questions api
    def get_questions_count(self):
        key = self.reqh.key("question", "count")

        request = {
            "query": "\n query getQuestionsCount {allQuestionsCount {\n    difficulty\n    count\n }} \n    "
        }
        selector = ['data', 'allQuestionsCount', 0,'count']

        data = self.reqh.request(
            key=key,
            request=request,
            selector=selector)
        
        return data
    
    def get_all_questions(self) -> List[Question]:
        count = self.get_questions_count()
        count = int(count)

        questions_data = self.get_limited_questions(count)

        data = [Question.from_json(question_data) for question_data in questions_data]
 
        return data

    def get_limited_questions(self, limit, skip = 0):
        key = self.reqh.key("question", "list")

        request = {
            "query": "\n query problemsetQuestionList($categorySlug: String, $limit: Int, $skip: Int, $filters: QuestionListFilterInput) {\n  problemsetQuestionList: questionList(\n    categorySlug: $categorySlug\n    limit: $limit\n    skip: $skip\n    filters: $filters\n  ) {\n  questions: data {\n title\n titleSlug\n frontendQuestionId: questionFrontendId\n }\n  }\n}\n    ",
            "variables": {
                "categorySlug": "",
                "skip": skip,
                "limit": limit,
                "filters": {}
            }
        }

        selector = ['data', 'problemsetQuestionList', 'questions']

        data = self.reqh.request(
            key=key,
            request=request,
            selector=selector)
        
        return data

    def get_question(self, question_id, question_title_slug):
        key = self.reqh.key("question", question_id)

        request = {
            "operationName": "GetQuestion",
            "variables": {
                "titleSlug": question_title_slug
            },
            "query": "query GetQuestion($titleSlug: String!) {\n  question(titleSlug: $titleSlug) {\n title\n submitUrl\n similarQuestions\n difficulty\n  companyTagStats\n codeDefinition\n    content\n    hints\n    solution {\n      content\n   }\n   }\n }\n"
        }

        selector = ['data', 'question']

        data = self.reqh.request(
            key=key,
            request=request,
            selector=selector)
        return data
   
    #endregion questions api

    #region playground codes api

    def get_all_playground_codes(self, question_id, uuid):
        key = self.reqh.key("question", question_id, "uuid", uuid)

        request = {
            "operationName": "allPlaygroundCodes",
            "query": f"""query allPlaygroundCodes {{\n allPlaygroundCodes(uuid: \"{uuid}\") {{\n    code\n    langSlug\n }}\n}}\n"""
        }
        selector = ['data', 'allPlaygroundCodes']

        data = self.reqh.request(
            key=key,
            request=request,
            selector=selector)
        
        return data
    
    def get_slides_json(self, hash, slide_url):
        key = self.reqh.key("slide", hash)
        selector = ['timeline']

        data = self.reqh.request(
            key=key,
            method="get",
            selector=selector,
            url=slide_url,
            headers=Constants.DEFAULT_HEADERS)
        
        return data

    def get_slide_content(self, question_id, file_hash, filename_var1, filename_var2):
        key = self.reqh.key("question", question_id, "slide", file_hash)

        slide_url1 = f"https://assets.leetcode.com/static_assets/media/{filename_var1}.json"
        slide_url2 = f"https://assets.leetcode.com/static_assets/media/{filename_var2}.json"
        selector = ['timeline']

        data = None
        
        try:
            self.logger.debug(f"Slide url1: {slide_url1}")
            data = self.reqh.request(
                key=key,
                method="get",
                url=slide_url1,
                selector=selector,
                headers=Constants.DEFAULT_HEADERS)
        except:
            self.logger.error(f"Slide url1 failed: {slide_url1}")
            self.logger.debug(f"Slide url2: {slide_url2}")

            try:
                data = self.reqh.request(
                    key=key,
                    method="get",
                    url=slide_url2,
                    selector=selector,
                    headers=Constants.DEFAULT_HEADERS)
            except:
                self.logger.error(f"Slide url2 failed: {slide_url2}")
                pass

        return data

    #endregion playground codes api
    
    #region articles api
    def get_article(self, item_id, article_id):
        key = self.reqh.key("item", item_id, "article", article_id)

        request = {
            "operationName": "GetArticle",
            "variables": {
                "articleId": article_id
            },
            "query": "query GetArticle($articleId: String!) {\n  article(id: $articleId) {\n    id\n    title\n    body\n  }\n}\n"
        }
        selector = ['data', 'article', 'body']

        data = self.reqh.request(
            key=key,
            request=request,
            selector=selector)
        
        return data

    def get_html_article(self, item_id, html_article_id):
        key = self.reqh.key("item", item_id, "html", "article", html_article_id)

        request = {
            "operationName": "GetHtmlArticle",
            "variables": {
                "htmlArticleId": html_article_id
            },
            "query": "query GetHtmlArticle($htmlArticleId: String!) {\n  htmlArticle(id: $htmlArticleId) {\n    id\n    html\n      }\n}\n"
        }
        selector = ['data', 'htmlArticle', 'html']

        data = self.reqh.request(
            key=key,
            request=request,
            selector=selector)
        
        return data

    #endregion articles api 

    #region submissions api
    def get_submission_list(self, question_id, question_slug):
        key = self.reqh.key("question", question_id, "submissions")

        request = {
            "operationName": "submissionList",
            "variables": {
                "questionSlug": question_slug,
                "offset": 0,
                "limit": 20,
                "lastKey": None
            },
            "query": "\n    query submissionList($offset: Int!, $limit: Int!, $lastKey: String, $questionSlug: String!, $lang: Int, $status: Int) {\n  questionSubmissionList(\n    offset: $offset\n    limit: $limit\n    lastKey: $lastKey\n    questionSlug: $questionSlug\n    lang: $lang\n    status: $status\n  ) {\n    lastKey\n    hasNext\n    submissions {\n      id\n      title\n      titleSlug\n      status\n      statusDisplay\n      lang\n      langName\n      runtime\n      timestamp\n      url\n      isPending\n      memory\n      hasNotes\n      notes\n      flagType\n      topicTags {\n        id\n      }\n    }\n  }\n}\n    "
        }
        selector = ['data', 'questionSubmissionList', 'submissions']

        data = self.reqh.request(
            key=key,
            request=request,
            selector=selector)
        
        return data

    def get_submission_details(self, question_id, submission_id):
        key = self.reqh.key("question", question_id, "submission", submission_id)

        request = {
            "operationName": "submissionDetails",
            "variables": {
                "submissionId": submission_id
            },                
            "query":"\n    query submissionDetails($submissionId: Int!) {\n  submissionDetails(submissionId: $submissionId) {\n    runtime\n    runtimeDisplay\n    runtimePercentile\n    runtimeDistribution\n    memory\n    memoryDisplay\n    memoryPercentile\n    memoryDistribution\n    code\n    timestamp\n    statusCode\n    user {\n      username\n      profile {\n        realName\n        userAvatar\n      }\n    }\n    lang {\n      name\n      verboseName\n    }\n    question {\n      questionId\n      titleSlug\n      hasFrontendPreview\n    }\n    notes\n    flagType\n    topicTags {\n      tagId\n      slug\n      name\n    }\n    runtimeError\n    compileError\n    lastTestcase\n    totalCorrect\n    totalTestcases\n    fullCodeOutput\n    testDescriptions\n    testBodies\n    testInfo\n  }\n}\n    "
        }
        selector = ['data', 'submissionDetails']

        data = None
        try:
            data = self.reqh.request(
                key=key,
                request=request,
                selector=selector)
        except:
            pass

        return data

    #endregion submissions api

    #region user progress api
    def get_user_submission_progress(self, limit=50, skip=0):
        """Get user's submission progress (questions with submissions)."""
        key = self.reqh.key("user", "progress", "submissions", str(skip), str(limit))

        request = {
            "operationName": "userProgressQuestionList",
            "variables": {
                "filters": {
                    "skip": skip,
                    "limit": limit
                }
            },
            "query": "\n    query userProgressQuestionList($filters: UserProgressQuestionListInput) {\n  userProgressQuestionList(filters: $filters) {\n    totalNum\n    questions {\n      translatedTitle\n      frontendId\n      title\n      titleSlug\n      difficulty\n      lastSubmittedAt\n      numSubmitted\n      questionStatus\n      lastResult\n      topicTags {\n        name\n        nameTranslated\n        slug\n      }\n    }\n  }\n}\n    "
        }
        selector = ['data', 'userProgressQuestionList']

        data = self.reqh.request(
            key=key,
            request=request,
            selector=selector)
        
        return data

    def get_all_submissions(self):
        """Get all questions that the user has submitted solutions for.
        
        Returns a list of all questions with submission details including:
        - frontendId, title, titleSlug
        - difficulty, questionStatus, lastResult
        - lastSubmittedAt, numSubmitted
        - topicTags
        """
        self.logger.debug("Fetching all user submissions...")
        
        # Get first batch to determine total count
        first_batch = self.get_user_submission_progress(limit=50, skip=0)
        
        if not first_batch or 'totalNum' not in first_batch:
            self.logger.warning("Could not retrieve user submissions")
            return []
        
        total_num = first_batch['totalNum']
        all_questions = first_batch.get('questions', [])
        
        self.logger.debug(f"Total questions with submissions: {total_num}")
        
        # Fetch remaining batches if needed
        if total_num > 50:
            skip = 50
            while skip < total_num:
                self.logger.debug(f"Fetching submissions {skip} to {skip + 50}...")
                batch = self.get_user_submission_progress(limit=50, skip=skip)
                
                if batch and 'questions' in batch:
                    all_questions.extend(batch['questions'])
                
                skip += 50
        
        self.logger.debug(f"Retrieved {len(all_questions)} questions with submissions")
        return all_questions

    #endregion user progress api

    #region solutions api
    def get_official_solution(self, question_id, question_slug):
        key = self.reqh.key("question", question_id, "solution")

        request = {
            "operationName": "officialSolution",
            "variables": {
                "titleSlug": question_slug
            },
            "query": "\n    query officialSolution($titleSlug: String!) {\n  question(titleSlug: $titleSlug) {\n    solution {\n      id\n      title\n      content\n      contentTypeId\n      paidOnly\n      hasVideoSolution\n      paidOnlyVideo\n      canSeeDetail\n      rating {\n        count\n        average\n        userRating {\n          score\n        }\n      }\n      topic {\n        id\n        commentCount\n        topLevelCommentCount\n        viewCount\n        subscribed\n        solutionTags {\n          name\n          slug\n        }\n        post {\n          id\n          status\n          creationDate\n          author {\n            username\n            isActive\n            profile {\n              userAvatar\n              reputation\n            }\n          }\n        }\n      }\n    }\n  }\n}\n    "
        }
        selector = ['data', 'question', 'solution', 'content']

        data = self.reqh.request(
            key=key,
            request=request,
            selector=selector)
        
        return data

    #endregion solutions api
    
    #region company api
    def get_question_company_tags(self):
        key = self.reqh.key("company", "tags")

        request = {
            "operationName": "questionCompanyTags",
            "variables": {},
            "query": "query questionCompanyTags {\n  companyTags {\n    name\n    slug\n    questionCount\n  }\n}\n"
        }

        selector = ['data', 'companyTags']

        data = self.reqh.request(
            key=key,
            request=request,
            selector=selector)
        
        return data

    def get_favorite_details_for_company(self, company_slug):
        key = self.reqh.key("company", company_slug, "favorite")

        request = {
            "operationName": "favoriteDetailV2ForCompany",
            "variables": {
                "favoriteSlug": company_slug
            },
            "query": "query favoriteDetailV2ForCompany($favoriteSlug: String!) {\n  favoriteDetailV2(favoriteSlug: $favoriteSlug) {\n    questionNumber\n    collectCount\n    generatedFavoritesInfo {\n      defaultFavoriteSlug\n      categoriesToSlugs {\n        categoryName\n        favoriteSlug\n        displayName\n      }\n    }\n  }\n}\n    "
        }

        selector = ['data', 'favoriteDetailV2']

        data = self.reqh.request(
            key=key,
            request=request,
            selector=selector)
        
        return data
    
    def get_favorite_question_list_for_company(self, favorite_slug, total_questions, skip=0):
        key = self.reqh.key("company", "favorite", favorite_slug)

        request = {
            "operationName": "favoriteQuestionList",
            "variables": {
                "favoriteSlug": favorite_slug,
                "filter": {
                    "positionRoleTagSlug": "",
                    "skip": skip,
                    "limit": total_questions
                }
            },
            "query": "\n    query favoriteQuestionList($favoriteSlug: String!, $filter: FavoriteQuestionFilterInput) {\n  favoriteQuestionList(favoriteSlug: $favoriteSlug, filter: $filter) {\n    questions {\n      difficulty\n      id\n      paidOnly\n      questionFrontendId\n      status\n      title\n      titleSlug\n      translatedTitle\n      isInMyFavorites\n      frequency\n      topicTags {\n        name\n        nameTranslated\n        slug\n      }\n    }\n    totalLength\n    hasMore\n  }\n}\n    "
        }

        selector = ['data', 'favoriteQuestionList', 'questions']

        data = self.reqh.request(
            key=key,
            request=request,
            selector=selector)
        return data
    

    def get_next_data_id(self):
        key = self.reqh.key("company", "nextdataid")

        def selector(data):
            next_data_soup = BeautifulSoup(data, "html.parser")
            next_data_tag = next_data_soup.find('script', {'id': '__NEXT_DATA__'})
            next_data_json = json.loads(next_data_tag.text)
            next_data_id = next_data_json['props']['buildId']
            return next_data_id

        data = self.reqh.request(
            key=key,
            selector=selector,
            method="get",
            url=f"{Constants.LEETCODE_URL}/problemset/",
            headers=Constants.DEFAULT_HEADERS)

        return data

    #endregion company api

    #region community solution

    # order_by values "most_votes", "hot", "newest_to_oldest"
    def get_all_community_solutions(self, questionSlug, limit = 15, skip = 0, order_by = "most_votes"):
        key = self.reqh.key("community", "solutions", questionSlug)

        request = {
            "operationName": "communitySolutions",
            "variables": {
                "query": "",
                "languageTags": [],
                "topicTags": [],
                "questionSlug": questionSlug,
                "skip": skip,
                "first": limit,
                "orderBy": order_by
            },
            "query": "\n    query communitySolutions($questionSlug: String!, $skip: Int!, $first: Int!, $query: String, $orderBy: TopicSortingOption, $languageTags: [String!], $topicTags: [String!]) {\n  questionSolutions(\n    filters: {questionSlug: $questionSlug, skip: $skip, first: $first, query: $query, orderBy: $orderBy, languageTags: $languageTags, topicTags: $topicTags}\n  ) {\n    hasDirectResults\n    totalNum\n    solutions {\n      id\n      title\n      commentCount\n      topLevelCommentCount\n      viewCount\n      pinned\n      isFavorite\n      solutionTags {\n        name\n        slug\n      }\n      post {\n        id\n        status\n        voteStatus\n        voteCount\n        creationDate\n        isHidden\n        author {\n          username\n          isActive\n          nameColor\n          activeBadge {\n            displayName\n            icon\n          }\n          profile {\n            userAvatar\n            reputation\n          }\n        }\n      }\n      searchMeta {\n        content\n        contentType\n        commentAuthor {\n          username\n        }\n        replyAuthor {\n          username\n        }\n        highlights\n      }\n    }\n  }\n}\n    ",
        }

        selector = ['data', 'questionSolutions', 'solutions']

        data = self.reqh.request(
            key=key,
            request=request,
            selector=selector)
        return data


    def get_community_solution_content(self, topic_id):
        key = self.reqh.key("community", "solution", topic_id)

        request = {
            "operationName": "communitySolution",
            "variables": {
                "topicId": topic_id
            },
            "query": "\n    query communitySolution($topicId: Int!) {\n  topic(id: $topicId) {\n    id\n    viewCount\n    topLevelCommentCount\n    subscribed\n    title\n    pinned\n    solutionTags {\n      name\n      slug\n    }\n    hideFromTrending\n    commentCount\n    isFavorite\n    post {\n      id\n      voteCount\n      voteStatus\n      content\n      updationDate\n      creationDate\n      status\n      isHidden\n      author {\n        isDiscussAdmin\n        isDiscussStaff\n        username\n        nameColor\n        activeBadge {\n          displayName\n          icon\n        }\n        profile {\n          userAvatar\n          reputation\n        }\n        isActive\n      }\n      authorIsModerator\n      isOwnPost\n    }\n  }\n}\n    "
        }

        selector = ['data', 'topic', 'post', 'content']

        data = self.reqh.request(
            key=key,
            request=request,
            selector=selector)
        return data

    #endregion community solution
