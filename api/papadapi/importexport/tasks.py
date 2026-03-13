"""
importexport/tasks.py — ARQ background tasks for the importexport app.

The export/import business logic is synchronous (heavy file I/O, Django ORM
queries, tarfile operations).  Each ARQ task wraps its sync body in
asyncio.to_thread so the worker event-loop is not blocked.
"""

from __future__ import annotations

import asyncio
import json
import os
import tarfile
import uuid
from typing import Any

import requests
import structlog
from django.core.files import File

from papadapi.annotate.models import Annotation
from papadapi.archive.models import MediaStore
from papadapi.common.functions import create_or_update_tag
from papadapi.common.models import Group
from papadapi.importexport.models import IERequest

log = structlog.get_logger(__name__)


# ── sync helpers (unchanged from legacy — violations are pre-existing debt) ───


def download(url: str, file_name: str, files_path: str) -> str:
    file_name = file_name.split("/")[1]
    with open(os.path.join(files_path, file_name), "wb") as file:
        response = requests.get(url, timeout=120)
        file.write(response.content)
    return file_name


def export_annotation(
    files_path: str, annotation: Annotation,
) -> tuple[str | None, dict[str, Any]]:
    annotation_data: dict[str, Any] = {}
    annotation_data[str(annotation.uuid)] = {
        "annotation_text": annotation.annotation_text,
        "media_target": annotation.media_target,
    }
    annotation_tags = ""
    for tags in annotation.tags.all():
        annotation_tags += tags.name + ","
    annotation_data[str(annotation.uuid)]["tags"] = annotation_tags
    if annotation.annotation_image:
        annotation_file = download(
            annotation.annotation_image.url,
            annotation.annotation_image.name,
            files_path,
        )
        annotation_data[str(annotation.uuid)]["annotation_image"] = annotation_file
        return annotation_file, annotation_data
    else:
        return None, annotation_data


def export_media(
    files_path: str, media_instance: MediaStore,
) -> tuple[list[str | None], dict[str, Any]]:
    media_file_list: list[str | None] = []
    media_data: dict[str, Any] = {}
    media_data["name"] = media_instance.name
    media_data["description"] = media_instance.description
    media_file = download(
        media_instance.upload.url, media_instance.upload.name, files_path
    )
    media_data["media_file_name"] = media_file
    media_file_list.append(media_file)
    media_tags = ""
    for tags in media_instance.tags.all():
        media_tags += tags.name + ","
    media_data["tags"] = media_tags
    annotations = Annotation.objects.filter(
        is_delete=False, media_reference_id=media_instance.uuid
    )
    if len(annotations) > 0:
        media_data["annotations"] = {}
        for annotation in annotations:
            media_data["annotations"][str(annotation.uuid)] = {}
            annotation_file, annotation_data = export_annotation(files_path, annotation)
            media_file_list.append(annotation_file)
            media_data["annotations"].update(annotation_data)
    return media_file_list, media_data


def import_annotation(
    files_path: str, annovals: dict[str, Any], media: MediaStore,
) -> bool:
    from papadapi.annotate.serializers import AnnotationSerializer

    data: dict[str, Any] = {
        "annotation_text": annovals.get("annotation_text", ""),
        "media_target": annovals.get("media_target", ""),
        "media_reference_id": str(media.uuid),
        "annotation_type": annovals.get("annotation_type", "text"),
    }
    reply_to = annovals.get("reply_to")
    if reply_to is not None:
        data["reply_to"] = reply_to

    serializer = AnnotationSerializer(data=data)
    if not serializer.is_valid():
        log.warning("import_annotation_validation_failed", errors=serializer.errors)
        return False

    image_name = annovals.get("annotation_image")
    if image_name:
        annotation_file_name = os.path.join(files_path, image_name)
        try:
            with open(annotation_file_name, "rb") as f:
                instance = serializer.save(group=media.group)
                instance.annotation_image.save(image_name, File(file=f), save=True)
        except FileNotFoundError:
            log.warning("import_annotation_image_missing", path=annotation_file_name)
            return False
    else:
        serializer.save(group=media.group)
    return True


