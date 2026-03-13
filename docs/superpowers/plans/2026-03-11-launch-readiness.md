# papadam Launch Readiness — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make annotation solid end-to-end — validation, threading, visual polish, offline resilience — then deploy to a server for a real community.

**Architecture:** Six sequential work items. Items 1-2 (serializer + threading) are tightly coupled backend+frontend changes. Item 3 (visual overhaul) is a full CSS reskin using the frontend-design skill. Item 4 (service worker) is the largest item, broken into 4 sub-items that ship incrementally. Items 5-6 are deployment hardening and go-live.

**Tech Stack:** Python 3.12 / Django 4.2 / DRF / PostgreSQL 16 / pytest / SvelteKit 2 / Svelte 5 / Vitest / Playwright / Tailwind CSS / Workbox / Docker Compose / Caddy

**Spec:** `docs/superpowers/specs/2026-03-11-launch-readiness-design.md`

---

## Chunk 1: Serializer Validation + Reply Threading

### Task 1: Rewrite annotation serializer validation

**Files:**
- Modify: `api/papadapi/annotate/serializers.py` (full rewrite of AnnotationSerializer)
- Modify: `api/papadapi/annotate/views.py:97-158` (rewrite `create()` to use serializer)
- Modify: `api/papadapi/annotate/views.py:186-230` (rewrite `update()` to use serializer)
- Modify: `api/papadapi/media_relation/views.py:56-100` (rewrite `post()` to use serializer)
- Test: `api/papadapi/annotate/tests/test_create_update.py` (update existing + add new)
- Test: `api/papadapi/media_relation/tests/test_views.py` (add validation tests)

#### Step 1: Write failing tests for serializer validation

- [ ] **Step 1a: Write test for invalid reply_to returning 400**

Add to `api/papadapi/annotate/tests/test_create_update.py`:

```python
@pytest.mark.django_db
def test_create_nonexistent_reply_to_returns_400(member_client, member_media):
    """Non-existent reply_to must return 400, not silently set None."""
    resp = member_client.post(
        "/api/v1/annotate/",
        {
            "media_reference_id": str(member_media.uuid),
            "annotation_text": "orphan reply",
            "media_target": "t=0,5",
            "reply_to": "99999",
            "tags": "",
        },
        format="multipart",
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_create_malformed_reply_to_returns_400(member_client, member_media):
    """Non-numeric reply_to must return 400."""
    resp = member_client.post(
        "/api/v1/annotate/",
        {
            "media_reference_id": str(member_media.uuid),
            "annotation_text": "bad ref",
            "media_target": "t=0,5",
            "reply_to": "not-an-id",
            "tags": "",
        },
        format="multipart",
    )
    assert resp.status_code == 400
```

- [ ] **Step 1b: Write test for cross-group reply_to returning 400**

```python
@pytest.mark.django_db
def test_create_reply_to_different_group_returns_400(
    member_client, member_media, annotation
):
    """reply_to an annotation in a different group must return 400.
    `annotation` fixture is in `group`, not `group_with_member`."""
    resp = member_client.post(
        "/api/v1/annotate/",
        {
            "media_reference_id": str(member_media.uuid),
            "annotation_text": "cross-group reply",
            "media_target": "t=0,5",
            "reply_to": str(annotation.id),
            "tags": "",
        },
        format="multipart",
    )
    assert resp.status_code == 400
```

- [ ] **Step 1c: Write test for invalid media_ref_uuid returning 400**

```python
@pytest.mark.django_db
def test_create_nonexistent_media_ref_uuid_returns_400(member_client, member_media):
    """media_ref_uuid referencing a non-existent media must return 400."""
    resp = member_client.post(
        "/api/v1/annotate/",
        {
            "media_reference_id": str(member_media.uuid),
            "annotation_text": "bad ref",
            "media_target": "t=0,5",
            "annotation_type": "media_ref",
            "media_ref_uuid": "00000000-0000-0000-0000-000000000001",
            "tags": "",
        },
        format="multipart",
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_create_inaccessible_media_ref_uuid_returns_400(
    member_client, member_media, media
):
    """media_ref_uuid referencing media in another group must return 400.
    `media` fixture is in `group`, not `group_with_member`."""
    resp = member_client.post(
        "/api/v1/annotate/",
        {
            "media_reference_id": str(member_media.uuid),
            "annotation_text": "cross-group ref",
            "media_target": "t=0,5",
            "annotation_type": "media_ref",
            "media_ref_uuid": str(media.uuid),
            "tags": "",
        },
        format="multipart",
    )
    assert resp.status_code == 400
```

- [ ] **Step 1d: Write test for invalid annotation_type returning 400**

```python
@pytest.mark.django_db
def test_create_invalid_annotation_type_returns_400(member_client, member_media):
    """annotation_type not in valid choices must return 400."""
    resp = member_client.post(
        "/api/v1/annotate/",
        {
            "media_reference_id": str(member_media.uuid),
            "annotation_text": "note",
            "media_target": "t=0,5",
            "annotation_type": "bogus_type",
            "tags": "",
        },
        format="multipart",
    )
    assert resp.status_code == 400
```

- [ ] **Step 1e: Write test for valid create still returning 200/201**

```python
@pytest.mark.django_db
def test_create_with_valid_reply_to_and_media_ref(
    member_client, member_media, member_annotation, group_with_member
):
    """Valid reply_to (same group) and media_ref_uuid (accessible) → success."""
    # Create a second media in the same group for media_ref
    from papadapi.conftest import MediaStoreFactory

    ref_media = MediaStoreFactory(group=group_with_member)
    resp = member_client.post(
        "/api/v1/annotate/",
        {
            "media_reference_id": str(member_media.uuid),
            "annotation_text": "valid reply with ref",
            "media_target": "t=0,5",
            "annotation_type": "media_ref",
            "reply_to": str(member_annotation.id),
            "media_ref_uuid": str(ref_media.uuid),
            "tags": "",
        },
        format="multipart",
    )
    assert resp.status_code in (200, 201)
    ann = Annotation.objects.get(uuid=resp.data["uuid"])
    assert ann.reply_to_id == member_annotation.id
    assert str(ann.media_ref_uuid) == str(ref_media.uuid)
```

