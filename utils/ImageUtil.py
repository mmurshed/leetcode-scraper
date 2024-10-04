import os
from PIL import Image

from utils.Constants import Constants
from utils.Util import Util

class ImageUtil:
    @staticmethod
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

    @staticmethod
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

    @staticmethod
    def convert_to_uncompressed_png(img_path, img_ext):
        # Open the PNG file
        if img_ext == 'png':
            with Image.open(img_path) as img:
                # Save the image without compression
                img.save(img_path, 'PNG', compress_level=0)

    @staticmethod
    def recompress_images(question_id, images_dir):
        # Convert the question_id to a zero-padded 4-digit string
        question_id_str = Util.qstr(question_id)

        # Loop through all files in the source folder
        for filename in os.listdir(images_dir):
            if filename.startswith(question_id_str):
                input_image_path = os.path.join(images_dir, filename)
                ImageUtil.recompress_image(input_image_path)


    @staticmethod
    def recompress_image(img_path):
        try:
            img_path_lower = img_path.lower()
            # Open the image
            with Image.open(img_path) as img:
                if img_path_lower.endswith('.png'):
                    # Save the image with optimization
                    img.save(img_path, optimize=True)
                elif img_path_lower.endswith(('.jpg', '.jpeg')):
                    # Recompress JPEG with a quality parameter (default is 75, you can adjust)
                    img.save(img_path, 'JPEG', quality=85, optimize=True)
        except Exception as e:
            pass
