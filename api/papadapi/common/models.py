
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext as _
from djrichtextfield.models import RichTextField


class Tags(models.Model):
    name = models.CharField(_("tag name"), max_length=100)
    count = models.PositiveIntegerField(_("Count of this tag"), default=1)

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        verbose_name = _("Tags")
        verbose_name_plural = _("Tags")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("Tags_detail", kwargs={"pk": self.pk})


class Question(models.Model):

    question_type_choices = (
        ("text", "Text"),
        ("number", "Number"),
    )

    question = models.TextField(_("Question"))
    question_type = models.CharField(
        _("Question Type"), max_length=50, choices=question_type_choices
    )
    question_mandatory = models.BooleanField(default=False)
    group_question = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)
    created_by = models.ForeignKey(
        "users.User",
        verbose_name=_("Who created the question"),
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = _("Question")
        verbose_name_plural = _("Questions")

    def __str__(self):
        return self.question

    def get_absolute_url(self):
        return reverse("Question_detail", kwargs={"pk": self.pk})


class Group(models.Model):
    name = models.CharField(_("Group Name"), max_length=200)
    description = RichTextField(_("Group description"), blank=True, null=True)
    is_active = models.BooleanField(_("Is group Actve"), default=True)
    is_public = models.BooleanField(_("Public group "), default=True)
    users = models.ManyToManyField("users.User", verbose_name=_("Users"))
    group_extra_questions = models.JSONField(default={}, blank=True, null=True)
    extra_group_questions = models.ManyToManyField(
        "common.Question", verbose_name=_("Questions")
    )
    delete_wait_for = models.IntegerField(_("Wait before delete"), default=0)

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    def __str__(self):
        return self.name