- [ ] **Step 1f: Run tests to verify they fail**

Run: `cd /mnt/Ghar/2TA/DevStuff/papad/papadam/api && python -m pytest papadapi/annotate/tests/test_create_update.py -v -k "nonexistent_reply_to or malformed_reply_to or different_group or nonexistent_media_ref or inaccessible_media_ref or invalid_annotation_type_returns" --no-header`
Expected: All new tests FAIL (200 instead of 400)

#### Step 2: Add validation to AnnotationSerializer

- [ ] **Step 2a: Add validate_reply_to and validate_media_ref_uuid to serializer**

Replace the full content of `api/papadapi/annotate/serializers.py`:

```python
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from rest_framework import serializers

from papadapi.annotate.models import Annotation
from papadapi.archive.models import MediaStore
from papadapi.common.models import Group
from papadapi.common.serializers import TagsSerializer
from papadapi.users.serializers import UserSerializer

if TYPE_CHECKING:
    pass

MAX_REPLY_DEPTH = 2  # 0-indexed: root=0, reply=1, reply-to-reply=2


def compute_depth(annotation: Annotation) -> int:
    """Walk reply_to chain, capped at MAX_REPLY_DEPTH + 1 hops."""
    depth = 0
    current = annotation
    while current.reply_to_id is not None and depth <= MAX_REPLY_DEPTH:
        current = Annotation.objects.select_related().get(pk=current.reply_to_id)
        depth += 1
    return depth


class AnnotationSerializer(serializers.ModelSerializer):
    tags = TagsSerializer(many=True, read_only=True)
    created_by = UserSerializer(read_only=True)
    annotation_type = serializers.ChoiceField(
        choices=Annotation.AnnotationType.choices,
        default=Annotation.AnnotationType.TEXT,
    )

    class Meta:
        model = Annotation
        fields = (
            "id",
            "annotation_text",
            "annotation_type",
            "tags",
            "media_reference_id",
            "media_target",
            "annotation_image",
            "annotation_audio",
            "annotation_video",
            "reply_to",
            "media_ref_uuid",
            "uuid",
            "created_at",
            "updated_at",
            "created_by",
        )
        read_only_fields = (
            "id",
            "uuid",
            "created_at",
            "updated_at",
            "created_by",
        )

    def validate_reply_to(self, value: Annotation | None) -> Annotation | None:
        if value is None:
            return None
        # Group comes from media_reference_id on the annotation being created.
        # At validation time, we check the parent annotation's group.
        if value.group is None:
            raise serializers.ValidationError(
                "Cannot reply to an annotation with no group."
            )
        # Check depth
        parent_depth = compute_depth(value)
        if parent_depth >= MAX_REPLY_DEPTH:
            raise serializers.ValidationError(
                f"Maximum reply depth ({MAX_REPLY_DEPTH}) exceeded."
            )
        return value

    def validate_media_ref_uuid(self, value: Any) -> Any:
        if value is None:
            return None
        try:
            media = MediaStore.objects.get(uuid=value)
        except MediaStore.DoesNotExist:
            raise serializers.ValidationError(
                "Referenced media does not exist."
            )
        # Access check: the requesting user must be in the media's group
        request = self.context.get("request")
        if request and request.user and not request.user.is_anonymous:
            user_groups = Group.objects.filter(users=request.user)
            if media.group not in user_groups:
                raise serializers.ValidationError(
                    "You do not have access to the referenced media."
                )
        return value

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """Cross-field: reply_to must be in the same group as the target media."""
        reply_to = attrs.get("reply_to")
        media_ref_id = attrs.get("media_reference_id")
        if reply_to and media_ref_id:
            try:
                target_media = MediaStore.objects.get(uuid=media_ref_id)
            except MediaStore.DoesNotExist:
                raise serializers.ValidationError(
                    {"media_reference_id": "Target media does not exist."}
                )
            if reply_to.group_id != target_media.group_id:
                raise serializers.ValidationError(
                    {"reply_to": "Reply must be to an annotation in the same group."}
                )
        return attrs


class AnnotationStatsSerializer(serializers.Serializer):
    created_date = serializers.DateField()
    total = serializers.IntegerField()
```

- [ ] **Step 2b: Run tests to check new validation passes**

Run: `cd /mnt/Ghar/2TA/DevStuff/papad/papadam/api && python -m pytest papadapi/annotate/tests/test_create_update.py -v --no-header -x`
Expected: New tests still fail (view bypasses serializer), but serializer code compiles.

**Note on CRDT persistence bridge:** The spec requires enforcing validation in the CRDT persistence path. After code review, the CRDT bridge (`api/papadapi/crdt/views.py`) only stores binary Y.js state (`state_vector` bytes) — it does **not** write normalized `Annotation` rows. Normalized annotations are created exclusively through the REST API (`/api/v1/annotate/` and `/api/v1/media-relation/replies/`). Therefore, adding validation to the serializer covers all Annotation creation paths. No CRDT-specific changes needed.

#### Step 3: Rewrite create() to use serializer

- [ ] **Step 3a: Rewrite AnnotationCreateSet.create()**

Replace lines 97-158 of `api/papadapi/annotate/views.py`:

```python
    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = AnnotationSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        m = serializer.save(
            created_by=cast("User", request.user),
        )

        # File fields — assigned after create so upload_to functions run
        changed = False
        for field_name in ("annotation_image", "annotation_audio", "annotation_video"):
            f = request.FILES.get(field_name)
            if f:
                setattr(m, field_name, f)
                changed = True
        if changed:
            m.save()

        # Enqueue HLS transcoding for audio/video reply files
        if request.FILES.get("annotation_audio"):
            enqueue("transcode_annotation_audio", m.id)
        if request.FILES.get("annotation_video"):
            enqueue("transcode_annotation_video", m.id)

        # Tags — comma-separated string
        for tag in request.data.get("tags", "").split(","):
            tag = tag.strip()
            if tag:
                tag_obj = create_or_update_tag(tag)
                if tag_obj:
                    m.tags.add(tag_obj)

        return Response(AnnotationSerializer(m).data)
```

