import os
import argparse
import pypandoc
from queue import Queue
from threading import Thread
import logging
from logging.handlers import RotatingFileHandler
import time  # Import the time module

# Set up logging
log_file = 'conversion_errors.log'
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('Converter')
handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=5)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Function to validate the number of threads
def valid_num_threads(value):
    try:
        ivalue = int(value)
        if 1 <= ivalue <= 128:
            return ivalue
        else:
            raise argparse.ArgumentTypeError("Number of threads must be between 1 and 128")
    except ValueError:
        raise argparse.ArgumentTypeError("Invalid number of threads")

def convert_html_to_docx(source_path, num_threads=32):

    # Get the absolute path to the script
    script_path = os.path.abspath(__file__)

    # Get the directory containing the script
    script_dir = os.path.dirname(script_path)

    # Define conversion arguments for docx and pdf
    images_dir = os.path.join(os.path.dirname(source_path), "images")
    logger.info(f"Images dir {images_dir}")
    docxArgs = [
        '--resource-path', images_dir
    ]

    pdfArgs = [
        '-V', 'geometry:margin=0.5in',
        '--pdf-engine=xelatex',
        f'--template={script_dir}/leet-template.latex',
        f'--include-in-header={script_dir}/enumitem.tex',
        '--resource-path', images_dir
    ]

    # Start the timer
    start_time = time.time()

    # Check if the provided path is a file or folder
    if os.path.isfile(source_path):
        # Single file conversion
        convert_single_file(source_path, docxArgs, pdfArgs)
    elif os.path.isdir(source_path):
        # Folder conversion
        convert_folder(source_path, num_threads, docxArgs, pdfArgs)
    else:
        logger.error(f"Invalid path: {source_path}. It is neither a file nor a folder.")

    # End the timer and log the total time taken
    end_time = time.time()
    total_time = end_time - start_time
    logger.info(f"Total conversion time: {total_time:.2f} seconds")

def convert_folder(source_folder, num_threads, docxArgs, pdfArgs):
    os.chdir(source_folder)

    # Set the PDF output folder one level up from the source folder and rename to 'questions_pdf'
    pdf_output_folder = os.path.join(os.path.dirname(source_folder), 'questions_pdf')
    os.makedirs(pdf_output_folder, exist_ok=True)

    # Create the task queue
    task_queue = Queue()

    # Create worker threads
    workers = []
    for _ in range(num_threads):
        worker = Thread(target=worker_thread, args=(task_queue, docxArgs, pdfArgs))
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
    for _ in range(num_threads):
        task_queue.put(None)

    # Wait for all tasks to finish
    task_queue.join()

    # Wait for all threads to finish
    for worker in workers:
        worker.join()

def convert_single_file(file_path, docxArgs, pdfArgs):
    # Set the PDF output folder one level up from the file's directory and rename to 'questions_pdf'
    source_folder = os.path.dirname(file_path)
    os.makedirs(source_folder, exist_ok=True)

    os.chdir(source_folder)

    # Get the output paths
    docx_output_path = os.path.join(source_folder, os.path.basename(file_path).replace('.html', '.docx'))
    pdf_output_path = os.path.join(source_folder, os.path.basename(file_path).replace('.html', '.pdf'))

    # Convert the single file
    convert_file(file_path, docx_output_path, pdf_output_path, docxArgs, pdfArgs)


def worker_thread(task_queue, docxArgs, pdfArgs):
    while True:
        task = task_queue.get()

        # Exit the loop if a sentinel value is found
        if task is None:
            task_queue.task_done()
            break

        html_file_path, docx_output_path, pdf_output_path = task
        convert_file(html_file_path, docx_output_path, pdf_output_path, docxArgs, pdfArgs)
        task_queue.task_done()

def convert_file(html_file_path, docx_output_path, pdf_output_path, docxArgs, pdfArgs):
    logger.info(f"Converting: {html_file_path}")

    # Convert HTML to DOCX
    if not os.path.exists(docx_output_path):
        try:
            logger.info(f"Converting to DOCX: {docx_output_path}")
            pypandoc.convert_file(
                source_file=html_file_path,
                to='docx',
                format='html+tex_math_dollars-tex_math_double_backslash',
                outputfile=docx_output_path,
                extra_args=docxArgs)
        except Exception as e:
            logger.error(f"ERROR converting to DOCX: {docx_output_path}\n{str(e)}")

    # Convert DOCX to PDF
    if os.path.exists(docx_output_path) and not os.path.exists(pdf_output_path):
        try:
            logger.info(f"Converting to PDF: {pdf_output_path}")
            pypandoc.convert_file(
                source_file=docx_output_path,
                to='pdf',
                outputfile=pdf_output_path,
                extra_args=pdfArgs)

            # Remove the DOCX file after PDF conversion
            if os.path.exists(docx_output_path):
                logger.info(f"Removing DOCX file: {docx_output_path}")
                os.remove(docx_output_path)
        except Exception as e:
            logger.error(f"ERROR converting to PDF: {pdf_output_path}\n{str(e)}")

def main():
    parser = argparse.ArgumentParser(description="Convert HTML files to DOCX and PDF")
    parser.add_argument("path", help="Path to the folder or file to convert (HTML file or folder containing HTML files)")
    parser.add_argument("--threads", "-t", type=valid_num_threads, default=32,
                        help="Number of threads to use (default: 32, valid range: 1-128)")
    
    args = parser.parse_args()
    
    current_dir = os.curdir
    convert_html_to_docx(args.path, num_threads=args.threads)
    os.chdir(current_dir)

if __name__ == "__main__":
    main()