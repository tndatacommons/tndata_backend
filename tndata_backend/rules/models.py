from collections import OrderedDict
from django.db import models
from jsonfield import JSONField


class Rule(models.Model):
    app_name = models.CharField(max_length=256, db_index=True)
    rules = JSONField(
        db_index=True,
        load_kwargs={'object_pairs_hook': OrderedDict}
    )
    created = models.DateTimeField(auto_now_add=True, db_index=True)
    modified = models.DateTimeField(auto_now=True, db_index=True)

    def __str__(self):
        return "Rules for {0}".format(self.app_name)

    class Meta:
        ordering = ['app_name', 'created']
        verbose_name = "Rule"
        verbose_name_plural = "Rules"