- [ ] **Step 3b: Update the existing test that expects silent ignore to expect 400**

In `test_create_update.py`, update `test_create_invalid_reply_to_is_ignored` (lines 108-124):

```python
@pytest.mark.django_db
def test_create_invalid_reply_to_returns_400(member_client, member_media):
    """Malformed reply_to must return 400."""
    resp = member_client.post(
        "/api/v1/annotate/",
        {
            "media_reference_id": str(member_media.uuid),
            "annotation_text": "note",
            "media_target": "t=0,5",
            "reply_to": "not-an-id",
            "tags": "",
        },
        format="multipart",
    )
    assert resp.status_code == 400
```

- [ ] **Step 3c: Run all annotation tests**

Run: `cd /mnt/Ghar/2TA/DevStuff/papad/papadam/api && python -m pytest papadapi/annotate/tests/ -v --no-header`
Expected: All tests pass. If any fail, fix before proceeding.

- [ ] **Step 3d: Commit**

```bash
cd /mnt/Ghar/2TA/DevStuff/papad/papadam
git add api/papadapi/annotate/serializers.py api/papadapi/annotate/views.py api/papadapi/annotate/tests/test_create_update.py
git commit -m "feat(annotate): rewrite create to use serializer, add reply_to + media_ref_uuid validation

Annotation creation now goes through AnnotationSerializer.is_valid()
instead of bypassing it. reply_to validates existence, same-group, and
depth. media_ref_uuid validates existence and user access."
```

#### Step 4: Rewrite update() to use serializer

- [ ] **Step 4a: Rewrite AnnotationRetreiveSet.update()**

Replace lines 186-230 of `api/papadapi/annotate/views.py`:

```python
    def update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        instance = self.get_object()
        serializer = AnnotationSerializer(
            instance, data=request.data, partial=True, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        m = serializer.save()

        # Tags — comma-separated string replaces existing set
        if "tags" in request.data:
            for tag in m.tags.all():
                m.tags.remove(tag)
                recalculate_tag_count(tag)
            for tag_name in request.data["tags"].split(","):
                tag_name = tag_name.strip()
                if tag_name:
                    tag_obj = create_or_update_tag(tag_name)
                    if tag_obj:
                        m.tags.add(tag_obj)

        # File fields
        changed = False
        for field_name in ("annotation_image", "annotation_audio", "annotation_video"):
            f = request.FILES.get(field_name)
            if f:
                setattr(m, field_name, f)
                changed = True
        if changed:
            m.save()

        return Response(AnnotationSerializer(m).data, status=status.HTTP_200_OK)
```

- [ ] **Step 4b: Run all annotation tests**

Run: `cd /mnt/Ghar/2TA/DevStuff/papad/papadam/api && python -m pytest papadapi/annotate/tests/ -v --no-header`
Expected: PASS

- [ ] **Step 4c: Commit**

```bash
cd /mnt/Ghar/2TA/DevStuff/papad/papadam
git add api/papadapi/annotate/views.py
git commit -m "refactor(annotate): rewrite update() to use serializer validation"
```

#### Step 5: Rewrite media_relation reply creation to use serializer

- [ ] **Step 5a: Write failing test for depth limit in replies endpoint**

Create or update `api/papadapi/media_relation/tests/test_views.py`:

```python
@pytest.mark.django_db
def test_reply_at_max_depth_returns_400(member_client, member_annotation, member_media):
    """Creating a reply at depth > MAX_REPLY_DEPTH must return 400."""
    # member_annotation is depth 0 (root)
    # Create depth 1 reply
    resp1 = member_client.post(
        f"/api/v1/media-relation/replies/{member_annotation.uuid}/",
        {"annotation_text": "depth-1 reply"},
        format="json",
    )
    assert resp1.status_code == 201
    depth1_uuid = resp1.data["uuid"]

    # Create depth 2 reply (reply to the reply)
    resp2 = member_client.post(
        f"/api/v1/media-relation/replies/{depth1_uuid}/",
        {"annotation_text": "depth-2 reply"},
        format="json",
    )
    assert resp2.status_code == 201
    depth2_uuid = resp2.data["uuid"]

    # Depth 3 should be rejected
    resp3 = member_client.post(
        f"/api/v1/media-relation/replies/{depth2_uuid}/",
        {"annotation_text": "depth-3 reply — too deep"},
        format="json",
    )
    assert resp3.status_code == 400
```

- [ ] **Step 5b: Rewrite AnnotationRepliesView.post() to use serializer**

Replace lines 56-100 of `api/papadapi/media_relation/views.py`:

```python
    def post(self, request: Request, annotation_uuid: str) -> Response:
        parent = self._get_parent(annotation_uuid)
        if parent is None:
            return Response(
                {"detail": "Annotation not found."}, status=status.HTTP_404_NOT_FOUND
            )

        # Build data dict with parent context defaults
        data = {
            "media_reference_id": request.data.get(
                "media_reference_id", parent.media_reference_id
            ),
            "annotation_text": request.data.get("annotation_text", ""),
            "media_target": request.data.get("media_target", ""),
            "annotation_type": request.data.get("annotation_type", "text"),
            "reply_to": parent.pk,
        }
        serializer = AnnotationSerializer(data=data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        reply = serializer.save(
            group=parent.group,
            created_by=cast("UserModel", request.user),
        )

        if "tags" in request.data:
            from papadapi.common.functions import create_or_update_tag

            for tag in request.data["tags"].split(","):
                tag_name = tag.strip()
                if tag_name:
                    reply.tags.add(create_or_update_tag(tag_name))

        log.info(
            "reply_annotation_created",
            parent_uuid=str(parent.uuid),
            reply_uuid=str(reply.uuid),
        )
        serializer = AnnotationSerializer(reply)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
```

