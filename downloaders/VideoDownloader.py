import os
import yt_dlp

from logging import Logger

from utils.Constants import Constants
from utils.Util import Util
from utils.Config import Config


class VideoDownloader:
    @staticmethod
    def download_video(question_id, url, videos_dir):
        ydl_opts = {
            'outtmpl': f'{videos_dir}/{Util.qstr(question_id)}-%(id)s.%(ext)s',
            'format': 'bestvideo[height<=720]+bestaudio/best[height<=720]',
            'http_headers': {
                'Referer': Constants.LEETCODE_URL,
            }
        }

        # Download the video using yt-dlp
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            video_extension = info_dict.get('ext')
            video_filename = ydl.prepare_filename(info_dict)
            video_basename = os.path.basename(video_filename)

        return video_basename, video_extension
