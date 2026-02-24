# Exhibits

An exhibit is a curated, ordered presentation built from items in the archive.
Published exhibits are publicly viewable — no login required to view.

Exhibits must be enabled for your group before this feature appears.
If you do not see **Exhibits** in the navigation bar, ask your group admin to enable it
in **Settings → Features → Enable exhibit builder**.

---

## Creating an exhibit

You must have a group selected first. Open **Collections**, pick a group,
then come back to **Exhibits**.

1. Click **Exhibits** in the navigation bar.
2. Click **New Exhibit**.
3. Fill in:
   - **Title** (required)
   - **Description** (optional)
   - **Public exhibit** — tick to make it viewable without login
4. Click **Create**.

The exhibit is added to the list. Click **Edit** next to it to open the exhibit editor.

---

## Adding items

Each item in an exhibit is a **block**. Blocks are displayed in the order they were added.

1. Open an exhibit and click **Edit**.
2. Scroll to the **Add Block** section.
3. Choose a block type:
   - **Media** — a media item from the archive (audio, video, or image)
   - **Annotation** — a specific annotation from a media item
4. For **Media** blocks: use the search box to filter by name, then select an item
   from the dropdown. If no media has been uploaded to the group yet, enter the UUID manually.
   For **Annotation** blocks: enter the annotation UUID.
5. Optionally add a **Caption** — text shown beneath the block.
6. Click **Add Block**.

The block is added to the end of the list and appears immediately.

---

## Reordering blocks

Each block in the list has ▲ and ▼ buttons on the left.
Click ▲ to move a block one position up, ▼ to move it one position down.
The first block's ▲ and the last block's ▼ are disabled.
The new order saves to the server automatically.

---

## Removing a block

Click **Remove** next to any block to delete it from the exhibit.
The block is removed immediately. The original media or annotation in the archive is not affected.

---

## Editing an exhibit

From the exhibit list, click **Edit** next to an exhibit.

- Update the **Title**, **Description**, or **Public exhibit** toggle.
- Click **Save**. A green "Saved." message confirms success.

---

## Deleting an exhibit

On the edit page, scroll to **Danger Zone** and click **Delete Exhibit**.
A confirmation dialog appears before anything is removed.
This removes the exhibit and all its blocks permanently.
The original media and annotations in the archive are not affected.

---

## Viewing a published exhibit

Anyone with the exhibit URL can view a public exhibit without logging in.
Members of the exhibit's group can view private exhibits after logging in.

From the exhibit list, click **View** to open the published view.

---

## What goes wrong

**"Exhibits" is not in the navigation bar**

The exhibit builder is disabled for this group.
Ask your group admin to enable it: **Settings → Features → Enable exhibit builder**.

**"Select a collection first (visit Collections)"**

You do not have an active group selected. Open **Collections**, click a group, then return to **Exhibits** and try again.

**"Failed to add block. Check that the UUID exists."**

The UUID you entered does not match any media item or annotation.
Copy the UUID directly from the media item's detail page URL.