- [ ] **Step 5c: Run all tests**

Run: `cd /mnt/Ghar/2TA/DevStuff/papad/papadam/api && python -m pytest papadapi/annotate/tests/ papadapi/media_relation/tests/ -v --no-header`
Expected: PASS

- [ ] **Step 5d: Run full backend check suite**

Run: `cd /mnt/Ghar/2TA/DevStuff/papad/papadam/api && python -m pytest --no-header && ruff check . && mypy papadapi/ && lint-imports`
Expected: All green

- [ ] **Step 5e: Commit**

```bash
cd /mnt/Ghar/2TA/DevStuff/papad/papadam
git add api/papadapi/media_relation/views.py api/papadapi/media_relation/tests/
git commit -m "feat(media_relation): route reply creation through serializer, enforce depth limit

MAX_REPLY_DEPTH = 2 (3 levels: root → reply → reply-to-reply).
Replies to annotations at max depth return 400."
```

### Task 2: Frontend reply threading (3 levels deep)

**Files:**
- Modify: `ui/src/lib/components/AnnotationViewer.svelte` (recursive thread rendering)
- Modify: `ui/src/lib/api.ts` (add MAX_REPLY_DEPTH constant)
- Test: `ui/src/lib/api.test.ts` (add threading tests)

#### Step 1: Add depth constant to frontend

- [ ] **Step 1a: Add MAX_REPLY_DEPTH to api.ts**

Add after the `AnnotationType` definition (around line 89 of `ui/src/lib/api.ts`):

```typescript
/** Maximum reply nesting depth (0-indexed: root=0, reply=1, reply-to-reply=2). */
export const MAX_REPLY_DEPTH = 2;
```

- [ ] **Step 1b: Commit**

```bash
cd /mnt/Ghar/2TA/DevStuff/papad/papadam
git add ui/src/lib/api.ts
git commit -m "feat(ui): add MAX_REPLY_DEPTH constant"
```

#### Step 2: Rewrite AnnotationViewer for recursive threading

- [ ] **Step 2a: Rewrite AnnotationViewer.svelte**

Key changes to `ui/src/lib/components/AnnotationViewer.svelte`:

1. Make `allRepliesFor()` work recursively — it already returns replies for a given parent. The template needs to recurse.

2. Add a `depth` parameter to the annotation rendering. At `depth >= MAX_REPLY_DEPTH`, hide the Reply button.

3. Show "Replying to {username}" context on nested replies.

Replace the `<ul>` reply rendering block (lines 221-235) with a recursive `{#snippet}`:

```svelte
{#snippet annotationThread(annotation: Annotation & { timeParts?: [number, number] | null }, depth: number)}
  <li class="my-2 mb-5 rounded bg-white p-4 shadow-sm" style:margin-left="{depth * 1.5}rem">
    <!-- ... existing annotation rendering (type badge, timestamp, media body, text, author) ... -->

    <div class="mt-2 flex gap-3">
      {#if depth < MAX_REPLY_DEPTH}
        <button
          class="text-xs text-blue-600 hover:underline"
          onclick={() => toggleReplyForm(annotation.id)}
        >
          {expandedReplyFor === annotation.id ? 'Cancel' : 'Reply'}
        </button>
      {/if}
      <!-- delete button -->
    </div>

    <!-- reply form (only if depth < MAX_REPLY_DEPTH) -->

    <!-- Recursive children -->
    {#if allRepliesFor(annotation.id).length > 0}
      <ul class="mt-3 space-y-2 border-l-2 border-gray-200 pl-4">
        {#each allRepliesFor(annotation.id) as reply}
          {@render annotationThread({ ...reply, timeParts: getTimeParts(reply.media_target) }, depth + 1)}
        {/each}
      </ul>
    {/if}
  </li>
{/snippet}
```

Then the root rendering becomes:
```svelte
{#each rootAnnotations as annotation}
  {@render annotationThread(annotation, 0)}
{/each}
```

Import `MAX_REPLY_DEPTH` at the top:
```typescript
import { MAX_REPLY_DEPTH } from '$lib/api';
```

- [ ] **Step 2b: Run frontend checks**

Run: `cd /mnt/Ghar/2TA/DevStuff/papad/papadam/ui && npm run check && npm run lint && npm test`
Expected: All pass

- [ ] **Step 2c: Commit**

```bash
cd /mnt/Ghar/2TA/DevStuff/papad/papadam
git add ui/src/lib/components/AnnotationViewer.svelte
git commit -m "feat(ui): recursive reply threading up to MAX_REPLY_DEPTH levels

AnnotationViewer now renders the full reply tree with indentation.
Reply button hidden at max depth. Each reply shows parent context."
```

#### Step 3: Clean up unused imports in views.py

- [ ] **Step 3a: Remove contextlib import from views.py if no longer used**

Check `api/papadapi/annotate/views.py` — the `contextlib.suppress` was the only use. Remove the import.

- [ ] **Step 3b: Run ruff + mypy**

Run: `cd /mnt/Ghar/2TA/DevStuff/papad/papadam/api && ruff check . && mypy papadapi/`
Expected: Clean

- [ ] **Step 3c: Commit**

```bash
cd /mnt/Ghar/2TA/DevStuff/papad/papadam
git add api/papadapi/annotate/views.py
git commit -m "chore: remove unused contextlib import"
```

---

## Chunk 2: Visual Overhaul — Newspaper Aesthetic + Full API Wiring

### Task 3: Visual overhaul + API wiring (6 feature slices)

**This task combines the newspaper aesthetic reskin with wiring all remaining API functions into the UI. Each feature slice ships a complete, newspaper-styled surface. Uses `superpowers:brainstorming` followed by `frontend-design` skill for the visual design.**

