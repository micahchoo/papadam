from __future__ import annotations

from typing import Any

from papadapi.annotate.models import Annotation
from papadapi.archive.models import MediaStore
from papadapi.common.models import Group, Tags


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
