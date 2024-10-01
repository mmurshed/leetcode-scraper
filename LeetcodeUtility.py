import os
import re
import shutil
import sys
import markdown

class LeetcodeUtility:
    @staticmethod
    def clear():
        current_os = sys.platform
        
        if current_os.startswith('darwin'):
            os.system('clear')
        elif current_os.startswith('linux'):
            os.system('clear')
        elif current_os.startswith('win32') or current_os.startswith('cygwin'):
            os.system('cls')


    @staticmethod
    def copy_question_file(save_path, question_id, question_title, dest_dir, copy_pdf = True, copy_videos = False):
        questions_dir = os.path.join(save_path, "questions")
        question_filename = LeetcodeUtility.qhtml(question_id, question_title)
        question_filepath = os.path.join(questions_dir, question_filename)

        # logger.info(f"Copying {question_filepath} to {dest_dir}")

        if not os.path.exists(question_filepath):
            # logger.error(f"File not found: {question_filepath}")
            return False

        if not os.path.exists(dest_dir):
            # logger.error(f"Destination not found: {dest_dir}")
            return False

        # Copy html
        destination_filepath = os.path.join(dest_dir, question_filename)
        shutil.copy2(question_filepath, destination_filepath)

        question_id_str = LeetcodeUtility.qstr(question_id)

        # Copy images
        images_dir = os.path.join(questions_dir, "images")
        dest_images_dir = os.path.join(dest_dir, "images")
        os.makedirs(dest_images_dir, exist_ok=True)

        for filename in os.listdir(images_dir):
            if filename.startswith(question_id_str):
                source_imagepath = os.path.join(images_dir, filename)
                dest_imagepath = os.path.join(dest_images_dir, filename)
                shutil.copy2(source_imagepath, dest_imagepath)

        # Copy pdf
        if copy_pdf:
            question_basename = LeetcodeUtility.qbasename(question_id, question_title)
            pdf_dir = os.path.join(save_path, "questions_pdf")
            dest_pdf_dir = os.path.join(dest_dir, "questions_pdf")

            os.makedirs(dest_pdf_dir, exist_ok=True)
            question_filepath = os.path.join(pdf_dir, f"{question_basename}.pdf")
            destination_filepath = os.path.join(dest_pdf_dir, f"{question_basename}.pdf")
            
            if os.path.exists(question_filepath):
                shutil.copy2(question_filepath, destination_filepath)

        # Copy videos
        if copy_videos:
            videos_dir = os.path.join(questions_dir, "videos")
            dest_videos_dir = os.path.join(dest_dir, "videos")
            os.makedirs(dest_videos_dir, exist_ok=True)
            for filename in os.listdir(videos_dir):
                if filename.startswith(question_id_str):
                    source_imagepath = os.path.join(videos_dir, filename)
                    dest_imagepath = os.path.join(dest_videos_dir, filename)
                    shutil.copy2(source_imagepath, dest_imagepath)
        
        return True

    @staticmethod
    def html_to_question(filename):
        filename = os.path.basename(filename)

        # Remove the file extension
        name, _ = os.path.splitext(filename)
        
        # Split the string on the first dash and strip whitespace
        try:
            question_id, question_title = name.split('-', 1)
            question_id = int(question_id.strip())
            question_title = question_title.strip()
            
            return question_id, question_title
        except ValueError:
            raise ValueError(f"Filename format is incorrect: {filename}")

    @staticmethod
    def qstr(question_id):
        return f"{question_id:04}"

    @staticmethod
    def qhtml(question_id, queston_title):
        return f"{LeetcodeUtility.qbasename(question_id, queston_title)}.html"

    @staticmethod
    def qbasename(question_id, queston_title):
        return f"{LeetcodeUtility.qstr(question_id)}-{queston_title}"


    @staticmethod
    def convert_display_math_to_inline(content):
        # Strip spaces inside $$ ... $$ and convert it to $ ... $
        content = re.sub(r'\$\$\s*(.*?)\s*\$\$', r'$\1$', content)
        return content

    # Function to clean up math expressions
    @staticmethod
    def clean_tex_math(content):
        # Replace \space with a regular space
        return re.sub(r'\\space', ' ', content)

    @staticmethod
    def markdown_with_math(content):
        content = LeetcodeUtility.convert_display_math_to_inline(content)
        content = LeetcodeUtility.clean_tex_math(content)

        # Convert Markdown to HTML and ensure TeX math is not escaped
        return markdown.markdown(
            content,
            extensions=['extra', 'mdx_math'])
    
    @staticmethod
    def replace_filename(str):
        numDict = {':': ' ', '?': ' ', '|': ' ', '>': ' ', '<': ' ', '/': ' ', '\\': ' '}
        return numDict[str.group()]

    @staticmethod
    def get_cache_path(save_path, category, filename):
        data_dir = os.path.join(save_path, "cache", category)
        os.makedirs(data_dir, exist_ok=True)

        data_path = os.path.join(data_dir, filename)
        return data_path
    
