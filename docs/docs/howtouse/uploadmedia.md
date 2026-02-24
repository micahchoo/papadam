# Uploading media

You can upload audio, video, and image files to any group you are a member of.

## How to upload

1. Open a group's archive page.
2. Click the **Upload Media** button on the left panel.
3. Fill in the form:
   - **Media Name** (required)
   - **Description** (required)
   - **Tags** (optional — comma-separated)
   - **File** (required — audio, video, or image)
4. Click **Submit**.

## What happens after upload

The file is uploaded to storage. For audio and video files, a background job starts
to transcode the file to HLS (adaptive bitrate streaming). A progress indicator shows
the job status: Queued, Converting, then Complete.

Once transcoding is complete, the modal closes automatically and the media appears in the archive.
Image files are stored directly with no transcoding step.

## Supported formats

Audio: MP3, OGG, WAV, M4A, FLAC, and others supported by ffmpeg.
Video: MP4, WebM, MKV, MOV, and others supported by ffmpeg.
Images: JPEG, PNG, GIF, WebP.

Audio and video files are converted to HLS for adaptive streaming.

## File size

Contact your instance admin for the configured upload limit (default: 500MB per file).

<!-- TODO(loop): Screenshots need recapturing from papadam UI (current images are from upstream papad Vue UI) -->
