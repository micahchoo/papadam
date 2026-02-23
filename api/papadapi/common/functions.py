from django.shortcuts import get_object_or_404

from papadapi.annotate.models import Annotation
from papadapi.archive.models import MediaStore
from papadapi.common.models import Tags, Group


def recalculate_tag_count(tag_instance):
    tag_count = (
        MediaStore.objects.filter(tags__id=tag_instance.id).count()
        + Annotation.objects.filter(tags__id=tag_instance.id).count()
    )
    # INFO: This explictly handles scenario where this is the first time the tag is created and thus not yet mapped to the media. In such a case, we explictly set the tag count to 1 to get started
    if tag_count == 0: 
        tag_instance.count = 1
    else:
        tag_instance.count = tag_count
    tag_instance.save()
    
    
def get_final_tags_count(media_tags_count, annotation_tags_count,count=False):
    data = {}
    for val in media_tags_count+annotation_tags_count:
        if count:
            key = val["tag_id"]
        else:
            key = val["id"]
            
        if key in data:
            if count:
                data[key]['count'] = data[key]['count']+val['count']
            else:
                data[key]['value'] = data[key]['symbolSize']+val['symbolSize']
                data[key]['symbolSize'] = data[key]['value'] if data[key]['value'] > 8 else 8
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
                data[key]['symbolSize'] = data[key]['value'] if data[key]['value'] > 8 else 8
    return list(data.values())


def get_related_tags(group,tag,links,media=True,annotation=True):
    tag_obj = Tags.objects.filter(id=tag).first()
    group = Group.objects.filter(id=group).first()
    return_list = []
    if media and tag_obj and group:
        related_tags = MediaStore.objects.filter(group=group,tags=tag_obj).distinct()
        for rts in related_tags:
            for rts_tag in rts.tags.all():
                if tag != rts_tag.id:
                    return_list.append({"source":tag, "target":rts_tag.id}) 
        return return_list
    else:
        return []
    

def create_or_update_tag(tag):
    tag_value = tag.lower().strip()
    if tag_value:      
        t = Tags.objects.get_or_create(name=tag_value)[0]
        recalculate_tag_count(t)
        return t
    else:
        return None