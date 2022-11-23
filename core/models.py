from django.db import models
from django.utils.translation import gettext_lazy as _


class TimeStampedModel(models.Model):
    created = models.DateTimeField(verbose_name=_('생성시간'), auto_now_add=True)
    modified = models.DateTimeField(verbose_name=_('수정시간'), auto_now=True)

    class Meta:
        abstract = True
