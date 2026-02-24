# Uploading media

You can upload audio and video files to any group you are a member of.

## How to upload

1. Open a group's archive page.
2. Click the **Upload** button.
3. Fill in the form:
   - **Name** (required)
   - **Description** (optional)
   - **Tags** (optional — comma-separated)
   - **File** (required — audio or video)
4. Click **Upload**.

![Upload form](/static/uploadmedia/onSubmit.png)

## What happens after upload

The file is uploaded to storage and a background job starts to transcode it to HLS
(adaptive bitrate streaming). A progress indicator shows the job status.

Once transcoding is complete, the media is available in the group archive for playback and annotation.

![Upload complete](/static/uploadmedia/postUpload.png)

## Supported formats

Audio: MP3, OGG, WAV, M4A, FLAC, and others supported by ffmpeg.
Video: MP4, WebM, MKV, MOV, and others supported by ffmpeg.

All files are converted to HLS for adaptive streaming.

## File size

Contact your instance admin for the configured upload limit (default: 500MB per file).
