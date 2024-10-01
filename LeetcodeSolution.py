import os
from bs4 import BeautifulSoup
import yt_dlp

from LeetcodeUtility import LeetcodeUtility

class LeetcodeSolution:
    def __init__(self, config, logger, leetapi):
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


    def replace_iframes_with_codes(self, content, question_id):
        self.logger.debug("Replacing iframe with code")

        videos_dir = os.path.join(self.config.save_path, "questions", "videos")
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
                
                playground_content = self.lc.get_all_playground_codes(
                    LeetcodeUtility.question_id_title(question_id, uuid), uuid)

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
                video_basename = f"{LeetcodeUtility.question_id_title(question_id, video_id)}.{video_extension}"

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


    def attach_header_in_html():
        return r"""<head>
                        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet"/>
                        <link crossorigin="anonymous" href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css" integrity="sha384-rbsA2VBKQhggwzxH7pPCaAqO46MgnOM80zW1RWuH61DGLwZJEdK2Kadq2F9CUG65" rel="stylesheet"/>
                        <script crossorigin="anonymous" integrity="sha384-kenU1KFdBIe4zVF0s0G1M5b4hcpxyD9F7jL+jjXkk+Q2h455rYXK/7HAuoJl+0I4" src="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/js/bootstrap.bundle.min.js">
                        </script>
                        <script src="https://md-block.verou.me/md-block.js" type="module">
                        </script>
                        <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/9000.0.1/prism.min.js">
                        </script>
                        <script src="https://polyfill.io/v3/polyfill.min.js?features=es6">
                        </script>
                        <script async="" src="https://cdn.mathjax.org/mathjax/latest/MathJax.js?config=TeX-MML-AM_CHTML" type="text/javascript">
                        MathJax.Hub.Config({
                                            TeX: {
                                                Macros: {
                                                "exclude": "\\def\\exclude#1{}"
                                                }
                                            },
                                            tex2jax: {
                                                inlineMath: [["$", "$"], ["\\(", "\\)"], ["$$", "$$"], ["\\[", "\\]"] ],
                                                processEscapes: true,
                                                processEnvironments: true,
                                                skipTags: ['script', 'noscript', 'style', 'textarea', 'pre']
                                            },
                                            CommonHTML: {
                                                                scale: 80
                                                            },
                                            });

                                            MathJax.Hub.Register.StartupHook("TeX Jax Ready", function() {
                                            MathJax.Hub.Insert(MathJax.InputJax.TeX.Definitions.macros, {
                                                exclude: "exclude"
                                            });
                                            });
                        </script>
                        <script>
                        document.addEventListener('DOMContentLoaded', function() {
                                                    const carousel = document.querySelectorAll('.carousel');
                                                    console.log(carousel)
                                                    const items = Array.from(document.querySelectorAll('.carousel-item'));
                                                    console.log(items)
                                                    const maxWidth = Math.max(...items.map(item => item.querySelector('img').clientWidth));
                                                    console.log(maxWidth);
                                                    for (let i = 0; i < carousel.length; i++) {
                                                        carousel[i].style.width = maxWidth + 'px';            }
                                                    
                                                    $( ".change" ).on("click", function() {
                                                    if( $( "body" ).hasClass( "dark" )) {
                                                        $( "body" ).removeClass( "dark" );
                                                        $( "div[style*='background: wheat;']" ).removeClass( "dark-banner" );
                                                        $( "div[style*='background: beige;']" ).removeClass( "dark-banner-sq" );
                                                        $("div[id*='v-pills-tabContent']").removeClass( "tab-content dark" );
                                                        $("table").removeClass( "table-color-dark" );
                                                        $("table").addClass( "table-color" );
                                                        $("div[id*='v-pills-tabContent']").addClass( "tab-content" );
                                                        $( ".change" ).text( "OFF" );
                                                    } else {
                                                        $( "body" ).addClass( "dark" );
                                                        $( "div[style*='background: wheat;']" ).addClass( "dark-banner" );
                                                        $( "div[style*='background: beige;']" ).addClass( "dark-banner-sq" );
                                                        $("div[id*='v-pills-tabContent']").addClass( "tab-content dark" );
                                                        $("table").removeClass( "table-color" );
                                                        $("table").addClass( "table-color-dark" );
                                                        $( ".change" ).text( "ON" );
                                                    }
                                });
                                        });
                        </script>
                        <script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/3.4.0/jquery.min.js"></script>
                        <style>
                                    body {
                                        overflow-x: hidden;
                                        background-color: white;
                                        left: 10% !important;
                                        right: 10% !important;
                                        position: absolute;

                                        }
                                        .similar-questions-container {
                                            display: flex;
                                            justify-content: space-between;
                                            }

                                            .left::after {
                                            content: "-";
                                            margin-left: 5px;
                                            }

                                            .right::before {
                                            content: "-";
                                            margin-right: 5px;
                                            }
                                        .mode {
                                            float:right;
                                        }
                                        .dark.tab-content{
                                                background: repeating-linear-gradient(45deg, #130f0f, #3b3b3b4d 100px) !important;
                                        }
                                        .dark-banner-sq{
                                                background-color: #3b3451b8 !important;
                                                border: 1px solid #DCDCDC;
                                        }
                                        .tab-content{
                                            background: white !important;
                                        }
                                        .change {
                                            cursor: pointer;
                                            border: 1px solid #555;
                                            border-radius: 40%;
                                            width: 20px;
                                            text-align: center;
                                            padding: 5px;
                                            margin-left: 8px;
                                        }
                                        .dark{
                                            background-color: #222;
                                            color: #e6e6e6;
                                        }
                                        .dark-banner{
                                            background-color: darkslategray !important;
                                            color: #e6e6e6 !important;
                                        }
                                        .carousel-control-prev > span,
                                        .carousel-control-next > span {
                                        background-color: #007bff; 
                                        border-color: #007bff; 
                                        }
                                        img {
                                            width: auto;
                                            height: auto;
                                            max-width: 100%;
                                            max-height: 100%;
                                        }
                        </style>
                        <style>
                        mjx-container, .mjx-chtml {
                                            display: inline !important;
                                        }
                        </style></head>
    """

    def wrap_slides_with_p_tags(self, content):
        # Define the regex pattern to match the entire target string, including the !?! at both ends
        pattern = re.compile(r'(?<!<p>)(\!\?\!.*/Documents/.*\!\?\!)(?!</p>)', re.IGNORECASE | re.MULTILINE)

        # Replace the matched pattern with the <p> wrapped version
        result = pattern.sub(r'<p>\g<0></p>', content)

        return result


    def find_slides_json2(self, content, question_id):
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

            slide_content = self.lc.get_slide_content(question_id_title(question_id, file_hash), filename_var1, filename_var2)
            if not slide_content:    
                slide_content = []

            slide_contents.append(slide_content)

        return slide_contents

    def get_all_submissions():
        all_questions = get_all_questions_url(force_download=self.config.force_download)
        for question in all_questions:
            item_content = {"question": {'titleSlug': question['titleSlug'], 'frontendQuestionId': question['frontendQuestionId'], 'title': question['title']}}
            get_submission_data(item_content, False)

    def get_submission_data(item_content, save_submission_as_file):

        list_of_submissions = {}

        if item_content['question']:
            question_frontend_id = int(item_content['question']['frontendQuestionId']) if item_content['question']['frontendQuestionId'] else 0
            question_title_slug = item_content['question']['titleSlug']

            submission_content = self.lc.get_submission_list(question_id_title(question_frontend_id, 'subm'), question_title_slug)
            if not submission_content or len(submission_content) == 0:
                return

            for i, submission in enumerate(submission_content):
                submission_id = submission['id']
                if submission["statusDisplay"] != "Accepted":
                    continue

                submission_detail_content = self.lc.get_submission_details(question_id_title(question_frontend_id, submission_id), submission_id)
                if not submission_detail_content:
                    continue
                
                if save_submission_as_file:
                    list_of_submissions[int(submission["timestamp"])] = submission_detail_content['code']
                else:
                    submissions_download_dir = os.path.join(self.config.save_path, "questions", "submissions")
                    os.makedirs(submissions_download_dir, exist_ok=True)

                    file_extension = FILE_EXTENSIONS[submission["lang"]]
                    submission_file_name = f"{question_frontend_id:04}-{i+1:02}-{submission_id}.{file_extension}"
                    submission_file_path = os.path.join(submissions_download_dir, submission_file_name)

                    with open(submission_file_path, "w") as outfile:
                        outfile.write(submission_detail_content['code'])
        return list_of_submissions

    def get_solution_content(question_id, question_title_slug):
        self.logger.info("Getting solution data")

        solution = self.lc.get_official_solution(question_id_title(question_id, 'sol'), question_title_slug)
        return solution