**Wiring spec:** Section 3 of `docs/superpowers/specs/2026-03-11-launch-readiness-design.md`

**Files affected:**
- Modify: `ui/src/app.css` (global typography, color tokens, newspaper palette)
- Modify: `ui/src/lib/api.ts` (remove dead exports: `crdt.loadState`, `crdt.saveState`, `auth.refresh`)
- Modify: `ui/src/lib/api.test.ts` (remove tests for deleted exports)
- Modify: `ui/src/routes/+layout.svelte` (layout shell, navigation)
- Modify: `ui/src/routes/+page.svelte` (media list / archive front page)
- Modify: `ui/src/routes/groups/+page.svelte` (group selector, Load More error fix)
- Modify: `ui/src/routes/groups/[id]/+page.svelte` (export button in header, Load More error fix)
- Modify: `ui/src/routes/groups/[id]/media/[slug]/+page.svelte` ("See also" marginalia, annotation error fix)
- Modify: `ui/src/routes/exhibits/+page.svelte` (exhibit viewer, Load More error fix)
- Modify: `ui/src/routes/settings/+page.svelte` (group management + import/export sections)
- Modify: `ui/src/lib/components/AnnotationViewer.svelte` (editorial style, lazy reply loading, inline tag chips, edit trigger)
- Modify: `ui/src/lib/components/NavBar.svelte` (masthead navigation, "Annotations" link)
- Modify: `ui/src/lib/components/MediaPlayer.svelte` (player styling, Phase 5 waveform comment)
- Modify: `ui/src/lib/components/SearchSort.svelte` (search bar styling, Media/Annotations toggle)
- Modify: `ui/src/lib/components/UploadAnnotationModal.svelte` (wire `timeRangeInputMode` store)
- Create: `ui/src/lib/components/EditAnnotationModal.svelte` (edit annotation modal)
- Create: `ui/src/lib/components/EditAnnotationModal.test.ts` (unit tests)
- Create: `ui/src/routes/annotations/+page.svelte` (global annotation browser)
- Test: existing Vitest + wiring-lint tests must still pass; new tests for new components

#### Steps

- [ ] **Step 1: Invoke frontend-design skill for mockups**

Use the `superpowers:brainstorming` skill to explore the newspaper aesthetic direction, then use `frontend-design` skill (if available) for detailed mockups and implementation guidance. Mockups should include the new UI surfaces: `/annotations` route, settings group management section, import/export section, "See also" marginalia, inline tag chips, edit annotation modal.

- [ ] **Step 2: Implement typography foundation**

Add serif heading font (e.g., `Merriweather` or `Playfair Display`) and sans-serif body font to `app.css`. Set up Tailwind `fontFamily` extensions. Establish 3+ size levels for headings.

- [ ] **Step 3: Wiring Slice 1 — Dead export cleanup**

Remove `crdt.loadState`, `crdt.saveState`, `auth.refresh` from `api.ts`. Remove corresponding tests from `api.test.ts`. Wire `timeRangeInputMode` store in `UploadAnnotationModal.svelte` (branch on slider/timestamp/tap). Add Phase 5 waveform comment in `MediaPlayer`.

- [ ] **Step 4: Restyle media list as newspaper front page**

Column/grid layout. Prominent thumbnails, headline (media name), byline (uploader), date. Dense but readable.

- [ ] **Step 5: Restyle navigation as newspaper masthead**

Brand name prominent. UIConfig brand colors in masthead. Minimal chrome. Add "Annotations" nav link between "Collections" and "Exhibits" (auth-gated).

- [ ] **Step 6: Wiring Slice 2 — Reply fetching + cross-media marginalia**

Wire `mediaRelation.replies` into `AnnotationViewer.svelte`: lazy-load replies on expand, recursive to depth 3, inline spinner per thread, "Couldn't load replies" with retry on error. Wire `mediaRelation.mediaRefs` into media detail page: "See also" sidebar (desktop) / section (mobile), newspaper marginalia style. Empty = don't render. **Depends on Chunk 1 (Task 2) completing the recursive AnnotationViewer rewrite first.**

- [ ] **Step 7: Restyle annotation panel as editorial marginalia**

Annotations alongside media, not below. Typography-driven separation. Thread indentation using rules (thin lines) not boxes. Integrates with the reply fetching from Step 6.

- [ ] **Step 8: Wiring Slice 3 — Tag management + Edit annotation modal**

Inline tag chips on `AnnotationViewer`: removable chips (removeTag), "+" autocomplete dropdown (tags.list, addTag), optimistic UI, auth-gated. New `EditAnnotationModal.svelte`: pencil icon trigger, fetches via `annotations.get`, pre-fills fields, submits via `annotations.update`, respects `timeRangeInputMode`, cannot change annotation type. Write `EditAnnotationModal.test.ts`.

- [ ] **Step 9: Wiring Slice 4 — Group management in settings + import/export**

Settings page: "Collections" section with `groups.list`, inline edit (`groups.update`), delete with confirmation (`groups.delete`), create form (`groups.create`). Export button on `/groups/[id]` header (`importexport.requestExport`). Import/Export section in settings: file upload (`importexport.requestImport`), request table (`importexport.listRequests`), auto-refresh polling.

- [ ] **Step 10: Wiring Slice 5 — Global annotations route + enhanced search**

New `/annotations/+page.svelte`: `annotations.list` with pagination, filters (group, search, type, tag), newspaper "letters" archive style. Enhanced `SearchSort`: "Media" | "Annotations" toggle, calls `annotations.list` when annotations tab active.

- [ ] **Step 11: Restyle exhibit viewer as feature spread**

Magazine-style layout. Full-width media, editorial captions.

- [ ] **Step 12: Wiring Slice 6 — Silent failure fixes**

Replace 4 silent catch blocks with inline error + retry: `groups/+page.svelte` Load More, `groups/[id]/+page.svelte` Load More, `exhibits/+page.svelte` Load More, `groups/[id]/media/[slug]/+page.svelte` annotation fetch.

