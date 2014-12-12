"""
See api.py for APIs powering the mobile/mobile-web app.

These views are for internal organizational use.

"""
from django.http import JsonResponse
from django.views.generic import View

from . rules import entry_rule_data


class RulesDataView(View):
    http_method_names = ['get', 'head']

    def get(self, request):
        return JsonResponse(entry_rule_data())
