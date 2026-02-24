
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
    group_extra_questions = models.JSONField(default=dict, blank=True, null=True)
    extra_group_questions = models.ManyToManyField(
        "common.Question", verbose_name=_("Questions")
    )
    delete_wait_for = models.IntegerField(_("Wait before delete"), default=0)

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    def __str__(self):
        return self.name


# ── UIConfig defaults ─────────────────────────────────────────────────────────


def _default_player_controls():
    return {
        "skip_seconds": [10, 30],
        "show_waveform": False,
        "show_transcript": False,
        "default_quality": "auto",
    }


def _default_annotations_config():
    return {
        "allow_images": True,
        "allow_audio": True,
        "allow_video": True,
        "allow_media_ref": True,
        "time_range_input": "slider",
    }


def _default_exhibit_config():
    return {"enabled": True}


# ── UIConfig model ────────────────────────────────────────────────────────────


class UIConfig(models.Model):
    class Profile(models.TextChoices):
        STANDARD = "standard", "Standard"
        ICON = "icon", "Icon"
        VOICE = "voice", "Voice"
        HIGH_CONTRAST = "high-contrast", "High Contrast"

    class ColorScheme(models.TextChoices):
        DEFAULT = "default", "Default"
        WARM = "warm", "Warm"
        COOL = "cool", "Cool"
        HIGH_CONTRAST = "high-contrast", "High Contrast"

    group = models.OneToOneField(
        "common.Group",
        on_delete=models.CASCADE,
        related_name="uiconfig",
    )
    profile = models.CharField(
        choices=Profile.choices, default=Profile.STANDARD, max_length=20
    )
    # branding
    brand_name = models.CharField(max_length=100, default="Papad.alt")
    brand_logo_url = models.CharField(max_length=500, blank=True, default="")
    primary_color = models.CharField(max_length=7, default="#1e3a5f")
    accent_color = models.CharField(max_length=7, default="#3b82f6")
    # localisation
    language = models.CharField(max_length=10, default="en")
    # appearance
    icon_set = models.CharField(max_length=200, default="default")
    font_scale = models.FloatField(default=1.0)
    color_scheme = models.CharField(
        choices=ColorScheme.choices, default=ColorScheme.DEFAULT, max_length=20
    )
    # accessibility
    voice_enabled = models.BooleanField(default=False)
    offline_first = models.BooleanField(default=False)
    # complex sub-configs
    player_controls = models.JSONField(default=_default_player_controls)
    annotations_config = models.JSONField(default=_default_annotations_config)
    exhibit_config = models.JSONField(default=_default_exhibit_config)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        verbose_name = "UI Configuration"

    def __str__(self):
        return f"UIConfig({self.group})"


# ── Signal: auto-create UIConfig when Group is created ───────────────────────

from django.db.models.signals import post_save  # noqa: E402
from django.dispatch import receiver  # noqa: E402


@receiver(post_save, sender=Group)
def create_group_uiconfig(sender, instance, created, **kwargs):
    if created:
        UIConfig.objects.get_or_create(group=instance)
