# Groups

Groups are a logical seperation of media that we upload to be made available to different users. Groups ensure that only a group of users have the rights to upload and annotate. Groups also have the following configurations 

1. **Public / Private** : This setting ensures if non-member can see the group and access the media listed in the group. If public, everyone can see the media and annotation, but only members can annotate and upload media. 
2. **Keep deleted data**: This setting describes, how the delete action is to be take care. If this value is set of 0, then all delete actions (both media and annotation) are deleted immediatly. If this value is set to 1, then the actual permanent deletion happens after 1 day. If the value is set to 2, then 2 days and so on. 
3. **Extra Fields** : Papad by default only requires a Name, Media and tags for annotation. The description is an optional field. In an everyday deployment, communities find this extremenly limiting. This option allows every group to have a custom set of questions. As of now, this is only elementary support allowing fields to be named and marked as mandatory. In the upcoming releases, this should have a more stable version. 


You can create the group using the Create group button in the navigation bar. 

![Group Creation](/static/groups/group_create.png)


Settings like Public/Private and delete are configurable using the group settings. **But currently the extra fields setting is at create time only, so we are requesting group creators to be cautios**. In the upcoming release, we will introduce the ability to have dynamic editing of extra fields. 

![Group Settings](/static/groups/group_settings.png)

![Group Keep delete for](/static/groups/deletion_timelimit.png)

You can click on Add users option in group settings, search for users and add them to the group

![Group Add users](/static/groups/adding_users_to_group.png)
