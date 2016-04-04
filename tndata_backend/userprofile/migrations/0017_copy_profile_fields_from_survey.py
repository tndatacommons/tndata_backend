# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from datetime import datetime
from django.db import migrations, models


def copy_data_from_survey(apps, schema_editor=None):
    # The user's profile model, where we want to save data.
    UserProfile = apps.get_model("userprofile", "UserProfile")

    # Survey models, from which we're pulling dat.
    OpenEndedResponse = apps.get_model('survey', 'OpenEndedResponse')
    MultipleChoiceResponse = apps.get_model('survey', 'MultipleChoiceResponse')
    BinaryResponse = apps.get_model('survey', 'BinaryResponse')

    for profile in UserProfile.objects.all():

        # My sex is
        try:
            resp = MultipleChoiceResponse.objects.filter(
                user=profile.user,
                question__id=8
            ).latest()
            profile.sex = resp.selected_option.text
        except MultipleChoiceResponse.DoesNotExist:
            profile.sex = 'no-answer'

        # My birthday is...
        try:
            resp = OpenEndedResponse.objects.filter(
                user=profile.user,
                question__id=1
            ).latest()
            profile.birthday = datetime.strptime(resp.response, "%Y-%m-%d")
        except (ValueError, OpenEndedResponse.DoesNotExist):
            pass

        # My zip code is
        try:
            resp = OpenEndedResponse.objects.filter(
                user=profile.user,
                question__id=2
            ).latest()
            profile.zipcode = resp.response
        except (ValueError, OpenEndedResponse.DoesNotExist):
            pass

        # I am currently employed
        try:
            resp = BinaryResponse.objects.filter(
                user=profile.user,
                question__id=13
            ).latest()
            profile.employed = resp.selected_option
        except BinaryResponse.DoesNotExist:
            pass

        # I am currently in a romantic relationship
        try:
            resp = BinaryResponse.objects.filter(
                user=profile.user,
                question__id=14
            ).latest()
            profile.in_relationship = resp.selected_option
        except BinaryResponse.DoesNotExist:
            pass

        # I am a parent
        try:
            resp = BinaryResponse.objects.filter(
                user=profile.user,
                question__id=16
            ).latest()
            profile.is_parent = resp.selected_option
        except BinaryResponse.DoesNotExist:
            pass

        # I have a college degree
        try:
            resp = BinaryResponse.objects.filter(
                user=profile.user,
                question__id=12
            ).latest()
            profile.has_degree = resp.selected_option
        except BinaryResponse.DoesNotExist:
            pass

        # And save the model...
        profile.save()


class Migration(migrations.Migration):

    dependencies = [
        ('userprofile', '0016_auto_20160404_1940'),
        ('survey', '0028_auto_20150806_1743'),
    ]
    operations = [
        migrations.RunPython(copy_data_from_survey),
    ]
