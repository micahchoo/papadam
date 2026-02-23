import json
import os
import tarfile
import uuid

import requests
from django.core.files import File
from django.core.files.storage import default_storage
from django.shortcuts import get_object_or_404
import structlog

from papadapi.tasks_compat import db_task

log = structlog.get_logger(__name__)

from papadapi.annotate.models import Annotation
from papadapi.archive.models import MediaStore
from papadapi.common.models import Group, Tags
from papadapi.importexport.models import IERequest


def download(url, file_name, files_path):
    # open in binary mode
    file_name = file_name.split("/")[1]
    with open(os.path.join(files_path, file_name), "wb") as file:
        # get request
        response = requests.get(url)
        # write to file
        file.write(response.content)
    return file_name


def export_annotation(files_path, annotation):
    annotation_data = {}
    annotation_data[str(annotation.uuid)] = {
        "annotation_text": annotation.annotation_text,
        "media_target": annotation.media_target,
    }
    annotation_tags = ""
    for tags in annotation.tags.all():
        annotation_tags += tags.name + ","
    annotation_data[str(annotation.uuid)]["tags"] = annotation_tags
    # Annotation Image
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


def export_media(files_path, media_instance):
    media_file_list = []
    media_data = {}
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
    # If annotation lenght there
    if len(annotations) > 0:
        media_data["annotations"] = {}
        for annotation in annotations:
            media_data["annotations"][str(annotation.uuid)] = {}
            annotation_file, annotation_data = export_annotation(files_path, annotation)
            media_file_list.append(annotation_file)
            media_data["annotations"].update(annotation_data)
    return media_file_list, media_data


def import_annotation(files_path, annovals, media):
    annotation_file_name = os.path.join(files_path, annovals["annotation_image"])
    annotation = Annotation.objects.create(
        annotation_text=annovals["annotation_text"],
        media_target=annovals["media_target"],
        media_reference_id=str(media.uuid),
        annotation_image=File(file=open(annotation_file_name, "rb")),
    )
    return True


def import_media(files_path, media_data, group):
    media_file_name = os.path.join(files_path, media_data["media_file_name"])
    media = MediaStore.objects.create(
        name=media_data["name"],
        description=media_data["description"],
        uuid=uuid.uuid4(),
        group=group,
        upload=File(file=open(media_file_name, "rb")),
    )
    for tag in media_data["tags"].split(","):
        tag_obj = Tags.objects.filter(name=tag).first()
        if not tag_obj:
            tag_obj = Tags.objects.create(name=tag)
        media.tags.add(tag_obj)
    # Add annotaions if exists
    if "annotations" in media_data:
        for annotation_id, annovals in media_data["annotations"].items():
            import_annotation(files_path, annovals, media)

    return True


def extract_json_for_import(files_path, import_data):
    jsondata = {}
    tarfilename = download(import_data.url, import_data.name, files_path)
    # tarfilename = os.path.join(files_path,filename)
    if tarfile.is_tarfile(tarfilename):
        with tarfile.open(tarfilename, "r") as file_obj:
            file_obj.extractall()

        jsondata = json.load(open("data.json"))
        if jsondata:
            return jsondata
        else:
            return False


@db_task()
def export_request_task(request_id):
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
            export_data["group"] = {}
            export_data["group"]["group_name"] = group.name
            export_data["group"]["group_visibility"] = group.is_public
            export_data["group"]["group_description"] = group.description
            if requested_by in group.users.all() or group.is_public:
                media_data = {}
                media_data_queryset = MediaStore.objects.filter(group=group)
                for data in media_data_queryset:
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
                export.detail = "Not authorized to run export on the requested media, as user is not a part of the group"
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
                # media_data["annotations"] = {}
                media_data["annotation"] = {}
                media_files, media_data["annotation"] = export_annotation(
                    files_path, annotation
                )
                if media_files:
                    media_file_list.append(media_files)
                proceed_upload = True
            else:
                export.is_complete = True
                export.detail = "Not authorized to run export on the requested annotation, as user is not a part of the group"
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

        # Create a tar file
        fileobj = tarfile.open(request_uuid + ".tar", "w")
        fileobj.add("data.json")
        fileobj.list()
        # Now add the media also
        if len(media_file_list) > 0:
            for mfl in media_file_list:
                if (
                    mfl is not None
                ):  # TODO: Not sure why, but some rare cases, there is an empty None that gets added. This is explict handling, but identifying and patching the root cause needs to be done.
                    fileobj.add(mfl)
        fileobj.close()

        # Upload the created file
        fp = open(request_uuid + ".tar", "rb")
        export.requested_file.save(request_uuid + ".tar", File(fp))
        fp.close()
        os.chdir(cwd)

        # Other metadata update and save.
        export.is_authorized = True
        export.is_complete = True
        export.detail = "Request completed"
        export.save()
    return True


@db_task()
def import_request_task(request_id):
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
            # Create Group
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

            # Upload all media
            media_details = jsonfile["archive"]
            for id, media_data in media_details.items():
                import_media(files_path, media_data, group)
        else:
            export.is_complete = True
            export.detail = "Upload data corrupt. Unable to import"
            export.save()

    elif importreq_requested_type == "archive":
        group_into = importreq_metadata["import_into_group"]
        group = Group.objects.get(id=group_into)
        if group and requested_by in group.users.all():
            jsonfile = extract_json_for_import(files_path, importreq.requested_file)
            if jsonfile:
                media_details = jsonfile["archive"]
                for id, media_data in media_details.items():
                    import_media(files_path, media_data, group)
            else:
                export.is_complete = True
                export.detail = "Upload data corrupt. Unable to import"
                export.save()
    elif importreq_requested_type == "annotation":
        media_into = importreq_metadata["import_for_media"]
        media = MediaStore.objects.get(uuid=media_into)
        group = media.group
        if group and requested_by in group.users.all():
            jsonfile = extract_json_for_import(files_path, importreq.requested_file)
            if jsonfile:
                annotation_details = jsonfile["archive"]["annotation"]
                for (
                    annotation_detail
                ) in annotation_details.values():  # Mind the singular and plural here.
                    import_annotation(files_path, annotation_detail, media)
            else:
                export.is_complete = True
                export.detail = "Upload data corrupt. Unable to import"
                export.save()
        else:
            export.is_complete = True
            export.detail = "Not authorized to run import on the requested media, as user is not a part of the group"
            export.save()
    os.chdir(cwd)
    return True
