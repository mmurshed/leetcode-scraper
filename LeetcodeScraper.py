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


if __name__ == '__main__':
    import argparse
    import requests
    
    parser = argparse.ArgumentParser(description='Leetcode Scraper - GUI and Console Interface')
    parser.add_argument('--proxy', type=str,
                        help='Add rotating or static proxy username:password@ip:port',
                        required=False)
    parser.add_argument('--console', action='store_true',
                        help='Launch console interface instead of GUI (GUI is default)',
                        required=False)
    
    args = parser.parse_args()
    
    logger = Util.get_logger()
    if args.proxy:
        os.environ['http_proxy'] = "http://"+args.proxy
        os.environ['https_proxy'] = "http://"+args.proxy
        response = requests.get("https://httpbin.org/ip")
        logger.info("Proxy set", response.content)
    
    if args.console:
        # Launch console interface
        from LeetcodeScraperConsole import main as console_main
        console_main(logger)
    else:
        # Launch GUI interface (default)
        try:
            import tkinter as tk
            from LeetcodeScraperGUI import LeetcodeScraperGUI
            root = tk.Tk()
            app = LeetcodeScraperGUI(root)
            root.mainloop()
        except ImportError as e:
            print("Error: tkinter is not available.")
            print("Please install tkinter or use --console flag to use the console interface.")
            print(f"\nError details: {e}")
            print("\nTo use console mode, run: python LeetcodeScraper.py --console")

