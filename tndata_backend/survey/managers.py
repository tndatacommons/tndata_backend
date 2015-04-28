from django.db import models
from django.core.exceptions import ObjectDoesNotExist


class QuestionManager(models.Manager):

    def available(self, *args, **kwargs):
        qs = self.get_queryset()
        return qs.filter(available=True)


class SurveyResultManager(models.Manager):

    def create_objects(self, user, instrument):
        """Creates SurveyResult objects for the given user's responses to the
        specified Instrument.

        Returns a QuerySet of the created SurveyResponse objects.

        """
        created_ids = set()  # IDs for created objects.

        # ONLY applicable to Likert Questions.
        qtypes = {t.lower() for t, q in instrument.questions}
        if 'likertquestion' not in qtypes and len(qtypes) != 1:
            raise ValueError("A SurveyResult is only valid for LikertQuestions")

        questions = [q for qt, q in instrument.questions]
        if len(questions) % 2 != 0:
            # Maybe survey is incomplete?
            raise ValueError("Instruments must have even number of questions")

        # TODO: There's probably a nicer way to do this :-/
        # Split the questions into two subscales; they should be ordered
        # correctly by default.
        middle = int(len(questions) - len(questions) / 2)
        a, b = questions[:middle], questions[middle:]

        try:
            for q1, q2 in zip(a, b):
                # Q1 - Q2; discard anything less than zero (keep 0)
                # We need the user's responses to these questions.
                r1 = q1.likertresponse_set.filter(user=user).latest()
                r2 = q2.likertresponse_set.filter(user=user).latest()
                score = max(r1.selected_option - r2.selected_option, 0)
                labels = list(set(q1.labels + q2.labels))

                obj = self.create(
                    user=user,
                    instrument=instrument,
                    score=score,
                    labels=labels
                )
                created_ids.add(obj.id)
        except ObjectDoesNotExist:
            return self.get_queryset().none()

        return self.get_queryset().filter(id__in=created_ids)
