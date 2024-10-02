import os
import argparse
import requests

from LeetcodeApi import LeetcodeApi
from LeetcodeCards import LeetcodeCards
from LeetcodeCompany import LeetcodeCompany
from LeetcodeConstants import LeetcodeConstants
from LeetcodeImage import LeetcodeImage
from LeetcodePdfConverter import LeetcodePdfConverter
from LeetcodeQuestion import LeetcodeQuestion
from LeetcodeSolution import LeetcodeSolution
from LeetcodeSubmission import LeetcodeSubmission
from LeetcodeUtility import LeetcodeUtility
from LeetcodeConfigLoader import LeetcodeConfigLoader


def init():
    config = LeetcodeConfigLoader.load_config()
    LeetcodeConstants.LEETCODE_HEADERS = LeetcodeConstants.create_headers(config.leetcode_cookie)
    leetapi = LeetcodeApi(
        config=config,
        logger=logger)
    imagehandler = LeetcodeImage(
        config=config,
        logger=logger)
    solution = LeetcodeSolution(
        config=config,
        logger=logger,
        leetapi=leetapi)
    submission = LeetcodeSubmission(
        config=config,
        logger=logger,
        leetapi=leetapi)

    question = LeetcodeQuestion(
        config=config,
        logger=logger,
        leetapi=leetapi,
        solutionhandler=solution,
        imagehandler=imagehandler,
        submissionhandler=submission)
    
    cards = LeetcodeCards(
        config=config,
        logger=logger,
        leetapi=leetapi,
        questionhandler=question,
        solutionhandler=solution,
        imagehandler=imagehandler
    )

    company = LeetcodeCompany(
        config=config,
        logger=logger,
        leetapi=leetapi,
        questionhandler=question)

    return config, cards, company, imagehandler, question, submission

if __name__ == '__main__':

    logger = LeetcodeUtility.get_logger()

    parser = argparse.ArgumentParser(description='Leetcode Scraper Options')
    parser.add_argument('--non-stop', type=bool,
                        help='True/False - Will run non stop, will retry if any error occurs',
                        required=False)
    parser.add_argument('--proxy', type=str,
                        help='Add rotating or static proxy username:password@ip:port',
                        required=False)
    
    LeetcodeUtility.clear()

    args = parser.parse_args()
    previous_choice = 0
    if args.proxy:
        os.environ['http_proxy'] = "http://"+args.proxy
        os.environ['https_proxy'] = "http://"+args.proxy
        response = requests.get("https://httpbin.org/ip")
        logger.info("Proxy set", response.content)

    while True:
        # logger.info("Proxy set", SESSION.get(
        #     "https://httpbin.org/ip").content)
        try:
            print("""Leetcode-Scraper v2.0-beta
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
                config, cards, company, imagehandler, questionhandler, submission = init()


            if choice == 1:
                LeetcodeConfigLoader.generate_config()

            elif choice == 2:
                card_slug = input("Enter card slug: ")
                cards.scrape_selected_card(card_slug)
            elif choice == 3:
                cards.scrape_card_url()

            elif choice == 4:
                question_id = input("Enter question id: ")
                questionhandler.scrape_question_url(int(question_id))
            elif choice == 5:
                questionhandler.scrape_question_url()

            elif choice == 6:
                company_slug = input("Enter company slug: ")
                company.scrape_selected_company_questions(company_slug)
            elif choice == 7:
                company.scrape_all_company_questions()

            elif choice == 8:
                question_id = input("Enter question id: ")
                submission.get_selected_submissions(questionhandler=questionhandler, question_id=question_id)
            elif choice == 9:
                submission.get_all_submissions(questionhandler=questionhandler)

            elif choice == 9:
                directory = input("Enter directory: ")

                if not os.path.exists(directory) or not os.path.isdir(directory):
                    logger.error("Diectory doesn't exists or not valid")

                converter = LeetcodePdfConverter(
                    config=config,
                    logger=logger,
                    images_dir=imagehandler.get_images_dir(directory))
                converter.convert_folder(directory)
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
