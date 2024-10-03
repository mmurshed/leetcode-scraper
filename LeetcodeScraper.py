import os
import argparse
from diskcache import Cache
import requests

from downloaders.CardsDownloader import CardsDownloader
from downloaders.CompanyDownloader import CompanyDownloader
from downloaders.ImageDownloader import ImageDownloader

from downloaders.QuestionDownloader import QuestionDownloader
from downloaders.SolutionDownloader import SolutionDownloader
from downloaders.SubmissionDownloader import SubmissionDownloader

from utils.ApiManager import ApiManager
from utils.Config import Config
from utils.Constants import Constants
from utils.Util import Util
from utils.ConfigLoader import ConfigLoader
from utils.PdfConverter import PdfConverter

def init(logger):
    config = ConfigLoader.load_config()

    Constants.LEETCODE_HEADERS = Constants.create_headers(config.leetcode_cookie)
    cache = Cache(
        directory=config.cache_directory)

    leetapi = ApiManager(
        config=config,
        logger=logger,
        cache=cache)
    imagehandler = ImageDownloader(
        config=config,
        logger=logger)
    solution = SolutionDownloader(
        config=config,
        logger=logger,
        leetapi=leetapi)
    submission = SubmissionDownloader(
        config=config,
        logger=logger,
        leetapi=leetapi)

    question = QuestionDownloader(
        config=config,
        logger=logger,
        leetapi=leetapi,
        solutiondownloader=solution,
        imagedownloader=imagehandler,
        submissiondownloader=submission)
    
    cards = CardsDownloader(
        config=config,
        logger=logger,
        leetapi=leetapi,
        questiondownloader=question,
        solutiondownloader=solution,
        imagehdownloader=imagehandler
    )

    company = CompanyDownloader(
        config=config,
        logger=logger,
        leetapi=leetapi,
        questiondownloader=question)

    return config, cache, cards, company, imagehandler, question, submission

def main(logger):
    Util.clear()
    previous_choice = 0

    while True:
        try:
            print(
"""Leetcode-Scraper v2.0-beta
1: Setup config

2: Download a card by name
3: Download all cards
                  
4: Download a question by id
5: Download all questions
                  
6: Download a company by name
7: Download all company questions

8: Download submissions by question id
9: Download all your submissions

10: Convert all files from a directory to pdf
11: Clear cache
                  
Press any to quit
                """)
            if previous_choice != 0:
                print("Previous Choice: ", previous_choice)
            else:
                choice = input("Enter your choice: ")

            try:
                choice = int(choice)
            except Exception:
                break

            if choice > 1:
                try:
                    config, cache, cards, company, imagehandler, questionhandler, submission = init(logger)
                except Exception as e:
                    logger.error(f"Initilization error {e}")
                    continue

            if choice == 1:
                ConfigLoader.generate_config()

            elif choice == 2:
                card_slug = input("Enter card slug: ")
                cards.download_selected_card(card_slug)
            elif choice == 3:
                cards.download_all_cards()

            elif choice == 4:
                question_id = input("Enter question id: ")
                questionhandler.download_selected_question(int(question_id))
            elif choice == 5:
                questionhandler.download_all_questions()

            elif choice == 6:
                company_slug = input("Enter company slug: ")
                company.download_selected_company_questions(company_slug)
            elif choice == 7:
                company.download_all_company_questions()

            elif choice == 8:
                question_id = input("Enter question id: ")
                submission.get_selected_submissions(
                    questiondownloader=questionhandler,
                    question_id=int(question_id))
            elif choice == 9:
                submission.get_all_submissions(questiondownloader=questionhandler)

            elif choice == 10:
                directory = input("Enter directory: ")

                if not os.path.exists(directory) or not os.path.isdir(directory):
                    logger.error("Diectory doesn't exists or not valid")

                converter = PdfConverter(
                    config=config,
                    logger=logger,
                    images_dir=Config.get_images_dir(directory))
                converter.convert_folder(directory)
            elif choice == 11:
                cache.clear()
            else:
                break

            if previous_choice != 0:
                break
        except KeyboardInterrupt:
            if args.non_stop:
                print("Keyboard Interrupt, Exiting")
                break
        except Exception as e:
            print("""
            Error Occured, Possible Causes:
            1. Check your internet connection
            2. Leetcode Session Cookie might have expired 
            3. Check your config file
            4. Too many requests, try again after some time or use proxies
            5. Leetcode might have changed their api queries (Create an issue on github)
            """)
            lineNumber = e.__traceback__.tb_lineno
            raise Exception(f"Exception on line {lineNumber}: {e}")

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Leetcode Scraper Options')
    parser.add_argument('--non-stop', type=bool,
                        help='True/False - Will run non stop, will retry if any error occurs',
                        required=False)
    parser.add_argument('--proxy', type=str,
                        help='Add rotating or static proxy username:password@ip:port',
                        required=False)
    

    args = parser.parse_args()

    logger = Util.get_logger()
    if args.proxy:
        os.environ['http_proxy'] = "http://"+args.proxy
        os.environ['https_proxy'] = "http://"+args.proxy
        response = requests.get("https://httpbin.org/ip")
        logger.info("Proxy set", response.content)

    main(logger)
