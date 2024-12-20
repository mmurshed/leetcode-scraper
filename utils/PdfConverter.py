import os
import pypandoc
from queue import Queue
from threading import Thread

from logging import Logger

from utils.Config import Config
from utils.Constants import Constants
from utils.ImageUtil import ImageUtil
from utils.Util import Util

class PdfConverter:
    def __init__(
        self, 
        config: Config,
        logger: Logger,
        images_dir: str):
        
        self.config = config
        self.logger = logger
        self.num_threads = self.valid_num_threads(self.config.threads_count_for_pdf_conversion)
        self.images_dir = images_dir
        
        self.docxArgs = [
            '--resource-path', images_dir
        ]

        self.pdfArgs = [
            '-V', 'geometry:margin=0.5in',
            '--pdf-engine=xelatex',
            f'--template={Constants.TEX_TEMPLATE_PATH}',
            f'--include-in-header={Constants.TEX_HEADER_PATH}',
            '--variable', 'svg',
            '--resource-path', images_dir
        ]

    # Function to validate the number of threads
    def valid_num_threads(self, value):
        try:
            ivalue = int(value)
            if 1 <= ivalue <= 128:
                return ivalue
            else:
                self.logger.warning("Number of threads must be between 1 and 128. Defaulting to 8.")
        except ValueError:
            self.logger.warning("Invalid number of threads. Default to 8.")
        return 8


    def convert_folder(self, source_folder):
        curdir = os.curdir
        os.chdir(source_folder)

        pdf_output_folder = os.path.join(source_folder, 'pdf')
        os.makedirs(pdf_output_folder, exist_ok=True)

        # Create the task queue
        task_queue = Queue()

        # Create worker threads
        workers = []
        for _ in range(self.num_threads):
            worker = Thread(target=self.worker_thread, args=(task_queue, self.docxArgs, self.pdfArgs))
            worker.start()
            workers.append(worker)

        # Populate the task queue with file paths
        sorted_filenames = sorted(f for f in os.listdir(source_folder) if not f.startswith("._"))
        for filename in sorted_filenames:
            if filename.endswith('.html'):
                html_file_path = os.path.join(source_folder, filename)
                docx_output_path = os.path.join(pdf_output_folder, filename.replace('.html', '.docx'))
                pdf_output_path = os.path.join(pdf_output_folder, filename.replace('.html', '.pdf'))
                
                task_queue.put((html_file_path, docx_output_path, pdf_output_path))

        # Add a sentinel (None) for each worker to indicate when to stop
        for _ in range(self.num_threads):
            task_queue.put(None)

        # Wait for all tasks to finish
        task_queue.join()

        # Wait for all threads to finish
        for worker in workers:
            worker.join()

        os.chdir(curdir)

    def convert_single_file(self, file_path):
        curdir = os.curdir
        source_folder = os.path.dirname(file_path)
        os.chdir(source_folder)

        output_dir = os.path.join(source_folder, 'pdf')
        os.makedirs(output_dir, exist_ok=True)

        basename = os.path.basename(file_path)

        # Get the output paths
        docx_output_path = os.path.join(output_dir, basename.replace('.html', '.docx'))
        pdf_output_path = os.path.join(output_dir, basename.replace('.html', '.pdf'))

        # Convert the single file
        converted = self.convert_file(file_path, docx_output_path, pdf_output_path, self.docxArgs, self.pdfArgs)

        os.chdir(curdir)

        return converted


    def worker_thread(self, task_queue, docxArgs, pdfArgs):
        while True:
            task = task_queue.get()

            # Exit the loop if a sentinel value is found
            if task is None:
                task_queue.task_done()
                break

            html_file_path, docx_output_path, pdf_output_path = task
            self.process_file_with_retries(html_file_path, docx_output_path, pdf_output_path, docxArgs, pdfArgs)
            task_queue.task_done()

    def process_file_with_retries(self, html_file_path, docx_output_path, pdf_output_path, docxArgs, pdfArgs):
        """Process a file conversion with retries."""
        success = self.convert_file(html_file_path, docx_output_path, pdf_output_path, docxArgs, pdfArgs)
        if not success:
            try:
                question_id, _ = Util.html_to_question(html_file_path)
                self.logger.info(f"Recompressing the images and retrying pdf convert for question id {question_id} html file path {html_file_path}")
                ImageUtil.recompress_images(question_id=question_id, images_dir=self.images_dir)
                success = self.convert_file(html_file_path, docx_output_path, pdf_output_path, docxArgs, pdfArgs)
            except Exception as e:
                self.logger.info(f"EXCEPTION Recompressing the images and retrying pdf convert {e}")
                return False
        return success  # All retries failed

    def convert_file(self, html_file_path, docx_output_path, pdf_output_path, docxArgs, pdfArgs):
        self.logger.info(f"Converting: {html_file_path}")

        if os.path.exists(pdf_output_path):
            self.logger.warning(f"Pdf file exists, skipping recreation {pdf_output_path}")
            return True

        success = True

        # Convert HTML to DOCX
        if not os.path.exists(docx_output_path):
            try:
                self.logger.info(f"Converting to DOCX: {docx_output_path}")
                pypandoc.convert_file(
                    source_file=html_file_path,
                    to='docx',
                    format='html+tex_math_dollars-tex_math_double_backslash',
                    outputfile=docx_output_path,
                    extra_args=docxArgs)
            except Exception as e:
                self.logger.error(f"ERROR converting to DOCX: {docx_output_path}\n{str(e)}")
                success = False

        # Previous step was successful and docx file exists
        success = success and os.path.exists(docx_output_path)

        # Convert DOCX to PDF
        if success:
            try:
                self.logger.info(f"Converting to PDF: {pdf_output_path}")
                pypandoc.convert_file(
                    source_file=docx_output_path,
                    to='pdf',
                    outputfile=pdf_output_path,
                    extra_args=pdfArgs)
            except Exception as e:
                self.logger.error(f"ERROR converting to PDF: {pdf_output_path}\n{str(e)}")
                success = False

        # Remove the DOCX file after PDF conversion
        if os.path.exists(docx_output_path):
            self.logger.info(f"Removing DOCX file: {docx_output_path}")
            os.remove(docx_output_path)

        # Previous step was successful and pdf file exists
        success = success and os.path.exists(pdf_output_path)

        return success
