# Code Quality Review -- papadam monorepo

Date: 2026-03-12

---

## 1. Copy-Paste with Slight Variation

### 1a. Tag Add/Remove viewsets are near-identical across archive and annotate

Four viewsets share the same structure (queryset, serializer_class, permission_classes, lookup_field, get_object override, update method) with only the model/serializer/permission swapped:

- `MediaStoreAddTag` -- `/api/papadapi/archive/views.py:75-109`
- `MediaStoreRemoveTag` -- `/api/papadapi/archive/views.py:39-73`
- `AnnotationAddTag` -- `/api/papadapi/annotate/views.py:225-258`
- `AnnotationRemoveTag` -- `/api/papadapi/annotate/views.py:261-294`

Each is ~30 lines. A single generic `TagMixin` with `add`/`remove` actions would eliminate all four classes.

### 1b. StatsSerializer duplicated identically four times

`{created_date: DateField, total: IntegerField}` is defined as four separate classes:

- `MediaStatsSerializer` -- `/api/papadapi/archive/serializers.py:42-44`
- `AnnotationStatsSerializer` -- `/api/papadapi/annotate/serializers.py` (end of file)
- `GroupStatsSerializer` -- `/api/papadapi/common/serializers.py` (end of file)
- `UserStatsSerializer` -- `/api/papadapi/users/serializers.py` (end of file)

All four are byte-for-byte identical except for the class name.

### 1c. GroupTagSerializer duplicated across two files

Identical class defined in both:
- `/api/papadapi/common/serializers.py:41-44`
- `/api/papadapi/users/serializers.py:8-11`

### 1d. `extra_group_response` answer-building loop duplicated in create vs copy

The loop that iterates `extra_group_response["answers"]`, fetches each `Question`, and builds `group_extra_response` list appears twice with identical logic:

- `MediaStoreCreateSet.create` -- `/api/papadapi/archive/views.py:307-326`
- `MediaStoreCopySet.update` -- `/api/papadapi/archive/views.py:396-415`

### 1e. Search/filter query construction duplicated between media and annotation views

The `searchFrom` / `searchCollections` / anonymous-vs-authenticated group filtering logic is repeated with slight variation:

- `MediaStoreCreateSet.get_queryset` -- `/api/papadapi/archive/views.py:209-290`
- `AnnotationCreateSet.get_queryset` -- `/api/papadapi/annotate/views.py:43-109`

Both build the same `public_q | user_groups_q` pattern with identical branch structure for `all_collections`, `my_collections`, `public`, `selected_collections`.

### 1f. Instance*Stats / Group*Stats viewsets are structural clones

Three pairs of stats viewsets share the same `.values("id").annotate(created_date=TruncDate(...)).order_by(...).values(...).annotate(total=Count(...))` pattern:

- `InstanceMediaStats` / `GroupMediaStats` -- `/api/papadapi/archive/views.py:439-482`
- `InstanceAnnotationStats` / `GroupAnnotationStats` -- `/api/papadapi/annotate/views.py:319-368`
- `InstanceGroupStats` -- `/api/papadapi/common/views.py:361-379`

### 1g. Six Group-mutation viewsets with identical boilerplate

In `/api/papadapi/common/views.py`, these six classes all repeat `queryset = Group.objects.all()`, `serializer_class = UpdateGroupSerializer`, `pagination_class = CustomPageNumberPagination`, `permission_classes = [IsGroupOwnerMemberOrReadOnly]`, `lookup_field = "id"`, `lookup_url_kwarg = "id"`:

- `UpdateGroupViewSet` (line 148)
- `AddUserFromGroupView` (line 185)
- `RemoveUserFromGroupView` (line 211)
- `RemoveCustomQuestionFromGroupView` (line 247)
- `AddCustomQuestionFromGroupView` (line 282)
- `UpdateCustomQuestionFromGroupView` (line 324)

A single viewset with `@action` decorators would replace all six.

---

## 2. Redundant State / Redundant Queries

### 2a. `get_object()` immediately followed by `Model.objects.get()` on the same row

DRF's `get_object()` already returns the model instance (with permission checks). Re-fetching it is a wasted query:

