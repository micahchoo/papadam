# Codebase Simplification Plan

**Date**: 2026-03-12
**Status**: Ready to execute
**Scope**: All remaining findings from full-codebase /simplify review

---

## Task 1: Consolidate 4 Stats Serializers → 1 `DailyStatsSerializer`

**Files**: `common/serializers.py`, `archive/serializers.py`, `annotate/serializers.py`, `users/serializers.py`
**Risk**: Low — rename + re-import

1. Add `DailyStatsSerializer` to `common/serializers.py` (identical body: `created_date = DateField(), total = IntegerField()`)
2. Delete `MediaStatsSerializer` from `archive/serializers.py`, replace import in `archive/views.py`
3. Delete `AnnotationStatsSerializer` from `annotate/serializers.py`, replace import in `annotate/views.py`
4. Delete `GroupStatsSerializer` from `common/serializers.py` (already there, just rename)
5. Delete `UserStatsSerializer` from `users/serializers.py`, replace import in `users/views.py`
6. Verify: `ruff check`, `python -c "import papadapi.common.serializers"`

---

## Task 2: Remove Duplicate `GroupTagSerializer` from `users/serializers.py`

**Files**: `users/serializers.py`, `users/views.py`
**Risk**: Low

1. Check if `GroupTagSerializer` in `users/serializers.py` is used anywhere — if only in that file, import from `common/serializers.py` instead
2. Delete the duplicate class
3. Verify imports

---

## Task 3: Deduplicate `get_tags` in `GroupSerializer` vs `UpdateGroupSerializer`

**Files**: `common/serializers.py`
**Risk**: Low

Both serializers define identical `get_tags()` methods. Extract to a standalone function or a mixin.

1. Create `_get_group_tags(group_id)` function in `common/serializers.py` (or `common/functions.py`)
2. Both `GroupSerializer.get_tags` and `UpdateGroupSerializer.get_tags` call it
3. Verify

---

## Task 4: Extract `build_extra_group_response()` helper

**Files**: `archive/views.py`
**Risk**: Low

The loop that iterates `extra_group_response["answers"]`, fetches each `Question`, and builds the response list appears in both `MediaStoreCreateSet.create` and `MediaStoreCopySet.update`.

1. Extract to `def build_extra_group_response(raw_json: str | list) -> list[dict]` in `common/functions.py`
2. Call from both create and copy views
3. Verify

---

## Task 5: Extract `build_group_filter()` for search querysets

**Files**: `archive/views.py`, `annotate/views.py`
**Risk**: Medium — both querysets have slight variations

Both `MediaStoreCreateSet.get_queryset` and `AnnotationCreateSet.get_queryset` build identical `searchFrom`/`searchCollections` group filter logic.

1. Create `build_group_filter(user, search_from, search_collections, group_param=None) -> Q` in `common/functions.py`
2. Replace the branching logic in both views with a call to this helper
3. The annotation view has an extra `?group=<id>` shorthand — handle via optional `group_param`
4. Verify both views still work via ruff + syntax check

---

## Task 6: Consolidate 4 Tag Add/Remove Viewsets → `TagMixin`

**Files**: `archive/views.py`, `annotate/views.py`
**Risk**: Medium — URL routing must stay identical

`MediaStoreAddTag`, `MediaStoreRemoveTag`, `AnnotationAddTag`, `AnnotationRemoveTag` share identical structure.

1. Create `TagAddMixin` and `TagRemoveMixin` in `common/views.py` (or `common/mixins.py`)
   - Parameterized by model class, serializer class, lookup field
   - `TagAddMixin.update()`: get object, iterate `data["tags"]`, call `create_or_update_tag`, add
   - `TagRemoveMixin.update()`: get object, iterate `data["tags"]`, get Tag by id, remove, recalculate
2. Rewrite the 4 viewsets as thin subclasses
3. Verify URL routing unchanged via `urls.py` inspection
4. Ruff check

---

## Task 7: Consolidate 6 Group-Mutation Viewsets

**Files**: `common/views.py`, `common/urls.py`
**Risk**: Medium — URL routing must stay identical

`UpdateGroupViewSet`, `AddUserFromGroupView`, `RemoveUserFromGroupView`, `RemoveCustomQuestionFromGroupView`, `AddCustomQuestionFromGroupView`, `UpdateCustomQuestionFromGroupView` all share identical boilerplate.

1. Create `GroupManagementViewSet` with `@action` decorators for each operation
2. Update `common/urls.py` to route to the new viewset's actions
3. Verify all URL paths produce the same endpoints
4. Ruff check

---

## Task 8: Fix Boolean-as-String Comparisons

**Files**: `archive/views.py`, `common/views.py`
**Risk**: Low — but must match what the frontend actually sends

4 locations compare `data["key"] == "True"` instead of parsing to bool.

