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
    def recompress_images(question_id, images_dir, formats=None):
        """Recompress all images for a given question.
        
        Args:
            question_id: The question ID
            images_dir: Directory containing the images
            formats: List of formats to recompress. If None, uses ["all"]
        """
        # Convert the question_id to a zero-padded 4-digit string
        question_id_str = Util.qstr(question_id)

        # Loop through all files in the source folder
        for filename in os.listdir(images_dir):
            if filename.startswith(question_id_str):
                input_image_path = os.path.join(images_dir, filename)
                ImageUtil.recompress_image(input_image_path, formats)


    @staticmethod
    def recompress_image(img_path, formats=None):
        """Recompress an image based on specified formats.
        
        Args:
            img_path: Path to the image file
            formats: List of formats to recompress. Options: "all", "png", "jpg", "webp"
                    If None or empty, no recompression is done.
                    If "all" is in the list, all formats are recompressed.
        
        Returns:
            New path if the file was converted (e.g., webp -> png), otherwise original path
        """
        if not formats:
            return img_path
        
        try:
            img_path_lower = img_path.lower()
            
            # Check if we should process this format
            should_process = False
            if "all" in formats:
                should_process = True
            elif img_path_lower.endswith('.png') and "png" in formats:
                should_process = True
            elif img_path_lower.endswith(('.jpg', '.jpeg')) and "jpg" in formats:
                should_process = True
            elif img_path_lower.endswith('.webp') and "webp" in formats:
                should_process = True
            
            if not should_process:
                return img_path
            
            # Open the image
            with Image.open(img_path) as img:
                # Convert RGBA to RGB if necessary (for JPEG compatibility)
                if img.mode in ('RGBA', 'LA', 'P'):
                    # Create a white background
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                    img = background
                
                if img_path_lower.endswith('.png'):
                    # Save the image with optimization
                    img.save(img_path, 'PNG', optimize=True)
                elif img_path_lower.endswith(('.jpg', '.jpeg')):
                    # Recompress JPEG with a quality parameter (default is 75, you can adjust)
                    img.save(img_path, 'JPEG', quality=85, optimize=True)
                elif img_path_lower.endswith('.webp'):
                    # Convert webp to PNG for better LaTeX compatibility
                    png_path = img_path[:-5] + '.png'  # Replace .webp with .png
                    img.save(png_path, 'PNG', optimize=True)
                    # Remove the original webp file
                    if os.path.exists(png_path):
                        os.remove(img_path)
                        # Return the new path so caller can update references
                        return png_path
                    return img_path
        except Exception as e:
            pass
        return img_path
    
    @staticmethod
    def convert_webp_to_png_in_directory(directory, logger=None):
        """Convert all webp images in a directory (recursively) to PNG format.
        
        Args:
            directory: Root directory to search for webp files
            logger: Optional logger for progress messages
            
        Returns:
            Tuple of (converted_count, failed_count)
        """
        converted_count = 0
        failed_count = 0
        
        if logger:
            logger.debug(f"Searching for webp images in: {directory}")
        
        # Walk through all subdirectories
        for root, dirs, files in os.walk(directory):
            for filename in files:
                if filename.lower().endswith('.webp'):
                    webp_path = os.path.join(root, filename)
                    png_path = webp_path[:-5] + '.png'
                    
                    try:
                        # Open and convert to PNG
                        with Image.open(webp_path) as img:
                            # Convert RGBA to RGB if needed
                            if img.mode in ('RGBA', 'LA', 'P'):
                                background = Image.new('RGB', img.size, (255, 255, 255))
                                if img.mode == 'P':
                                    img = img.convert('RGBA')
                                background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                                img = background
                            
                            # Save as PNG
                            img.save(png_path, 'PNG', optimize=True)
                        
                        # Verify the PNG was created successfully
                        if os.path.exists(png_path):
                            # Remove the original webp file
                            os.remove(webp_path)
                            converted_count += 1
                            if logger:
                                logger.debug(f"Converted: {filename} -> {os.path.basename(png_path)}")
                        else:
                            failed_count += 1
                            if logger:
                                logger.error(f"Failed to create PNG: {filename}")
                    
                    except Exception as e:
                        failed_count += 1
                        if logger:
                            logger.error(f"Error converting {filename}: {e}")
        
        if logger:
            logger.debug(f"WebP conversion complete: {converted_count} converted, {failed_count} failed")
        
        return converted_count, failed_count

