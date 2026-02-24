# Groups

Groups are the primary organisational unit. Each group has its own archive of media,
its own members, and its own settings.

## Browsing groups

Click **Collections** in the navigation bar to see available groups. Click a group card
to open its archive page, where you can view media, upload, and annotate.

## Creating a group

Groups are created by instance admins through the Django admin panel at `/nimda/`.
There is no self-service group creation in the frontend.

## Adding users to a group

User management is handled by instance admins through the admin panel.
Only admins can add or remove group members.

## Customising the workspace

Each group can be configured with its own look and feature set from the **Settings** page.
Click **Settings** in the navigation bar to:

- Set the instance name, logo, and brand colours
- Choose an interaction profile (standard, icon, voice, or high-contrast)
- Control which annotation types (images, audio, video, media references) are available
- Configure the media player skip intervals
- Enable or disable the exhibit builder

See [Customising your group's workspace](../admin/settings.md) for a full reference.

<!-- TODO(loop): Screenshots need recapturing from papadam UI (current images are from upstream papad Vue UI) -->