1. Check what the frontend sends (multipart form data sends strings, JSON sends bools)
2. If form data: create `def parse_bool(val) -> bool` helper that handles `"True"`, `"true"`, `True`, `"1"`
3. Replace all 4 comparisons
4. Verify

---

## Task 9: `MediaStoreTranscriptView` — Proper DRF Auth

**Files**: `archive/views.py`
**Risk**: Low

Replace manual `X-Internal-Key` check with a proper DRF authentication class.

1. Create `InternalServiceKeyAuthentication(BaseAuthentication)` in `common/permissions.py` (or `common/authentication.py`)
2. `authenticate()` checks `X-Internal-Key` header against `settings.INTERNAL_SERVICE_KEY`
3. Returns `(None, "internal-service")` on success, raises `AuthenticationFailed` on failure
4. Set `authentication_classes = [InternalServiceKeyAuthentication]` and `permission_classes = [AllowAny]` on `MediaStoreTranscriptView`
5. Remove the manual key check from the view body

---

## Task 10: Fix `list(queryset)` → Subquery (4 locations)

**Files**: `common/views.py`, `common/serializers.py`, `annotate/views.py`
**Risk**: Low

`Annotation.objects.filter(media_reference_id__in=list(MediaStore.objects.filter(...)))` forces a full query evaluation. Use `.values_list("uuid", flat=True)` subquery instead.

1. Replace `list(MediaStore.objects.filter(group=X))` with `MediaStore.objects.filter(group=X).values_list("uuid", flat=True)` in:
   - `common/views.py` TagsViewSet.get (line ~71)
   - `common/views.py` GroupTagGraphView.retrieve (line ~396)
   - `common/serializers.py` get_tags method (line ~78)
   - `annotate/views.py` GroupAnnotationStats.retrieve (line ~341)
2. Verify

---

## Task 11: Extract Shared `_upload_hls_folder` + Remove TOCTOU

**Files**: `archive/tasks.py`, `annotate/tasks.py`
**Risk**: Medium

Both files have near-identical `_upload_hls_folder` with `stat_object` before `fput_object` (TOCTOU).

1. Move `_upload_hls_folder` to `common/storage.py`
2. Remove the `stat_object` check — just `fput_object` directly (idempotent overwrite)
3. Import from both task files
4. Verify

---

## Task 12: `annotation_structure` Reads JSON Inside Loop → Read Once

**Files**: `annotate/models.py`
**Risk**: Low

`Annotation.annotation_structure()` opens `annotation_structure.json` inside a `for d in data` loop.

1. Move the `open()` + `json.loads()` before the loop
2. Use `copy.deepcopy(ref_json)` inside the loop for each annotation
3. Verify

---

## Task 13: Events View Redis Pool Reuse

**Files**: `events/views.py`
**Risk**: Low

`_fetch_job_status` creates a new `aioredis.from_url()` connection per call.

1. Use a module-level connection pool or pass a shared pool
2. The pool should be created lazily on first use
3. Verify

---

## Task 14: Custom Question Views `media.save()` in Loop → `bulk_update`

**Files**: `common/views.py`
**Risk**: Low

`RemoveCustomQuestionFromGroupView`, `AddCustomQuestionFromGroupView`, `UpdateCustomQuestionFromGroupView` all call `media.save()` inside a loop over all group media.

1. Collect modified media objects in a list
2. Call `MediaStore.objects.bulk_update(modified, ["extra_group_response"])` once
3. Verify

---

## Task 15: `importexport/tasks.py` — Use `create_or_update_tag`

**Files**: `importexport/tasks.py`
**Risk**: Low

Import creates tags with `Tags.objects.create(name=tag_name)` directly instead of using the shared `create_or_update_tag` helper.

1. Find tag creation in importexport tasks
2. Replace with `from papadapi.common.functions import create_or_update_tag`
3. Verify

---

## Task 16: `use_can_access_group` in Archive/Annotate Permissions

**Files**: `archive/permissions.py`, `annotate/permissions.py`
**Risk**: Low

These permission classes duplicate the group membership check that `user_can_access_group` already handles.

1. Import `user_can_access_group` from `common/permissions.py`
2. Refactor `has_object_permission` to delegate to the shared helper
3. Verify

---

## Task 17: Minor UI Dedup — `AnnotationType` in crdt.ts

**Files**: `ui/src/lib/crdt.ts`, `ui/src/lib/api.ts`
**Risk**: Low

If `AnnotationType` is defined in both files, remove the duplicate and import from one canonical location.

1. Check if `AnnotationType` exists in both files
2. If so, keep in `api.ts`, import in `crdt.ts`
3. Verify with `npm run check` or `tsc --noEmit`

---

## Execution Order

**Wave 1** (independent, no cross-dependencies): Tasks 1, 2, 8, 9, 12, 13, 15, 16, 17
**Wave 2** (depends on Wave 1 helpers): Tasks 3, 4, 5, 10, 14
**Wave 3** (structural refactors): Tasks 6, 7, 11
