class LeetcodeImage:
    def __init__(self):
        pass

    def is_valid_image(image_path):
        # SVG file is allowed by default
        if image_path.lower().endswith('.svg'):
            return True

        try:
            with Image.open(image_path) as img:
                img.verify()
        except:
            return False
        return True

    def decompose_gif(gif_path, filename_no_ext, output_folder):
        # Open the GIF file
        gif = Image.open(gif_path)
        
        frame_paths = []

        # Iterate over each frame in the GIF
        frame_number = 0
        while True:
            try:
                # Save each frame as a separate image
                frame_path = os.path.join(output_folder, f"{filename_no_ext}_{frame_number:03d}.png")
                gif.seek(frame_number)
                gif.save(frame_path, 'PNG')
                frame_number += 1
                frame_paths.append(frame_path)
            except EOFError:
                break
        return frame_paths


    def convert_to_uncompressed_png(img_path, img_ext):
        # Open the PNG file
        try:
            if img_ext == 'png':
                with Image.open(img_path) as img:
                    # Save the image without compression
                    img.save(img_path, 'PNG', compress_level=0)
                    logger.debug(f"Decompressed PNG saved at {img_path}")
        except Exception as e:
            logger.error(f"Error reading file {img_path}\n{e}")
            return None

    def recompress_images(question_id):
        images_dir = os.path.join(CONFIG.save_path, "questions", "images")

        # Convert the question_id to a zero-padded 4-digit string
        question_id_str = qstr(question_id)

        # Loop through all files in the source folder
        for filename in os.listdir(images_dir):
            if filename.startswith(question_id_str):
                input_image_path = os.path.join(images_dir, filename)
                recompress_image(input_image_path)


    def recompress_image(img_path):
        try:
            img_path_lower = img_path.lower()
            # Open the image
            with Image.open(img_path) as img:
                if img_path_lower.endswith('.png'):
                    # Save the image with optimization
                    img.save(img_path, optimize=True)
                    logger.debug(f"Recompressed and overwrote: {img_path}")
                elif img_path_lower.endswith(('.jpg', '.jpeg')):
                    # Recompress JPEG with a quality parameter (default is 75, you can adjust)
                    img.save(img_path, 'JPEG', quality=85, optimize=True)
                    logger.debug(f"Recompressed and overwrote: {img_path}")
        except Exception as e:
            logger.error(f"Error recompressing {img_path}: {e}")
            return

    def download_image(question_id, img_url):
        logger.debug(f"Downloading image: {img_url}")

        if not validators.url(img_url):
            logger.error(f"Invalid image url: {img_url}")
            return
        
        images_dir = os.path.join(CONFIG.save_path, "questions", "images")
        os.makedirs(images_dir, exist_ok=True)
        
        parsed_url = urlsplit(img_url)
        basename = os.path.basename(parsed_url.path)

        img_ext = str.lower(basename.split('.')[-1])

        url_hash = hashlib.md5(img_url.encode()).hexdigest()
        image_path = os.path.join(images_dir, f"{question_id_title(question_id, url_hash)}.{img_ext}")

        if not CONFIG.cache_data or not os.path.exists(image_path):
            try:
                img_data = CLOUD_SCRAPER.get(url=img_url).content

                with open(image_path, 'wb') as file:
                    file.write(img_data)

                if CONFIG.recompress_image:
                    recompress_image(image_path)

            except Exception as e:
                logger.error(f"Error downloading image url: {img_url}")
                return None

        if not os.path.exists(image_path):
            logger.error(f"File not found {image_path}\n{img_url}")
            return None

        if not is_valid_image(image_path):
            os.remove(image_path)
            logger.error(f"Invalid image file from url: {img_url}")
            return None

        if CONFIG.extract_gif_frames and img_ext == "gif":
            files = decompose_gif(image_path, url_hash, images_dir)
        else:
            files = [image_path]

        return files

    def load_image_local(files):
        questions_dir = os.path.join(CONFIG.save_path, "questions")
        relframes = [os.path.relpath(frame, questions_dir) for frame in files]

        return relframes

    def load_image_in_b64(files, img_url):
        logger.debug(f"Loading image: {img_url}")

        parsed_url = urlsplit(img_url)
        basename = os.path.basename(parsed_url.path)
        img_ext = str.lower(basename.split('.')[-1])

        if img_ext == "svg":
            img_ext = "svg+xml"

        encoded_string = None

        imgs_decoded = []
        for file in files:
            if not is_valid_image(file):
                continue

            with open(file, "rb") as file:
                img_data = file.read()
                encoded_string = base64.b64encode(img_data)

            if not encoded_string:
                logger.error(f"Error loading image url: {img_url}")
                return None

            decoded_string = encoded_string.decode('utf-8')
            decoded_image = f"data:image/{img_ext};base64,{decoded_string}"
            imgs_decoded.append(decoded_image)

        return imgs_decoded

    def fix_image_urls(content_soup, question_id):
        logger.info("Fixing image urls")

        images = content_soup.select('img')

        for image in images:
            logger.debug(f"img[src]: {image['src']}")
            if image.has_attr('src') and "base64" not in image['src']:
                splitted_image_src = image['src'].split('/')

                if ".." in splitted_image_src:
                    index = 0
                    for idx in range(len(splitted_image_src)-1):
                        if splitted_image_src[idx] == ".." and splitted_image_src[idx+1] != "..":
                            index = idx+1
                    img_url = f"https://leetcode.com/explore/{'/'.join(splitted_image_src[index:])}"
                else:
                    img_url = image['src']
                    # Parse the URL
                    img_url_parsed = urlparse(img_url)
                    hostname = img_url_parsed.hostname

                    # Check for localhost or 127.0.0.1
                    if hostname == "127.0.0.1" or hostname == "localhost":
                        logger.warning(f"localhost detected: {img_url}")
                        # Remove leading `/` from the path before appending, or directly append the path
                        img_url = f"https://leetcode.com/explore{img_url_parsed.path}"                    

                logger.debug(f"img_url: {img_url}")

                image['src'] = img_url

                if CONFIG.download_images:
                    files = download_image(question_id, img_url)
                    if files:
                        if CONFIG.base64_encode_image:
                            frames = load_image_in_b64(files, img_url)
                        else:
                            frames = load_image_local(files)

                        if frames and len(frames) > 0:
                            if len(frames) == 1:
                                if frames[0]:
                                    image['src'] = frames[0]
                                else:
                                    image.decompose()
                            else:
                                new_tags = []
                                for frame in frames:
                                    if frame:
                                        frame_tag = content_soup.new_tag('img', src=frame)
                                        new_tags.append(frame_tag)

                                # Replace the GIF <img> tag with the new image tags
                                image.replace_with(*new_tags)
                        else:
                            image.decompose()
                    else:
                        image.decompose()
        return content_soup

    def manual_convert_images_to_base64():
        root_dir = input("Enter path of the folder where html are located: ")
        for root, dirs, files in os.walk(root_dir):
            for file in files:
                if file.endswith('.html'):
                    with open(os.path.join(root, file), "r") as f:
                        soup = BeautifulSoup(f.read(), 'html.parser')
                        question_id, _ = html_toquestion(file)
                        res_soup = fix_image_urls(soup, question_id)
                    with open(os.path.join(root, file), "w") as f:
                        f.write(res_soup.prettify())
        
