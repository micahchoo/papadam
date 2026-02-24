# Annotating media

Annotations let you add commentary, responses, or context to any point in an audio or video file.
Annotations can be time-anchored to a specific segment.

## Adding an annotation

1. Open a media item.
2. Play the media and note the start and end time of the segment you want to annotate.
3. Click **Annotate** to open the annotation form.
4. Fill in:
   - **Start time / End time** — the segment this annotation refers to (click at the right moment during playback to capture the time)
   - **Annotation text** (required)
   - **Tags** (optional)
5. Click **Upload**.

![Annotation page](/static/annotate/annotatePage.png)

![Annotation form](/static/annotate/mandatoryFields.png)

## Annotation types

| Type | Description |
|---|---|
| **Text** | Standard text annotation |
| **Image** | An image pinned to a segment — displayed as an overlay during playback |
| **Audio reply** | A spoken response — transcoded and playable inline |
| **Video reply** | A video response — transcoded and playable inline |
| **Media reference** | Links an existing archive item as a reply |

Not all types may be enabled on every group — ask your group admin.

## Threaded replies

Any annotation can have replies. Click **Reply** on an annotation to add your response.
Replies can also be time-anchored and can use any annotation type.

This creates a dialogue thread across the archive — a community member's story can accumulate
text replies, voice replies, and video responses from multiple contributors.

## Viewing annotations

All annotations for a media item are listed below the player, grouped by time segment.
Replies appear indented under their parent annotation.

![Annotation submitted](/static/annotate/AnnoSuccess.png)

## Annotating audio

The same form applies to audio files. The media player shows the waveform and playback position.

![Audio annotation page](/static/annotate/AudioAnnoPage.png)

## Collaborative annotation

If multiple people are viewing the same media at the same time, annotations sync in real time
using CRDT (conflict-free replicated data). If you are offline, annotations are saved locally
and sync when you reconnect — no data is lost.