- [ ] **Step 13: Verify acceptance criteria**

Run:
```bash
cd /mnt/Ghar/2TA/DevStuff/papad/papadam/ui
npm run lint    # wiring-lint: no hardcoded colors
npm run check   # svelte-check
npm test        # all tests pass (existing + new)
```

Verify:
- Zero unwired API exports in `api.ts`
- `timeRangeInputMode` consumed in annotation time input UI
- `/annotations` route renders and paginates
- Group CRUD works from `/settings`
- Import/export request flow works end-to-end
- All 4 silent catch blocks replaced with inline error + retry

- [ ] **Step 14: Commit**

```bash
cd /mnt/Ghar/2TA/DevStuff/papad/papadam
git add ui/
git commit -m "feat(ui): newspaper aesthetic + full API wiring

Typography-driven layout with serif headings, column grid for media list,
editorial marginalia for annotations, masthead navigation with brand tokens.

Wires all remaining API functions: group CRUD in settings, import/export flow,
inline tag management, edit annotation modal, global annotations route,
cross-media 'See also' marginalia, enhanced search toggle, lazy reply loading.

Removes dead exports (crdt.loadState/saveState, auth.refresh). Fixes 4 silent
catch blocks with inline error + retry."
```

---

## Chunk 3: Service Worker — Offline Resilience

### Task 4a: SPA shell precache with Workbox

**Files:**
- Create: `ui/src/service-worker.ts` (Workbox service worker)
- Modify: `ui/vite.config.js` (add workbox plugin or manual SW registration)
- Modify: `ui/src/routes/+layout.svelte` (register service worker)
- Test: `ui/src/service-worker.test.ts`

#### Steps

- [ ] **Step 1: Install Workbox**

Run: `cd /mnt/Ghar/2TA/DevStuff/papad/papadam/ui && npm install workbox-precaching workbox-routing workbox-strategies workbox-expiration workbox-background-sync`

Note: SvelteKit has built-in service worker support via `src/service-worker.ts`. Check SvelteKit docs for the right approach — may not need a vite plugin.

- [ ] **Step 2: Create service worker with precache**

Create `ui/src/service-worker.ts`:

```typescript
/// <reference types="@sveltejs/kit" />
import { build, files, version } from '$service-worker';
import { precacheAndRoute } from 'workbox-precaching';

// Precache all build output (JS, CSS) and static files
const precacheEntries = [...build, ...files].map((url) => ({
  url,
  revision: version,
}));

precacheAndRoute(precacheEntries);
```

**Note:** SvelteKit 2 automatically registers a service worker when `src/service-worker.ts` exists. Do NOT add manual registration in `+layout.svelte` — that would cause double registration.

- [ ] **Step 3: Build and verify SW is included**

Run: `cd /mnt/Ghar/2TA/DevStuff/papad/papadam/ui && npm run build && ls build/service-worker.js`
Expected: File exists

- [ ] **Step 5: Commit**

```bash
cd /mnt/Ghar/2TA/DevStuff/papad/papadam
git add ui/src/service-worker.ts ui/package.json ui/package-lock.json
git commit -m "feat(ui): add service worker with SPA shell precache

App loads even when fully offline. Workbox precaches all build output.
SvelteKit auto-registers the SW — no manual registration needed."
```

### Task 4b: Runtime media cache

**Files:**
- Modify: `ui/src/service-worker.ts` (add runtime caching strategies)

#### Steps

- [ ] **Step 1: Add runtime cache for media assets**

Add to `ui/src/service-worker.ts`:

```typescript
import { registerRoute } from 'workbox-routing';
import { StaleWhileRevalidate, NetworkFirst } from 'workbox-strategies';
import { ExpirationPlugin } from 'workbox-expiration';

// HLS segments, thumbnails, images — stale-while-revalidate with LRU cap
registerRoute(
  ({ url }) =>
    url.pathname.match(/\.(ts|m3u8|jpg|jpeg|png|gif|webp|svg|mp3|mp4|webm)$/i) !== null,
  new StaleWhileRevalidate({
    cacheName: 'media-cache',
    plugins: [
      new ExpirationPlugin({
        maxEntries: 200,
        maxAgeSeconds: 7 * 24 * 60 * 60, // 7 days
      }),
    ],
  })
);

// API responses — network-first with cached fallback for offline
registerRoute(
  ({ url }) => url.pathname.startsWith('/api/'),
  new NetworkFirst({
    cacheName: 'api-cache',
    plugins: [
      new ExpirationPlugin({
        maxEntries: 100,
        maxAgeSeconds: 24 * 60 * 60, // 1 day
      }),
    ],
  })
);
```

- [ ] **Step 2: Build and verify**

Run: `cd /mnt/Ghar/2TA/DevStuff/papad/papadam/ui && npm run build`
Expected: Builds without error

- [ ] **Step 3: Commit**

```bash
cd /mnt/Ghar/2TA/DevStuff/papad/papadam
git add ui/src/service-worker.ts
git commit -m "feat(ui): runtime media + API caching in service worker

Stale-while-revalidate for media assets (200 entry LRU, 7d TTL).
Network-first for API responses with 1d cached fallback for offline."
```

### Task 4c: Offline upload queue

**Files:**
- Create: `ui/src/lib/upload-queue.ts` (IndexedDB queue + Background Sync registration)
- Create: `ui/src/lib/upload-queue.test.ts` (unit tests)
- Modify: `ui/src/service-worker.ts` (Background Sync handler)
- Modify: `ui/src/lib/api.ts` (wrap upload methods to use queue on failure)
- Modify: `ui/src/lib/components/UploadMediaModal.svelte` (show queue status)

#### Steps

- [ ] **Step 1: Write failing tests for upload queue**

Create `ui/src/lib/upload-queue.test.ts`:

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';

