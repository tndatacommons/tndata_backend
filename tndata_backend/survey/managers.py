from django.db import models


class QuestionManager(models.Manager):

    def available(self, *args, **kwargs):
        qs = self.get_queryset()
        return qs.filter(available=True)