def import_media(files_path: str, media_data: dict[str, Any], group: Group) -> bool:
    media_file_name = os.path.join(files_path, media_data["media_file_name"])
    with open(media_file_name, "rb") as f:
        media = MediaStore.objects.create(
            name=media_data["name"],
            description=media_data["description"],
            uuid=uuid.uuid4(),
            group=group,
            upload=File(file=f),
        )
    for tag in media_data["tags"].split(","):
        tag_obj = create_or_update_tag(tag)
        if tag_obj:
            media.tags.add(tag_obj)
    if "annotations" in media_data:
        for annovals in media_data["annotations"].values():
            import_annotation(files_path, annovals, media)
    return True


def extract_json_for_import(
    files_path: str, import_data: object,
) -> dict[str, Any] | None:
    jsondata: dict[str, Any] = {}
    tarfilename = download(import_data.url, import_data.name, files_path)  # type: ignore[attr-defined]
    if tarfile.is_tarfile(tarfilename):
        with tarfile.open(tarfilename, "r") as file_obj:
            file_obj.extractall(filter="data")
        with open("data.json") as f:
            jsondata = json.load(f)
        return jsondata or None
    return None


# ── sync task bodies ──────────────────────────────────────────────────────────


def _export_sync(request_id: int) -> bool:
    export = IERequest.objects.get(id=request_id)
    export_metadata = export.ie_metadata
    requested_by = export.requested_by
    export_requested_type = export_metadata["type"]
    export_requested_id = export_metadata["id"]
    request_uuid = str(export.request_id)
    media_file_list = []
    files_path = os.path.abspath(os.path.join(os.getcwd(), "export", request_uuid))
    if not os.path.isdir(files_path):
        os.makedirs(files_path, exist_ok=True)
    proceed_upload = False
    is_proceed = False

    if export_requested_type == "group":
        export_data = {}
        try:
            group = Group.objects.get(id=export_requested_id)
            is_proceed = True
        except Group.DoesNotExist:
            export.is_complete = True
            export.detail = "Requested group does not exist"
            export.save()
        if is_proceed:
            export_data["group"] = {
                "group_name": group.name,
                "group_visibility": group.is_public,
                "group_description": group.description,
            }
            if requested_by in group.users.all() or group.is_public:
                media_data: dict[str, Any] = {}
                for data in MediaStore.objects.filter(group=group):
                    data_id = str(data.uuid)
                    media_data[data_id] = {}
                    media_files, media_data[data_id] = export_media(files_path, data)
                    media_file_list += media_files
                    proceed_upload = True
            else:
                export.is_complete = True
                export.detail = "Not authorized to run export on the requested group"
                export.save()

    elif export_requested_type == "archive":
        export_data = {}
        media_id = export_metadata["id"]
        try:
            media = MediaStore.objects.get(uuid=media_id)
            is_proceed = True
        except MediaStore.DoesNotExist:
            export.is_complete = True
            export.detail = "Requested Media does not exist"
            export.save()
        if is_proceed:
            group = media.group
            if requested_by in group.users.all() or group.is_public or media.is_public:
                media_data = {}
                media_data[str(media.uuid)] = {}
                media_files, media_data[str(media.uuid)] = export_media(
                    files_path, media
                )
                media_file_list += media_files
                proceed_upload = True
            else:
                export.is_complete = True
                export.detail = (
                    "Not authorized to run export on the requested media, "
                    "as user is not a part of the group"
                )
                export.save()

    elif export_requested_type == "annotation":
        export_data = {}
        annotation_id = export_metadata["id"]
        is_proceed = False
        try:
            annotation = Annotation.objects.get(uuid=annotation_id)
            is_proceed = True
        except Annotation.DoesNotExist:
            export.is_authorized = True
            export.is_complete = True
            export.detail = "Annotation does not exist"
            export.save()
        if is_proceed:
            media = MediaStore.objects.get(uuid=annotation.media_reference_id)
            group = media.group
            if requested_by in group.users.all() or group.is_public or media.is_public:
                media_data = {}
                media_data["annotation"] = {}
                media_files, media_data["annotation"] = export_annotation(  # type: ignore[assignment]
                    files_path, annotation
                )
                if media_files:
                    media_file_list.append(media_files)  # type: ignore[arg-type]
                proceed_upload = True
            else:
                export.is_complete = True
                export.detail = (
                    "Not authorized to run export on the requested annotation, "
                    "as user is not a part of the group"
                )
                export.save()
    else:
        export.is_complete = True
        export.detail = "Unknown request. Not doing anything"
        export.save()

    if proceed_upload:
        cwd = os.getcwd()
        os.chdir(files_path)
        export_data["archive"] = media_data
        with open("data.json", "w") as outfile:
            json.dump(export_data, outfile)

        with tarfile.open(request_uuid + ".tar", "w") as fileobj:
            fileobj.add("data.json")
            fileobj.list()
            for mfl in media_file_list:
                if mfl is not None:
                    fileobj.add(mfl)

        with open(request_uuid + ".tar", "rb") as fp:
            export.requested_file.save(request_uuid + ".tar", File(fp))
        os.chdir(cwd)

        export.is_authorized = True
        export.is_complete = True
        export.detail = "Request completed"
        export.save()
    return True