// Tests for the upload queue module — queue add, list, retry, discard
describe('upload-queue', () => {
  it('adds an upload to the queue', async () => {
    // Test: queue.add({ url, method, body }) → stored in IndexedDB
  });

  it('lists queued uploads with status', async () => {
    // Test: queue.list() returns [{ id, url, status, createdAt }]
  });

  it('discards a queued upload', async () => {
    // Test: queue.discard(id) → removed from IndexedDB
  });

  it('retries a failed upload', async () => {
    // Test: queue.retry(id) → re-registers Background Sync
  });
});
```

- [ ] **Step 2: Add Background Sync to service worker**

Workbox `BackgroundSyncPlugin` handles the actual queuing and retry. Add to `ui/src/service-worker.ts`:

```typescript
import { BackgroundSyncPlugin } from 'workbox-background-sync';
import { NetworkOnly } from 'workbox-strategies';

const uploadSyncPlugin = new BackgroundSyncPlugin('upload-queue', {
  maxRetentionTime: 7 * 24 * 60, // 7 days in minutes
});

// POST requests to upload endpoints: network-only with background sync retry
registerRoute(
  ({ url }) =>
    url.pathname.startsWith('/api/v1/annotate/') ||
    url.pathname.startsWith('/api/v1/archive/'),
  new NetworkOnly({ plugins: [uploadSyncPlugin] }),
  'POST'
);
```

- [ ] **Step 3: Implement upload queue UI status layer**

Create `ui/src/lib/upload-queue.ts` — this reads from Workbox's internal IndexedDB (`workbox-background-sync` store) to surface queue status to the UI. It does NOT maintain a parallel queue — Workbox owns the actual queuing and retry. This module only provides:
- `getQueuedUploads()` — reads pending entries from Workbox's IndexedDB
- `discardUpload(id)` — removes an entry from Workbox's queue
- Queue status events for the UI (pending count, sync success/failure)

- [ ] **Step 4: Add queue status UI to UploadMediaModal**

Show pending/syncing/failed count. Retry/discard buttons for failed items.

- [ ] **Step 5: Run tests**

Run: `cd /mnt/Ghar/2TA/DevStuff/papad/papadam/ui && npm test && npm run check && npm run lint`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
cd /mnt/Ghar/2TA/DevStuff/papad/papadam
git add ui/src/lib/upload-queue.ts ui/src/lib/upload-queue.test.ts ui/src/service-worker.ts ui/src/lib/api.ts ui/src/lib/components/UploadMediaModal.svelte
git commit -m "feat(ui): offline upload queue with Background Sync

Failed uploads queued in IndexedDB, retried via Background Sync API.
Queue status visible in upload modal with retry/discard controls."
```

### Task 4d: Auth token resilience

**Files:**
- Modify: `ui/src/service-worker.ts` (token refresh before replay)
- Modify: `ui/src/lib/api.ts` (store refresh token accessible to SW)
- Test: `ui/src/lib/upload-queue.test.ts` (add auth refresh tests)

#### Steps

- [ ] **Step 1: Write failing test for token refresh on replay**

Add to `ui/src/lib/upload-queue.test.ts`:

```typescript
it('refreshes auth token before replaying queued requests', async () => {
  // Test: when a queued request is replayed, if the access token is expired,
  // refresh it using the stored refresh token before sending
});

it('surfaces login prompt when refresh token is also expired', async () => {
  // Test: if refresh also fails (401), emit an event to show login UI
});
```

- [ ] **Step 2: Implement token refresh in service worker**

In the Background Sync `onSync` callback, check if the access token is expired. If so, call the refresh endpoint. If refresh fails, mark the queue item as `auth_expired` and surface to the UI.

- [ ] **Step 3: Run tests**

Run: `cd /mnt/Ghar/2TA/DevStuff/papad/papadam/ui && npm test`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
cd /mnt/Ghar/2TA/DevStuff/papad/papadam
git add ui/src/service-worker.ts ui/src/lib/api.ts ui/src/lib/upload-queue.test.ts
git commit -m "feat(ui): auth token refresh before replaying queued uploads

Service worker refreshes expired JWT before Background Sync replay.
If refresh token is also expired, surfaces login prompt to user."
```

### Task 4e: E2E offline test

**Files:**
- Create: `ui/tests/offline.spec.ts` (Playwright E2E)

#### Steps

- [ ] **Step 1: Write Playwright offline test**

Create `ui/tests/offline.spec.ts`:

```typescript
import { test, expect } from '@playwright/test';

test('app loads offline after initial visit', async ({ page, context }) => {
  // Visit the app online to populate SW cache
  await page.goto('/');
  await page.waitForLoadState('networkidle');

  // Go offline
  await context.setOffline(true);

  // Reload — should load from SW cache
  await page.reload();
  await expect(page.locator('body')).not.toBeEmpty();
  // Check the page rendered something meaningful (not a browser error)
  await expect(page).not.toHaveTitle(/cannot be reached/i);
});
```

- [ ] **Step 2: Run E2E tests**

Run: `cd /mnt/Ghar/2TA/DevStuff/papad/papadam/ui && npm run test:e2e`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
cd /mnt/Ghar/2TA/DevStuff/papad/papadam
git add ui/tests/offline.spec.ts
git commit -m "test(e2e): verify app loads offline after initial visit"
```

---

## Chunk 4: Deployment Hardening + Deploy

### Task 5: Enhance seed_prod with env-configurable group settings

**Files:**
- Modify: `api/papadapi/users/management/commands/seed_prod.py`
- Test: `api/papadapi/users/tests/test_seed_prod.py` (create if needed)

#### Steps

- [ ] **Step 1: Write test for seed_prod env vars**

Create `api/papadapi/users/tests/test_seed_prod.py`:

```python
import os
from unittest.mock import patch

import pytest
from django.core.management import call_command

from papadapi.common.models import Group, UIConfig


@pytest.mark.django_db
def test_seed_prod_creates_group_from_env():
    """seed_prod uses SEED_GROUP_NAME and SEED_GROUP_LANGUAGE."""
    env = {
        "ADMIN_PASSWORD": "testpass123",
        "SEED_GROUP_NAME": "TestVillage",
        "SEED_GROUP_LANGUAGE": "kn",
        "SEED_BRAND_NAME": "Village Archive",
        "SEED_BRAND_PRIMARY": "#2d5a27",
        "SEED_BRAND_ACCENT": "#e6a817",
    }
    with patch.dict(os.environ, env):
        call_command("seed_prod")

    group = Group.objects.get(name="TestVillage")
    uiconfig = UIConfig.objects.get(group=group)
    assert uiconfig.language == "kn"
    assert uiconfig.brand_name == "Village Archive"
    assert uiconfig.primary_color == "#2d5a27"
    assert uiconfig.accent_color == "#e6a817"


@pytest.mark.django_db
def test_seed_prod_idempotent():
    """Running seed_prod twice does not duplicate."""
    env = {"ADMIN_PASSWORD": "testpass123"}
    with patch.dict(os.environ, env):
        call_command("seed_prod")
        call_command("seed_prod")
    assert Group.objects.filter(name="Community").count() == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /mnt/Ghar/2TA/DevStuff/papad/papadam/api && python -m pytest papadapi/users/tests/test_seed_prod.py -v --no-header`
Expected: FAIL (seed_prod creates "Instance", not "Community", and ignores SEED_ vars)

- [ ] **Step 3: Update seed_prod to read SEED_ env vars**

Modify `api/papadapi/users/management/commands/seed_prod.py`:

```python
        # ── Instance group ────────────────────────────────────────────────────
        group_name = os.environ.get("SEED_GROUP_NAME", "Community")
        group, created = Group.objects.get_or_create(
            name=group_name,
            defaults={"is_public": False, "is_active": True},
        )
        if created:
            logger.info("created_group", name=group_name)
            self.stdout.write(f"  created group '{group_name}'")
        else:
            self.stdout.write(f"  skip group '{group_name}' (already exists)")

        group.users.add(admin)

        # ── UIConfig ──────────────────────────────────────────────────────────
        # Note: Group post_save signal auto-creates UIConfig with model defaults.
        # Use update_or_create to apply SEED_ overrides regardless.
        uiconfig, created = UIConfig.objects.update_or_create(
            group=group,
            defaults={
                "language": os.environ.get("SEED_GROUP_LANGUAGE", "en"),
                "brand_name": os.environ.get("SEED_BRAND_NAME", group_name),
                "primary_color": os.environ.get("SEED_BRAND_PRIMARY", "#1e3a5f"),
                "accent_color": os.environ.get("SEED_BRAND_ACCENT", "#d97706"),
            },
        )
        if created:
            logger.info("created_uiconfig", group=group_name)
            self.stdout.write(f"  created UIConfig for {group_name} group")
        else:
            logger.info("updated_uiconfig", group=group_name)
            self.stdout.write(f"  updated UIConfig for {group_name} group")
```

- [ ] **Step 4: Run tests**

Run: `cd /mnt/Ghar/2TA/DevStuff/papad/papadam/api && python -m pytest papadapi/users/tests/test_seed_prod.py -v --no-header`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd /mnt/Ghar/2TA/DevStuff/papad/papadam
git add api/papadapi/users/management/commands/seed_prod.py api/papadapi/users/tests/test_seed_prod.py
git commit -m "feat(seed_prod): configurable group name, language, brand via SEED_ env vars

SEED_GROUP_NAME, SEED_GROUP_LANGUAGE, SEED_BRAND_NAME, SEED_BRAND_PRIMARY,
SEED_BRAND_ACCENT read from environment. Defaults to sensible values."
```

### Task 6: Add restart policies to Docker Compose

**Files:**
- Modify: `deploy/docker-compose.yml`

#### Steps

- [ ] **Step 1: Verify restart policies already present**

All services in `deploy/docker-compose.yml` already have `restart: unless-stopped`. Verify this is the case and that no service is missing it. (`minio-init` is a one-shot container and intentionally has no restart policy.)

- [ ] **Step 2: Add SEED_ env vars to service_config.env.sample**

Add to `deploy/service_config.env.sample`:

```env
# ── Seed data (used by `manage.py seed_prod`) ─────────────────────────────
# SEED_GROUP_NAME=Community
# SEED_GROUP_LANGUAGE=en
# SEED_BRAND_NAME=Community Archive
# SEED_BRAND_PRIMARY=#1e3a5f
# SEED_BRAND_ACCENT=#d97706
```

- [ ] **Step 3: Commit**

```bash
cd /mnt/Ghar/2TA/DevStuff/papad/papadam
git add deploy/docker-compose.yml deploy/service_config.env.sample
git commit -m "ops: add restart policies + SEED_ env vars to compose stack"
```

### Task 7: Deployment verification checklist (manual)

This task is a manual checklist, not automated code. Execute on the target server.

- [ ] **Step 1:** Clone repo, copy and configure `deploy/service_config.env`
- [ ] **Step 2:** `docker compose --profile webserver --profile minio --profile backup up -d`
- [ ] **Step 3:** Wait for healthchecks: `docker compose ps` — all services "healthy"
- [ ] **Step 4:** Run `docker compose exec api python manage.py seed_prod`
- [ ] **Step 5:** Run seed_prod again — verify idempotent (no errors, no duplicates)
- [ ] **Step 6:** Smoke test: upload media → wait for HLS transcode → annotate → reply → verify CRDT sync in second tab
- [ ] **Step 7:** Kill a container: `docker kill papadam-api` → verify it restarts within 30s
- [ ] **Step 8:** Verify Caddy HTTPS: `curl -I https://DOMAIN/healthcheck/`
- [ ] **Step 9:** Backup test: `docker compose exec backup /backup.sh` → wipe postgres → restore → verify data
- [ ] **Step 10:** (Optional) Whisper: upload audio → verify VTT appears in player
