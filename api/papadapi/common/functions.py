from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from django.contrib.auth.models import AnonymousUser  # noqa: TCH002
from django.db.models import Q

from papadapi.annotate.models import Annotation
from papadapi.archive.models import MediaStore
from papadapi.common.models import Group, Question, Tags

if TYPE_CHECKING:
    from papadapi.users.models import User


def build_extra_group_response(raw_data: str | list | dict) -> list[dict[str, Any]]:
    """Parse extra_group_response JSON and expand Question details for each answer."""
    parsed = json.loads(raw_data) if isinstance(raw_data, str) else raw_data

    if not parsed:
        return []

    answers = parsed.get("answers", []) if isinstance(parsed, dict) else []
    if not answers:
        return []

    result: list[dict[str, Any]] = []
    for answer in answers:
        q = answer["question_id"]
        question = Question.objects.get(id=q)
        if question:
            result.append(
                {
                    "question_id": q,
                    "question": question.question,
                    "question_type": question.question_type,
                    "question_mandatory": question.question_mandatory,
                    "response": answer["response"],
                }
            )
    return result


def build_group_filter(
    user: User | AnonymousUser,
    search_from: str | None,
    search_collections: str | None,
    group_param: str | None = None,
) -> Q:
    """Build a Q filter for group-based access control.

    Shared by archive and annotation search views.  The ``group_param``
    argument supports the annotation view's ``?group=<id>`` shorthand.
    """
    public_q = Q(group__in=Group.objects.filter(is_public=True, is_active=True))

    if user.is_anonymous:
        if (
            search_from == "selected_collections"
            and search_collections is not None
        ):
            group_list = search_collections.split(",")
            return Q(group__in=Group.objects.filter(id__in=group_list))
        # anonymous: default / all_collections / public all resolve to public
        return public_q

    # Authenticated user
    my_q = Q(group__in=Group.objects.filter(users__in=[user]))

    if search_from == "all_collections":
        return public_q | my_q
    if search_from == "my_collections":
        return my_q
    if search_from == "public":
        return public_q
    if search_from == "selected_collections" and search_collections is not None:
        group_list = search_collections.split(",")
        return Q(group__in=Group.objects.filter(id__in=group_list))

    # No explicit search_from — check for ?group=<id> shorthand
    if group_param:
        return Q(
            group_id=group_param,
            group__in=Group.objects.filter(users__in=[user])
            | Group.objects.filter(is_public=True, is_active=True),
        )

    # Default for authenticated users: all accessible collections
    return public_q | my_q


def is_truthy(val: Any) -> bool:
    """Parse a form-data boolean (string "True"/"true"/"1" or actual bool)."""
    if isinstance(val, bool):
        return val
    return str(val).lower() in ("true", "1", "yes")


def recalculate_tag_count(tag_instance: Tags) -> None:
    tag_count = (
        MediaStore.objects.filter(tags__id=tag_instance.id).count()
        + Annotation.objects.filter(tags__id=tag_instance.id).count()
    )
    # INFO: Explicitly handles the case where the tag is newly created and not
    # yet mapped to any media — set count to 1 to get started.
    if tag_count == 0:
        tag_instance.count = 1
    else:
        tag_instance.count = tag_count
    tag_instance.save()


def get_final_tags_count(
    media_tags_count: list[dict[str, Any]],
    annotation_tags_count: list[dict[str, Any]],
    count: bool = False,
) -> list[dict[str, Any]]:
    data: dict[Any, dict[str, Any]] = {}
    for val in media_tags_count + annotation_tags_count:
        key = val["tag_id"] if count else val["id"]

        if key in data:
            if count:
                data[key]['count'] = data[key]['count'] + val['count']
            else:
                data[key]['value'] = data[key]['symbolSize'] + val['symbolSize']
                data[key]['symbolSize'] = (
                    data[key]['value'] if data[key]['value'] > 8 else 8
                )
                if data[key]['tag_in'] and val['tag_in']:
                    data[key]["category"] = 2
                elif data[key]['tag_in'] and not val['tag_in']:
                    data[key]["category"] = 0
                else:
                    data[key]["category"] = 1
        else:
            data[key] = val
            if not count:
                data[key]['value'] = data[key]['symbolSize']
                data[key]['symbolSize'] = (
                    data[key]['value'] if data[key]['value'] > 8 else 8
                )
    return list(data.values())


def get_related_tags(
    group: int | str,
    tag: int,
    links: list[dict[str, int]],
    media: bool = True,
    annotation: bool = True,
) -> list[dict[str, int]]:
    tag_obj = Tags.objects.filter(id=tag).first()
    group_obj = Group.objects.filter(id=group).first()
    if media and tag_obj and group_obj:
        related_tags = MediaStore.objects.filter(
            group=group_obj, tags=tag_obj
        ).distinct()
        return [
            {"source": tag, "target": rts_tag.id}
            for rts in related_tags
            for rts_tag in rts.tags.all()
            if tag != rts_tag.id
        ]
    return []


def create_or_update_tag(tag: str) -> Tags | None:
    tag_value = tag.lower().strip()
    if tag_value:
        t = Tags.objects.get_or_create(name=tag_value)[0]
        recalculate_tag_count(t)
        return t
    else:
        return None
