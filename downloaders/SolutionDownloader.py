import hashlib
import os
import re
from bs4 import BeautifulSoup
import yt_dlp

from logging import Logger

from utils.Constants import Constants
from utils.Util import Util
from utils.Config import Config
from utils.ApiManager import ApiManager

class SolutionDownloader:
    def __init__(
        self,
        config: Config,
        logger: Logger,
        leetapi: ApiManager):
        
        self.config = config
        self.logger = logger
        self.lc = leetapi

    def get_playground_content(self, iframe, question_id, src_url):
        uuid = src_url.split('/')[-2]
        self.logger.debug(f"Playground uuid: {uuid} url: {src_url}")
        
        playground_content = self.lc.get_all_playground_codes(question_id, uuid)

        if not playground_content:
            self.logger.error(f"Error in getting code data from source url {src_url}")
            return

        code_html = f"""<div>"""
        
        lang_to_include = "all"
        languages = set(item.get("langSlug") for item in playground_content)

        if "all" in self.config.preferred_language_order:
            lang_to_include == "all"
        else:
            for preferred_language in self.config.preferred_language_order:
                if preferred_language in languages:
                    lang_to_include = preferred_language
                    break

        for code_idx in range(len(playground_content)):
            lang = playground_content[code_idx]['langSlug']
            if lang_to_include == "all" or lang_to_include == lang:
                code_html += f"""<div style="font-weight: bold;">{lang}</div>"""
                code_html += f"""<div><code style="color:black"><pre>{playground_content[code_idx]['code']}</pre></code></div>"""

        code_html += f"""</div>"""
        iframe.replace_with(BeautifulSoup(f""" {code_html} """, 'html.parser'))

    def get_video_content(self, iframe, question_id, src_url, root_dir):
        videos_dir = os.path.join(root_dir, "videos")
        if self.config.download_videos:
            os.makedirs(videos_dir, exist_ok=True)

        width = iframe.get('width') or 640
        height = iframe.get('height') or 360

        video_id = src_url.split("/")[-1]
        video_extension = "mp4"
        video_basename = f"{Util.qbasename(question_id, video_id)}.{video_extension}"

        if self.config.download_videos:
            ydl_opts = {
                'outtmpl': f'{videos_dir}/{Util.qstr(question_id)}-%(id)s.%(ext)s',
                'format': 'bestvideo[height<=720]+bestaudio/best[height<=720]',
                'http_headers': {
                    'Referer': Constants.LEETCODE_URL,
                }
            }

            # Download the video using yt-dlp
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(src_url, download=self.config.download_videos)
                video_extension = info_dict.get('ext')
                video_filename = ydl.prepare_filename(info_dict)
                video_basename = os.path.basename(video_filename)

        if video_basename:
            video_html = f"""
                <video width="{width}" height="{height}" controls>
                    <source src="videos/{video_basename}" type="video/{video_extension}">
                </video>
            """
            iframe.replace_with(BeautifulSoup(video_html, 'html.parser'))


    def replace_iframes_with_content(self, content, question_id, root_dir):
        self.logger.debug("Replacing iframe with code")

        content_soup = BeautifulSoup(content, 'html.parser')
        iframes = content_soup.find_all('iframe')

        for iframe in iframes:
            src_url = iframe['src']
            src_url_lcase = str.lower(src_url)

            if "playground" in src_url_lcase:
                self.get_playground_content(iframe, question_id, src_url)
            elif "vimeo" in src_url_lcase:
                self.get_video_content(iframe, question_id, src_url, root_dir)

        return str(content_soup)

 
    def slide_match(self, slide_name, question_id, slide_idx):
        json_split = slide_name.strip().split(".json")
        base_name = json_split[-2]
        
        json_split = base_name.split("/")
        drop_dots = json_split[1:]
        
        documents = drop_dots[0] # Documents

        rest_after_documents = drop_dots[1:] # 01_LIS.json
        filename = "/".join(rest_after_documents)

        filename_var1 = f"{str.lower(documents)}/{filename}" # variation 1: only documents/ lower
        filename_var2 = f"{str.lower(documents)}/{str.lower(filename)}" # variation 2: all lower
    
        file_hash = hashlib.md5(filename_var1.encode()).hexdigest()

        slide_content = self.lc.get_slide_content(question_id, file_hash, filename_var1, filename_var2)
        if not slide_content:
            self.logger.error(f"Slide content not found {question_id}\n{filename_var1}\n{filename_var2}")
            slide_content = []

        slides_html = f"""<div id="carouselExampleControls-{slide_idx}" class="carousel slide" data-bs-ride="carousel">
                        <div  class="carousel-inner">"""
        for img_idx, img_links in enumerate(slide_content):
            slides_html += f"""<div class="carousel-item {'active' if img_idx == 0 else ''}">
                                <img src="{img_links['image']}" class="d-block" alt="...">
                            </div>"""
        
        slides_html += f"""</div>
                            <button class="carousel-control-prev" type="button" data-bs-target="#carouselExampleControls-{slide_idx}" data-bs-slide="prev">
                                <span class="carousel-control-prev-icon" aria-hidden="true"></span>
                                <span class="visually-hidden"></span>
                            </button>
                            <button class="carousel-control-next" type="button" data-bs-target="#carouselExampleControls-{slide_idx}" data-bs-slide="next">
                                <span class="carousel-control-next-icon" aria-hidden="true"></span>
                                <span class="visually-hidden"></span>
                            </button>
                            </div>"""
        return slides_html

    def replace_slides_json(self, content, question_id):
        self.logger.info("Replacing slides json")

        slide_idx = [0]  # A list to hold the counter, because lists are mutable

        def slide_replacement(match):
            current_slide_idx = slide_idx[0]  # Get the current slide index
            slide_idx[0] += 1  # Increment the counter
            
            # Call slide_match with the current index
            return self.slide_match(match.group(), question_id, current_slide_idx)


        word = "/Documents/"
        content = re.sub(
            pattern=fr"!?!.*{word}.*!?!",
            string=content,
            flags=re.IGNORECASE | re.MULTILINE,
            repl=slide_replacement)
        return content