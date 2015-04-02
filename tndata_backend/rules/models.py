import json

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
        return self.rule_name if self.rule_name else self.app_name

    class Meta:
        ordering = ['app_name', 'created']
        verbose_name = "Rule"
        verbose_name_plural = "Rules"

    @property
    def _conditions(self):
        """Return json-decoded versions of the conditions."""
        return json.loads(self.conditions)

    @property
    def _actions(self):
        """Return json-decoded versions of the actions."""
        return json.loads(self.actions)

    @models.permalink
    def get_absolute_url(self):
        return ('rules:detail', [str(self.id)])

    def build_rules(self):
        return [{'conditions': self._conditions, 'actions': self._actions}]


# TODO: Helper function to query all Rules for a given app, model?
