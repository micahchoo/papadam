# Customising your group's workspace

The Settings page lets you change how papadam looks and behaves for your community.
Changes take effect immediately — no restart, no rebuild.

## Getting there

Log in, then click **Settings** in the navigation bar.
You must be logged in to access this page.

---

## Branding

| Field | What it does |
|---|---|
| **Instance name** | The name shown in the page title and navigation bar |
| **Logo URL** | A public image URL displayed as the header logo. Leave blank for no logo. |
| **Primary colour** | Main colour for buttons and header backgrounds — pick from the colour wheel |
| **Accent colour** | Highlight colour for links and focus rings |

Changes to colours apply immediately in your browser without a page reload.

---

## Interface

| Field | What it does |
|---|---|
| **Interaction profile** | `Standard` — text-based desktop UI. `Icon` — pictogram-first for low-literacy use. `Voice` — mic-first, annotation starts by recording. `High contrast` — WCAG AAA contrast ratios, larger text. |
| **Colour scheme** | `Default`, `Warm`, `Cool`, or `High contrast` — tints the whole UI |
| **Language** | BCP 47 language tag for the interface language (`en`, `kn`, `hi`, `ta`, etc.) |
| **Font scale** | Drag to increase text size. 1.0× is default. 1.4–1.8× for low-vision accessibility. |
| **Icon set** | Leave as `default`, or enter a MinIO URL pointing to a custom icon sprite |

---

## Accessibility

| Toggle | What it does |
|---|---|
| **Enable voice interaction** | Makes a microphone button always accessible for voice-first communities |
| **Offline-first mode** | Prioritises offline storage and background sync (coming in a future release) |

---

## Player

| Field | What it does |
|---|---|
| **Skip backward / Skip forward** | How many seconds the skip buttons jump — drag each slider (5–60 s) |
| **Default quality** | Starting bitrate for HLS streams: `Auto` adapts to the viewer's connection speed |
| **Show waveform** | Display an audio waveform under the player (coming in a future release) |
| **Show transcript** | Display Whisper captions below the player (coming in a future release) |

---

## Annotations

| Field | What it does |
|---|---|
| **Time range input** | How members mark the start/end of a segment: `Slider`, `Timestamp (MM:SS)`, or `Tap to mark` |
| **Images** | Allow image annotations pinned to a time segment |
| **Audio clips** | Allow voice reply annotations |
| **Video clips** | Allow video reply annotations |
| **Media references** | Allow linking an existing archive item as a reply |

Unchecking a type removes that option from the annotation form for everyone in the group.

---

## Features

| Toggle | What it does |
|---|---|
| **Enable exhibit builder** | Shows the Exhibits section in navigation. Uncheck to hide it from members. |

---

## Saving

Click **Save settings**. The button shows "Saving…" while the request is in flight.
A green confirmation appears when the save succeeds.

## What if it fails?

A red error message appears at the top of the form.
Check your connection and try again. If the error persists, log out and back in — your session may have expired.