- `/api/papadapi/archive/views.py:63-64` -- `obj = self.get_object(); m = MediaStore.objects.get(uuid=obj.uuid)`
- `/api/papadapi/archive/views.py:99-100` -- same pattern
- `/api/papadapi/archive/views.py:135-136` -- same pattern
- `/api/papadapi/archive/views.py:154-155` -- `obj = self.get_object(); m = MediaStore.objects.get(id=obj.id)`
- `/api/papadapi/archive/views.py:186-187` -- same pattern
- `/api/papadapi/annotate/views.py:248-249` -- `obj = self.get_object(); m = Annotation.objects.get(id=obj.id)`
- `/api/papadapi/annotate/views.py:284-285` -- same pattern
- `/api/papadapi/annotate/views.py:211-212` -- `perform_destroy` calls `get_object()` again (already called by DRF's `destroy`)
- `/api/papadapi/common/views.py:163-165` -- `obj = self.get_object(); g = Group.objects.get(id=obj.id)`
- `/api/papadapi/common/views.py:200-202` -- same
- `/api/papadapi/common/views.py:226-228` -- same
- `/api/papadapi/common/views.py:263-265` -- same
- `/api/papadapi/common/views.py:294-296` -- same
- `/api/papadapi/common/views.py:336-338` -- same

Every one of these is a redundant database hit.

### 2b. `get_object()` overrides that do nothing

Multiple viewsets override `get_object` only to call `super().get_object()` and return the result with a comment "perform some extra checks" but no actual checks:

- `/api/papadapi/archive/views.py:55-58`
- `/api/papadapi/archive/views.py:91-94`
- `/api/papadapi/archive/views.py:127-130`
- `/api/papadapi/annotate/views.py:166-168`
- `/api/papadapi/annotate/views.py:241-243`
- `/api/papadapi/annotate/views.py:277-279`

---

## 3. Stringly-Typed Code

### 3a. `media_processing_status` uses raw string literal instead of enum

The model defines `ProcessingStatus` TextChoices (`/api/papadapi/archive/models.py:37-51`), but the view uses a raw string:

- `/api/papadapi/archive/views.py:359` -- `m.media_processing_status = "Media unknown"` instead of `MediaStore.ProcessingStatus.MEDIA_UNKNOWN`

### 3b. `searchFrom` / `searchWhere` magic strings in views

Both media and annotation views branch on raw strings `"all_collections"`, `"my_collections"`, `"public"`, `"selected_collections"`, `"name"`, `"description"`, `"tags"` with no constants or enum:

- `/api/papadapi/archive/views.py:225-268`
- `/api/papadapi/annotate/views.py:53-100`

### 3c. Boolean-as-string comparisons

`data["copy_tags"] == "True"` and `data["copy_annotations"] == "True"` and `data["remove_existing_data"] == "True"` and `data["add_default_value"] == "True"` -- comparing string `"True"` instead of parsing to bool:

- `/api/papadapi/archive/views.py:425`
- `/api/papadapi/archive/views.py:430`
- `/api/papadapi/common/views.py:269`
- `/api/papadapi/common/views.py:304`

### 3d. Annotation type filter options as raw strings in UI

- `/ui/src/routes/annotations/+page.svelte:147-150` -- `<option value="text">`, `<option value="image">`, etc.
- `/ui/src/routes/annotations/+page.svelte:56` -- `params['annotation_type'] = filterType`
- `/ui/src/routes/groups/[id]/media/[slug]/+page.svelte:60` -- `a.annotation_type === 'image'`
- `/ui/src/routes/exhibits/[uuid]/edit/+page.svelte:398-400` -- `<option value="audio">`, etc.

No shared constant for annotation type values between API and UI.

### 3e. Task function names passed as strings to enqueue

- `/api/papadapi/archive/views.py:351-352` -- `enqueue_after("convert_to_hls", ...)`
- `/api/papadapi/archive/views.py:355-356` -- `enqueue_after("convert_to_hls_audio", ...)`
- `/api/papadapi/archive/views.py:159` -- `enqueue_after("delete_media_post_schedule", ...)`
- `/api/papadapi/annotate/views.py:217` -- `enqueue_after("delete_annotate_post_schedule", ...)`

These strings must match `WorkerSettings.functions` names exactly but have no compile-time or import-time validation.

---

## 4. Leaky Abstractions

### 4a. `MediaStoreTranscriptView` implements its own auth instead of using the permission system

- `/api/papadapi/archive/views.py:494-501` -- Sets `permission_classes = [AllowAny]` and `authentication_classes = []`, then manually checks `X-Internal-Key` header in the view body. This bypasses DRF's auth framework entirely, unlike the CRDT view which properly uses `CrdtServerTokenAuthentication`.

### 4b. `GroupViewSet.create` and `UpdateGroupViewSet.update` bypass serializer validation

- `/api/papadapi/common/views.py:107-145` -- `create` reads `data["name"]`, `data["description"]`, etc. directly from `request.data` and calls `Group.objects.create(...)` without running the serializer's `is_valid()`. Same for `update` at line 161-183.

### 4c. `MediaStoreCreateSet.create` does manual field assignment instead of using the serializer

- `/api/papadapi/archive/views.py:292-376` -- The entire create method manually extracts fields, creates the object, assigns file fields, and handles tags. The serializer is only used for the response, not for validation or creation.

---

## 5. Parameter Sprawl

### 5a. `get_queryset` methods with implicit parameter extraction

- `MediaStoreCreateSet.get_queryset` (`/api/papadapi/archive/views.py:209-290`) reads 4 query params (`search`, `searchWhere`, `searchFrom`, `searchCollections`) plus `mediaType`, then builds ~80 lines of branching logic. This filter-building should be extracted into a FilterSet or utility.

### 5b. `MediaStoreCreateSet.create` handles too many concerns

- `/api/papadapi/archive/views.py:292-376` -- file upload, name/description extraction, extra_group_response JSON parsing + question lookup, model creation, file assignment, tag parsing, HLS job dispatch, error cleanup. This 84-line method handles at least 6 distinct responsibilities.

---

## 6. Unnecessary Svelte Nesting

No significant issues found. The Svelte components use wrapper `<div>` elements appropriately for layout (flex containers, modal wrappers, card structures). No purely structural wrappers that add zero layout value were identified.

---

## Summary

| Category | Count | Severity |
|---|---|---|
| Copy-paste duplication | 7 findings | High -- 4 serializers, 4 tag viewsets, 6 group viewsets, 2 search filters |
| Redundant queries | 14 redundant `objects.get()` calls after `get_object()`, 6 no-op overrides | High -- each is a wasted DB round-trip |
| Stringly-typed code | 5 findings | Medium -- raw strings where enums/constants exist |
| Leaky abstractions | 3 findings | Medium -- bypassed serializer validation, manual auth |
| Parameter sprawl | 2 findings | Low -- large methods that need decomposition |
| Unnecessary Svelte nesting | None found | -- |
