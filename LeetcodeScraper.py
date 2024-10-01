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

2: Get all cards url
3: Scrape card url

4: Get all question url
5: Scrape question url
6: Scrape a single question with frontend id

7: Scrape all company questions indexes
8: Scrape all company questions

9: Scrape selected company questions indexes
10: Scrape selected company questions

11: Save all your submissions in files
12: Convert all questions to pdf
                  
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


            if choice == 1:
                LeetcodeConfigLoader.generate_config()
            elif choice == 2:
                cards.get_all_cards_url()
            elif choice == 3:
                cards.scrape_card_url()

            elif choice == 4:
                question.get_all_questions_url(force_download=True)
            elif choice == 5:
                question.scrape_question_url()
            elif choice == 6:
                question_id = input("Enter question frontend id: ")
                question.scrape_question_url(int(question_id))

            elif choice == 7 or choice == 8:
                company.scrape_all_company_questions(choice)
            elif choice == 9 or choice == 10:
                company.scrape_selected_company_questions(choice)

            elif choice == 11:
                submission.get_all_submissions(question=question)
            elif choice == 12:
                converter = LeetcodePdfConverter(
                    config=config,
                    logger=logger,
                    images_dir=imagehandler.get_images_dir())
                converter.convert_folder(question.get_questions_dir())
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
            if args.non_stop:
                print("Retrying")
                previous_choice = choice
                continue
            input("Press Enter to continue")
