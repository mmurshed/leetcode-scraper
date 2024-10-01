class LeetcodeCards:
    def __init__(self, config, logger, leetapi):
        self.config = config
        self.logger = logger
        self.lc = leetapi

    def get_all_cards_url():
        logger.info("Getting all cards url")

        cards = LEETAPI.get_categories()

        with open(CONFIG.cards_url_path, "w") as f:
            for category_card in cards:
                if category_card['slug'] != "featured":
                    for card in category_card['cards']:
                        card_url = "https://leetcode.com/explore/" + \
                            card['categorySlug'] + "/card/" + card['slug'] + "/\n"
                        f.write(card_url)


    def scrape_card_url():
        cards_dir = os.path.join(CONFIG.save_path, "cards")
        os.makedirs(cards_dir, exist_ok=True)
        os.chdir(cards_dir)

        # Creating Index for Card Folder
        with open(os.path.join(cards_dir, "index.html"), 'w') as main_index:
            main_index_html = ""
            with open(CONFIG.cards_url_path, "r") as f:
                card_urls = f.readlines()
                for card_url in card_urls:
                    card_url = card_url.strip()
                    card_slug = card_url.split("/")[-2]
                    main_index_html += f"""<a href={card_slug}/index.html>{card_slug}</a><br>"""        
            main_index.write(main_index_html)

        # Creating HTML for each cards topics
        with open(CONFIG.cards_url_path, "r") as f:
            card_urls = f.readlines()
            for card_url in card_urls:
                card_url = card_url.strip()

                logger.info("Scraping card url: ", card_url)

                card_slug = card_url.split("/")[-2]

                chapters = LEETAPI.get_chapter_with_items(card_slug)

                if chapters:
                    cards_dir = os.path.join(CONFIG.save_path, "cards", card_slug)
                    os.makedirs(cards_dir, exist_ok=True)
                    
                    create_card_index_html(chapters, card_slug)
                    for subcategory in chapters:
                        logger.info("Scraping subcategory: ", subcategory['title'])

                        for item in subcategory['items']:
                            logger.info("Scraping Item: ", item['title'])

                            item_id = item['id']
                            item_title = re.sub(r'[:?|></\\]', replace_filename, item['title'])

                            filename = question_html(item_id, item_title)
                            
                            cards_filepath = os.path.join(cards_dir, filename)

                            if not CONFIG.force_download and os.path.exists(cards_filepath):
                                logger.info(f"Already scraped {cards_filepath}")
                                continue

                            if CONFIG.force_download or not copy_question_file(item_id, item_title, cards_dir):
                                item_content = LEETAPI.get_chapter_items(card_slug, item_id)

                                if item_content:
                                    create_card_html(item_content, item_title, item_id)
                    os.chdir("..")
        os.chdir('..')


    def create_card_html(item_content, item_title, item_id):
        content = """<body>"""
        question_content, _ = get_question_data(item_content)
        content += question_content
        content += get_article_data(item_content, item_title, item_id)
        content += get_html_article_data(item_content, item_title)
        content += """</body>"""
        slides_json = find_slides_json2(content, item_id)
        content = attach_header_in_html() + content
        content_soup = BeautifulSoup(content, 'html.parser')
        content_soup = place_solution_slides(content_soup, slides_json)
        content_soup = fix_image_urls(content_soup, item_id)

        with open(question_html(item_id, item_title), "w", encoding="utf-8") as f:
            f.write(content_soup.prettify())

    def create_card_index_html(chapters, card_slug):
        logger.info("Creating index.html")

        introduction = LEETAPI.get_card_details(card_slug)

        body = ""
        for chapter in chapters:
            body += f"""
                        <br>
                        <h3>{chapter['title']}</h3>
                        {chapter['description']}
                        <br>
            """
            for item in chapter['items']:
                item['title'] = re.sub(r'[:?|></\\]', replace_filename, item['title'])
                item_fname = question_html(item['id'], item['title'])
                body += f"""<a href="{item_fname}">{item['id']}-{item['title']}</a><br>"""
        with open("index.html", 'w') as f:
            f.write(f"""<!DOCTYPE html>
                    <html lang="en">
                    {attach_header_in_html()}
                    <body>
                        <div class="mode">
                        Dark mode:  <span class="change">OFF</span>
                        </div>"
                        <h1 class="card-title">{introduction['title']}</h1>
                        <p class="card-text">{introduction['introduction']}</p>
                        <br>
                        {body}
                    </body>
                    </html>""")
