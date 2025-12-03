from logging import Logger
import os
import argparse
from diskcache import Cache
import requests

from ai.OllamaSolution import OllamaSolution
from ai.OpenAISolution import OpenAISolution
from downloaders.CardsDownloader import CardsDownloader
from downloaders.CompanyDownloader import CompanyDownloader
from downloaders.ImageDownloader import ImageDownloader

from downloaders.QuestionDownloader import QuestionDownloader
from downloaders.SolutionDownloader import SolutionDownloader
from downloaders.SubmissionDownloader import SubmissionDownloader

from api.CachedRequest import CachedRequest
from api.ApiManager import ApiManager

from utils.Config import Config
from utils.Constants import Constants
from utils.Util import Util
from utils.ConfigLoader import ConfigLoader
from utils.PdfConverter import PdfConverter

def init(logger: Logger):
    config = ConfigLoader.load_config()

    if config.logging_level:
        logger.setLevel(str.upper(config.logging_level))

    Constants.LEETCODE_HEADERS = Constants.create_headers(config.leetcode_cookie)
    cache = Cache(
        directory=config.cache_directory)
    
    cached_req = CachedRequest(
        config=config,
        logger=logger,
        cache=cache)

    leetapi = ApiManager(
        config=config,
        logger=logger,
        requesth=cached_req)
    
    ai_solution_generator = None
    if config.ai_solution_generator:
        ai_solution_generator_method = str.lower(config.ai_solution_generator)
        if "ollama" == ai_solution_generator_method:
            logger.info(f"Ollama AI Solution Generator Initiated")
            ai_solution_generator = OllamaSolution(
                config=config,
                logger=logger,
                cache=cache)
        elif "openai" == ai_solution_generator_method:
            logger.info(f"Open AI Solution Generator Initiated")
            ai_solution_generator = OpenAISolution(
                config=config,
                logger=logger,
                leetapi=leetapi,
                cache=cache)
        else:
            logger.error(f"Invalid AI solution generator method specified: {ai_solution_generator_method}")

    imgd = ImageDownloader(
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
        imagedownloader=imgd,
        submissiondownloader=submission,
        ai_solution_generator=ai_solution_generator)
    
    cards = CardsDownloader(
        config=config,
        logger=logger,
        leetapi=leetapi,
        questiondownloader=question,
        solutiondownloader=solution,
        imagehdownloader=imgd
    )

    company = CompanyDownloader(
        config=config,
        logger=logger,
        leetapi=leetapi,
        questiondownloader=question)


    return config, cache, cards, company, question, submission

def main(logger: Logger):
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
                  
6: Download all questions for a company
7: Download all favorite questions for a company
8: Download all company questions

9: Download submissions by question id
10: Download all your submissions

11: Convert all files from a directory or a single file to pdf

12: Get cache by key
13: Delete cache by key
14: Clear cache
                  
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
                    config, cache, cards, company, qued, submission = init(logger)
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
                qued.download_selected_question(int(question_id))
            elif choice == 5:
                qued.download_all_questions()

            elif choice == 6:
                company_slug = input("Enter company slug: ")
                company.download_selected_company_questions(company_slug)
            elif choice == 7:
                company_slug = input("Enter company slug: ")
                favorite_details = company.get_company_favorite_slugs(company_slug)
                prompt = "Company favorite slugs\n"
                for idx, favorite_detail in enumerate(favorite_details, start=1):
                    comp_fav_slug, name = favorite_detail
                    prompt += f"{idx}. {name}\n"

                print(prompt)

                fav_slug = input("Enter favorite company slug: ")
                fav_slug = int(fav_slug) - 1
                comp_fav_slug, name = favorite_details[fav_slug]
                company.download_favorite_company_questions(company_slug, comp_fav_slug)

            elif choice == 8:
                company.download_all_company_questions()

            elif choice == 9:
                question_id = input("Enter question id: ")
                submission.get_selected_submissions(
                    question_id=int(question_id))
            elif choice == 10:
                submission.get_all_submissions()

            elif choice == 11:
                path = input("Enter directory or file path: ")

                if not os.path.exists(path):
                    logger.error("Diectory or file doesn't exists.")
                else:
                    converter = PdfConverter(
                        config=config,
                        logger=logger,
                        images_dir=Config.get_images_dir(path))
                    if os.path.isdir(path):
                        converter.convert_folder(path)
                    else:
                        converter.convert_single_file(path)
            elif choice == 12:
                key = input("Enter key: ")
                print(cache.get(key))
            elif choice == 13:
                key = input("Enter key: ")
                cache.delete(key=key)
            elif choice == 14:
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
