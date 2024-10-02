import hashlib
import os
import re
from bs4 import BeautifulSoup
import yt_dlp

from logging import Logger

from LeetcodeUtility import LeetcodeUtility
from LeetcodeConfig import LeetcodeConfig
from LeetcodeApi import LeetcodeApi

class LeetcodeSolution:
    def __init__(
        self,
        config: LeetcodeConfig,
        logger: Logger,
        leetapi: LeetcodeApi):
        
        self.config = config
        self.logger = logger
        self.lc = leetapi

    def place_solution_slides(self, content_soup, slides_json):
            self.logger.debug("Placing solution slides")

            slide_p_tags = set()
            for p in content_soup.find_all('p'):
                text = p.get_text().lower()
                if '/documents/' in text and ".json" in text:
                    slide_p_tags.add(p)

            self.logger.debug(f"slide_p_tags len {len(slide_p_tags)}")

            # For case when <p> is selected twice because of nested <p>
            # Input: <p>something<p>../Documents/a.json</p></p>
            # List contains:
            # 1. <p>something<p>../Documents/a.json</p></p>
            # 2. <p>../Documents/a.json</p>
            # Output:
            # 1. <p>../Documents/a.json</p>
            slide_p_tags_deduped = set()

            # Iterate over all <p> tags in slide_p_tags
            for slide_p_tagx in slide_p_tags:
                textx = slide_p_tagx.get_text().lower()
                # Flag to check if this tag is a duplicate (nested in another tag)
                is_nested = False

                # Compare with all other <p> tags to check if it's nested
                for slide_p_tagy in slide_p_tags:
                    if slide_p_tagx == slide_p_tagy:
                        continue
                    
                    texty = slide_p_tagy.get_text().lower()
                    
                    # If textx is fully contained in texty, mark it as nested
                    if textx in texty:
                        is_nested = True
                        break

                # Add only if it's not nested
                if not is_nested:
                    slide_p_tags_deduped.add(slide_p_tagx)

            slide_p_tags = slide_p_tags_deduped
            self.logger.debug(f"slide_p_tags len {len(slide_p_tags)}")
            
            for slide_idx, slide_p_tag in enumerate(slide_p_tags):
                self.logger.debug(f"slide_idx {slide_idx} {slide_p_tag}")
                
                if slides_json[slide_idx] == []:
                    continue

                slides_html = f"""<div id="carouselExampleControls-{slide_idx}" class="carousel slide" data-bs-ride="carousel">
                                <div  class="carousel-inner">"""
                for img_idx, img_links in enumerate(slides_json[slide_idx]):
                    self.logger.debug(f"Image links: {img_links}")
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
                slide_p_tag.replace_with(BeautifulSoup(
                    slides_html, 'html.parser'))
            return content_soup


    def replace_iframes_with_content(self, content, question_id, root_dir):
        self.logger.debug("Replacing iframe with code")

        videos_dir = os.path.join(root_dir, "videos")
        if self.config.download_videos:
            os.makedirs(videos_dir, exist_ok=True)

        content_soup = BeautifulSoup(content, 'html.parser')
        iframes = content_soup.find_all('iframe')
        for if_idx, iframe in enumerate(iframes, start=1):
            src_url = iframe['src']
            self.logger.debug(f"Playground url: {src_url}")

            src_url_lcase = str.lower(src_url)

            if "playground" in src_url_lcase:
                uuid = src_url.split('/')[-2]
                self.logger.debug(f"Playground uuid: {uuid} url: {src_url}")
                
                playground_content = self.lc.get_all_playground_codes(question_id, uuid)

                if not playground_content:
                    self.logger.error(f"Error in getting code data from source url {src_url}")
                    continue

                code_html = f"""<div>"""
                
                lang_to_include = "all"
                languages = set(item.get("langSlug") for item in playground_content)

                if self.config.preferred_language_order == "all":
                    lang_to_include = self.config.preferred_language
                else:
                    preferred_languages = self.config.preferred_language_order.split(",")
                    for preferred_language in preferred_languages:
                        preferred_language = preferred_language.strip()
                        if preferred_language in languages:
                            lang_to_include = preferred_language
                            break

                for code_idx in range(len(playground_content)):
                    lang = playground_content[code_idx]['langSlug']
                    if lang_to_include == "all" or lang_to_include == lang:
                        code_html += f"""<div style="font-weight: bold;">{lang}</div>"""
                        code_html += f"""<div><code style="color:black"><pre>{playground_content[code_idx]['code']}</pre></code></div>"""

                code_html += f"""</div>"""
                iframe.replace_with(BeautifulSoup(
                    f""" {code_html} """, 'html.parser'))
            elif "vimeo" in src_url_lcase:
                width = iframe.get('width') or 640
                height = iframe.get('height') or 360

                video_id = src_url.split("/")[-1]
                video_extension = "mp4"
                video_basename = f"{LeetcodeUtility.qbasename(question_id, video_id)}.{video_extension}"

                if self.config.download_videos:
                    ydl_opts = {
                        'outtmpl': f'{videos_dir}/{LeetcodeUtility.qstr(question_id)}-%(id)s.%(ext)s',
                        'format': 'bestvideo[height<=720]+bestaudio/best[height<=720]',
                        'http_headers': {
                            'Referer': 'https://leetcode.com',
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

        return str(content_soup)

    def wrap_slides_with_p_tags(self, content):
        # Define the regex pattern to match the entire target string, including the !?! at both ends
        pattern = re.compile(r'(?<!<p>)(\!\?\!.*/Documents/.*\!\?\!)(?!</p>)', re.IGNORECASE | re.MULTILINE)

        # Replace the matched pattern with the <p> wrapped version
        result = pattern.sub(r'<p>\g<0></p>', content)

        return result


    def find_slides_json(self, content, question_id):
        self.logger.info("Finding slides json")

        word = "/Documents/"
        pattern = re.compile(fr"!?!.*{word}.*!?!", re.IGNORECASE | re.MULTILINE)
        slide_names_list = pattern.findall(content)

        slide_names = [x for x in slide_names_list if ".json" in x]

        self.logger.debug(f"Slide names count: {len(slide_names)}")

        slide_contents = []
        for slide_name in slide_names:
            self.logger.debug(f"Slide name: {slide_name}")
            json_split = slide_name.strip().split(".json")
            base_name = json_split[-2]

            self.logger.debug(f"Base name: {base_name}")
            
            json_split = base_name.split("/")
            drop_dots = json_split[1:]
            
            documents = drop_dots[0] # Documents
            self.logger.debug(f"documents: {documents}")

            rest_after_documents = drop_dots[1:] # 01_LIS.json
            filename = "/".join(rest_after_documents)
            self.logger.debug(f"filename: {filename}")

            filename_var1 = f"{str.lower(documents)}/{filename}" # variation 1: only documents/ lower
            filename_var2 = f"{str.lower(documents)}/{str.lower(filename)}" # variation 2: all lower
            self.logger.debug(f"filename_var1: {filename_var1}")
            self.logger.debug(f"filename_var2: {filename_var2}")
        
            file_hash = hashlib.md5(filename_var1.encode()).hexdigest()

            slide_content = self.lc.get_slide_content(question_id, file_hash, filename_var1, filename_var2)
            if not slide_content:    
                slide_content = []

            slide_contents.append(slide_content)

        return slide_contents