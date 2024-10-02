import os
import argparse
import pypandoc
from queue import Queue
from threading import Thread

from logging import Logger

from LeetcodeConfig import LeetcodeConfig
from LeetcodeConstants import LeetcodeConstants

class LeetcodePdfConverter:
    def __init__(
        self, 
        config: LeetcodeConfig,
        logger: Logger,
        images_dir: str,
        num_threads: int = 8):
        
        self.config = config
        self.logger = logger
        self.num_threads = self.valid_num_threads(num_threads)
        
        self.docxArgs = [
            '--resource-path', images_dir
        ]

        template_file = os.path.join(LeetcodeConstants.ROOT_DIR, "leet-template.latex")
        header_file = os.path.join(LeetcodeConstants.ROOT_DIR, "enumitem.tex")

        if not os.path.exists(template_file):
            raise Exception(f"Template file missing {template_file}")

        if not os.path.exists(header_file):
            raise Exception(f"Header file missing {header_file}")

        self.pdfArgs = [
            '-V', 'geometry:margin=0.5in',
            '--pdf-engine=xelatex',
            f'--template={template_file}',
            f'--include-in-header={header_file}',
            '--resource-path', images_dir
        ]

    # Function to validate the number of threads
    def valid_num_threads(self, value):
        try:
            ivalue = int(value)
            if 1 <= ivalue <= 128:
                return ivalue
            else:
                raise argparse.ArgumentTypeError("Number of threads must be between 1 and 128")
        except ValueError:
            raise argparse.ArgumentTypeError("Invalid number of threads")


    def convert_folder(self, source_folder):
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
        sorted_filenames = sorted(os.listdir(source_folder))
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

    def convert_single_file(self, file_path):
        # Set the PDF output folder one level up from the file's directory and rename to 'questions_pdf'
        source_folder = os.path.dirname(file_path)
        os.chdir(source_folder)

        basename = os.path.basename(file_path)

        # Get the output paths
        docx_output_path = os.path.join(source_folder, basename.replace('.html', '.docx'))
        pdf_output_path = os.path.join(source_folder, basename.replace('.html', '.pdf'))

        # Convert the single file
        converted = self.convert_file(file_path, docx_output_path, pdf_output_path, self.docxArgs, self.pdfArgs)

        return converted


    def worker_thread(self, task_queue, docxArgs, pdfArgs):
        while True:
            task = task_queue.get()

            # Exit the loop if a sentinel value is found
            if task is None:
                task_queue.task_done()
                break

            html_file_path, docx_output_path, pdf_output_path = task
            self.convert_file(html_file_path, docx_output_path, pdf_output_path, docxArgs, pdfArgs)
            task_queue.task_done()

    def convert_file(self, html_file_path, docx_output_path, pdf_output_path, docxArgs, pdfArgs):
        self.logger.info(f"Converting: {html_file_path}")

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
                return False

        # Convert DOCX to PDF
        if os.path.exists(docx_output_path) and not os.path.exists(pdf_output_path):
            try:
                self.logger.info(f"Converting to PDF: {pdf_output_path}")
                pypandoc.convert_file(
                    source_file=docx_output_path,
                    to='pdf',
                    outputfile=pdf_output_path,
                    extra_args=pdfArgs)

                # Remove the DOCX file after PDF conversion
                if os.path.exists(docx_output_path):
                    self.logger.info(f"Removing DOCX file: {docx_output_path}")
                    os.remove(docx_output_path)
            except Exception as e:
                self.logger.error(f"ERROR converting to PDF: {pdf_output_path}\n{str(e)}")
                return False

        return True
