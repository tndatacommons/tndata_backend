from django.db import models
from jsonfield import JSONField


class Rule(models.Model):
    app_name = models.CharField(max_length=256, db_index=True)
    rule_name = models.CharField(max_length=256, blank=True)
    conditions = JSONField(db_index=True)
    actions = JSONField(db_index=True)
    created = models.DateTimeField(auto_now_add=True, db_index=True)
    modified = models.DateTimeField(auto_now=True, db_index=True)

    def __str__(self):
        if self.rule_name:
            return "{0}: {1}".format(self.app_name, self.rule_name)
        return self.app_name

    class Meta:
        ordering = ['app_name', 'created']
        verbose_name = "Rule"
        verbose_name_plural = "Rules"

    def build_rules(self):
        return [{'conditions': self.conditions, 'actions': self.actions}]


# TODO: Helper function to query all Rules for a given app, model?
