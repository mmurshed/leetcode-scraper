import os
import argparse

import logging
from logging.handlers import RotatingFileHandler

from LeetcodeApi import LeetcodeApi
from LeetcodePdfConverter import LeetcodePdfConverter
from LeetcodeImage import LeetcodeImage
from LeetcodeUtility import LeetcodeUtility


if __name__ == '__main__':
    # Set up logging
    log_file = 'scrape_errors.log'
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("Leet")
    handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=2)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    global selected_config
    selected_config = "0"

    DEFAULT_CONFIG = load_default_config()
    CONFIG = load_config(DEFAULT_CONFIG)

    parser = argparse.ArgumentParser(description='Leetcode Scraper Options')
    parser.add_argument('--non-stop', type=bool,
                        help='True/False - Will run non stop, will retry if any error occurs',
                        required=False)
    parser.add_argument('--proxy', type=str,
                        help='Add rotating or static proxy username:password@ip:port',
                        required=False)
    clear()
    args = parser.parse_args()
    previous_choice = 0
    if args.proxy:
        os.environ['http_proxy'] = "http://"+args.proxy
        os.environ['https_proxy'] = "http://"+args.proxy
        response = REQ_SESSION.get("https://httpbin.org/ip")
        logger.info("Proxy set", response.content)

    while True:
        # logger.info("Proxy set", SESSION.get(
        #     "https://httpbin.org/ip").content)
        try:
            print("""Leetcode-Scraper v1.5-stable
1: Setup config
2: Select config[Default: 0]
3: Get all cards url
4: Get all question url
5: Scrape card url
6: Scrape question url
7: Scrape all company questions indexes
8: Scrape all company questions
9: Scrape selected company questions indexes
10: Scrape selected company questions
11: Convert images to base64 using os.walk
12: Save submissions in files
13: Scrape a single question with frontend id
                  
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

            if choice > 2:
                CONFIG = load_config()
                LEETCODE_HEADERS = create_headers(CONFIG.leetcode_cookie)
                LEETAPI = LeetcodeApi(CONFIG, logger, DEFAULT_HEADERS, LEETCODE_HEADERS)

            if choice == 1:
                generate_config()
            elif choice == 2:
                select_config()
            elif choice == 3:
                get_all_cards_url()
            elif choice == 4:
                get_all_questions_url(force_download=True)
            elif choice == 5:
                scrape_card_url()
            elif choice == 6:
                scrape_question_url()
            elif choice == 7 or choice == 8:
                scrape_all_company_questions(choice)
            elif choice == 9 or choice == 10:
                scrape_selected_company_questions(choice)
            elif choice == 11:
                manual_convert_images_to_base64()
            elif choice == 12:
                get_all_submissions()
            elif choice == 13:
                question_id = input("Enter question frontend id: ")
                scrape_question_url(int(question_id))
                pass
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
