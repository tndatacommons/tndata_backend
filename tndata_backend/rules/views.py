"""
These views are for internal organizational use.

"""
from django.http import JsonResponse
from django.views.generic import View

from . rules import entry_rule_data


class RulesDataView(View):
    http_method_names = ['get', 'head']

    def get(self, request):
        return JsonResponse(entry_rule_data())


# TODO: Probably need a RulesView with .get .post methods to save rules that
# are created (and will probably need a RulesForm... depends on how we store these)

