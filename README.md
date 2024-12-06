## Leetcode-Scraper

Leetcode downloader that uses Api Requests to get content.

## Installation
`pip install -r requirements.txt`

## Run
`python LeetcodeScraper.py`

Use `--proxy` option to set a proxy url.

## Menu Options

1. **Setup Config**: Initialize or update the configuration settings.
2. **Download a Card by Name**: Download a specific card using its name. It will ask about the card name (e.g., `google`). Cards are available in the **Explore** page. Once you click the play button the card name will be displayed in the URL.
3. **Download All Cards**: Download all available cards.
4. **Download a Question by ID**: Download a specific question using its ID. It will ask about the question id (e.g., `2`, `1030`).
5. **Download All Questions**: Download all available questions.
6. **Download All Questions for a Company**: Download all questions related to a specific company. It will ask about the company name (e.g., `google`, `microsoft`, `facebook`, `amazon`, etc.). Company names are displayed on the right sidebard of the `Problems` page.
7. **Download All Favorite Questions for a Company**: Download all favorite questions associated with a particular company. It will ask about the company name (e.g., `google`, `microsoft`, `facebook`, `amazon`, etc.) followed by the favorite category displayed as list.
8. **Download All Company Questions**: Download all questions for all companies and for all favorite categories.
9. **Download Submissions by Question ID**: Download all of your accepted submissions for a specific question using its ID and save as source files.
10. **Download All Your Submissions**: Download all your accepted submissions and save as source files.
11. **Convert All Files from a Directory to PDF**: Convert every file in a specified directory to PDF format. If failed it will convert the PNG and JPG and retry.
12. **Get Cache by Key**: Retrieve a cached item using its key. It will ask about a cache key (e.g., `question-0002` returns cache for question data for id 0002).
13. **Delete Cache by Key**: Remove a specific item from the cache using its key. It will ask about a cache key (e.g., `question-1030-solution-ollama` will delete cache for ai solution generated using ollama)
14. **Clear Cache**: Clear all cached items.

## Configuration Values

The following configuration values are essential for setting up and customizing the application:

* `leetcode_cookie`: Authentication token required to access resources.
* `save_directory`: Path where downloaded items will be saved.
* `overwrite`: Boolean flag to determine if existing files should be overwritten. When true and the question html file exists it will not be downloaded again. True by default.
* `download_images`: Boolean flag to enable downloading of images. When true the images will be downloaded to `images` sub directory and linked from there. Otherwise, the images will be included as urls. True by default.
* `download_videos`: Boolean flag to enable downloading of videos. When true the videos will be downloaded to `videos` sub directory and linked from there. Otherwise, the videos will be included as urls. False by default.
* `preferred_language_order`: List of preferred languages for downloading questions (e.g., `csharp`, `cpp`, `python`, `java`, `scala`, etc.). When including solution, preferred lanauge order is used to include the implementation. If you want implementation in `all` languages, specify `all`. This setting is also used to generate AI implmentation.
* `include_submissions_count`: Specifies the number of your own successful submissions to include, if any. 0 to exclude your submissions, which is the default.
* `include_community_solution_count`: Specifies the number of community solutions (most voted) to include when official solution isn't available. If the official solution is available, no community solution will be included. 0 to exclude community solutions. 1 by default.
* `cache_api_calls`: Boolean flag to enable/disable caching of API calls. When true API resposnes will be cached for number of days as specified in the `cache_expiration_days` settings. True by default.


## Additional Settings
* `cache_expiration_days`: Number of days before cache expires. 7 days by default.
* `include_default_code`: Boolean flag to include or exclude default code in downloads. False by default.
* `extract_gif_frames`: Boolean flag to determine if GIF frames should be extracted. False by default since it can generate a large number of frames.
* `recompress_image`: Boolean flag to enable or disable image recompression. False by default.
* `base64_encode_image`: Boolean flag to enable/disable base64 encoding of images. False by default.
* `threads_count_for_pdf_conversion`: Number of threads to use for converting files to PDF. 8 by default.
* `api_max_failures`: Maximum number of API call failures before aborting. 3 by default.
* `logging_level`: Set the logging level (e.g., `debug`, `error`, `info`). `info` by default.

## Directories (optional)
* `cache_directory`: Directory path for storing cached items. This is initiated from save directory as `{SAVE_DIRECTOTY}/cache`.
* `cards_directory`: Directory where card files will be saved. This is initiated from save directory as `{SAVE_DIRECTOTY}/cards`.
* `companies_directory`: Directory where company-related files will be stored. This is initiated from save directory as `{SAVE_DIRECTOTY}/companies`.
* `questions_directory`: Directory for storing question files. This is initiated from save directory as `{SAVE_DIRECTOTY}/questions`.
* `submissions_directory`: Directory to store submissions data. This is initiated from save directory as `{SAVE_DIRECTOTY}/submissions`.

## AI Related (optional)
* `ai_solution_generator`: AI solution generator to use (`openai`, or `ollama`). When this string is empty, no solution is generated with AI.
* `open_ai_api_key`: API key for the Open AI solution generator.
* `open_ai_model`: Model specification for OpenAI usage (e.g., `gpt-4o-mini`).
* `ollama_url`: URL for [Ollama API](https://github.com/ollama/ollama) (e.g., `http://localhost:11434/api/generate`).
* `ollama_model`: Model specification for Ollama API (e.g., `llama3.1`).

## Tips
* Exclude video download in first attempt since videos take time to download. Download with both `download_images` and `overwrite` set to true, but `download_videos` set to false. Then download again with `download_videos` and `overwrite` set to true, but `download_images` set to false. The second time the api calls will be cached and images already downloaded. So only video downloads will take place but you will already have the questions to work with.
* If PDF conversion fails, it will attempt to recompress PNG and JPG and retry. If the SVG fails, check if the SVG file was downlaoded correct. The image files start with question id. Find the question id in the `images` directory and then check if it opens in browser. Delete faulty image and download the question again.
* To setup Ollama follow the [github page](https://github.com/ollama/ollama). In my testing `llama3.1` worked great.
* To setup Open AI for solution generation use paid version. Once paid you can generate a token to use. The `gpt-4o-mini` works pretty well and is fairly cost effective.
* To avoid duplicates when downloading company questions, each favorite category contains question for that period. For example, three months category contain questions from 30 days to 3 months, but not question earlier than 30 days.
* When updating make sure the cache is clean but `overwrite` is set to false to avoid downloading again. For example, to update google questions for 30-days, set `overwrite` to false, the delete cache keys `company-favorite-google-thirty-days`, `company-favorite-google-three-months`, `company-favorite-google-six-months`,`company-favorite-google-more-than-six-months`, `company-favorite-google-all`.