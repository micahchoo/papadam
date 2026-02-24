# Annotating media

Annotations let you add commentary, responses, or context to any point in an audio or video file.
Annotations can be time-anchored to a specific segment.

## Adding an annotation

1. Open a media item.
2. Click **+ Create Annotation** to open the annotation form.
3. Set the **Start time** and **End time** for the segment this annotation covers.
   How you do this depends on your group's setting:
   - **Slider** (default) — drag two sliders along the timeline
   - **Timestamp (MM:SS)** — type start and end times in MM:SS format
   - **Tap to mark** — play the media and click **Set start** / **Set end** at the right moments
4. Choose an **Annotation type** (see below).
5. Fill in **Description** (required) and **Tags** (optional, comma-separated).
6. Click **Create Annotation**.

## Annotation types

| Type | Description |
|---|---|
| **Text** | Standard text annotation |
| **Image** | An image pinned to a segment — attach an image file |
| **Audio** | A spoken response — attach an audio file |
| **Video** | A video response — attach a video file |
| **Media Reference** | Links an existing archive item — enter its UUID |

Not all types may be enabled on every group — ask your group admin.

## Viewing annotations

All annotations for a media item are listed on the right side of the media page.
Each annotation shows:
- The time segment it covers (click the timestamp to jump the player to that segment)
- The annotation content (text, image, audio, video, or linked media)
- The username of the person who posted it

Replies appear indented under their parent annotation, each showing the author's username and the time posted.

## Deleting your own annotation

A **Delete** button appears under annotations you created.
Clicking Delete removes the annotation immediately — there is no confirmation dialog.
You can only delete your own annotations; you cannot delete annotations posted by others.

## Threaded replies

Any annotation can have replies. Click **Reply** on an annotation to open an inline reply form.
Type your reply and click **Post Reply**.
Replies appear indented under the parent annotation.

## Collaborative annotation

If multiple people are viewing the same media at the same time, annotations sync in real time
using CRDT (conflict-free replicated data). If you are offline, annotations are saved locally
and sync when you reconnect — no data is lost.

## Annotating audio

The same annotation form applies to audio files. The media player uses your browser's
native audio controls with skip forward / skip backward buttons.

<!-- TODO(loop): Screenshots need recapturing from papadam UI (current images are from upstream papad Vue UI) -->