def _import_sync(request_id: int) -> bool:
    importreq = IERequest.objects.get(id=request_id)
    importreq_metadata = json.loads(importreq.ie_metadata)
    requested_by = importreq.requested_by
    importreq_requested_type = importreq_metadata["type"]
    request_uuid = str(importreq.request_id)
    files_path = os.path.abspath(os.path.join(os.getcwd(), "import", request_uuid))
    if not os.path.isdir(files_path):
        os.makedirs(files_path, exist_ok=True)
    cwd = os.getcwd()
    os.chdir(files_path)

    if importreq_requested_type == "group":
        jsonfile = extract_json_for_import(files_path, importreq.requested_file)
        if jsonfile:
            group_details = jsonfile["group"]
            group_name = (
                importreq_metadata["name"]
                if "name" in importreq_metadata
                else group_details["group_name"]
            )
            group_description = (
                importreq_metadata["description"]
                if "description" in importreq_metadata
                else group_details["group_description"]
            )
            group_visibility = (
                importreq_metadata["is_public"]
                if "is_public" in importreq_metadata
                else group_details["group_visibility"]
            )
            group = Group.objects.create(
                name=group_name,
                description=group_description,
                is_public=group_visibility,
                is_active=True,
            )
            group.users.add(requested_by)
            group.delete_wait_for = 7
            group.save()

            media_details = jsonfile["archive"]
            for media_data in media_details.values():
                import_media(files_path, media_data, group)
        else:
            importreq.is_complete = True
            importreq.detail = "Upload data corrupt. Unable to import"
            importreq.save()

    elif importreq_requested_type == "archive":
        group_into = importreq_metadata["import_into_group"]
        group = Group.objects.get(id=group_into)
        if group and requested_by in group.users.all():
            jsonfile = extract_json_for_import(files_path, importreq.requested_file)
            if jsonfile:
                media_details = jsonfile["archive"]
                for media_data in media_details.values():
                    import_media(files_path, media_data, group)
            else:
                importreq.is_complete = True
                importreq.detail = "Upload data corrupt. Unable to import"
                importreq.save()

    elif importreq_requested_type == "annotation":
        media_into = importreq_metadata["import_for_media"]
        media = MediaStore.objects.get(uuid=media_into)
        group = media.group
        if group and requested_by in group.users.all():
            jsonfile = extract_json_for_import(files_path, importreq.requested_file)
            if jsonfile:
                annotation_details = jsonfile["archive"]["annotation"]
                for annotation_detail in annotation_details.values():
                    import_annotation(files_path, annotation_detail, media)
            else:
                importreq.is_complete = True
                importreq.detail = "Upload data corrupt. Unable to import"
                importreq.save()
        else:
            importreq.is_complete = True
            importreq.detail = (
                "Not authorized to run import on the requested media, "
                "as user is not a part of the group"
            )
            importreq.save()

    os.chdir(cwd)
    return True


# ── ARQ async task entry-points ───────────────────────────────────────────────


async def export_request_task(ctx: dict, request_id: int) -> bool:
    """ARQ task: run export business logic in a thread pool."""
    return await asyncio.to_thread(_export_sync, request_id)


async def import_request_task(ctx: dict, request_id: int) -> bool:
    """ARQ task: run import business logic in a thread pool."""
    return await asyncio.to_thread(_import_sync, request_id)
