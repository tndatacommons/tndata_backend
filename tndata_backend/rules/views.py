"""
These views are for internal organizational use.

"""
from django.http import JsonResponse
from django.views.generic import View

from . import rulesets


class RulesDataView(View):
    http_method_names = ['get', 'head']

    def get(self, request):
        return JsonResponse(rulesets.ruleset.export())


# TODO: Probably need a RulesView with .get .post methods to save rules that
# are created (and will probably need a RulesForm... depends on how we store these)
#
# /rules/       --- GET: list existing rules with links to delete.
#               --- POST: create new rule.
# /rules/add/   --- GET: display form
# /rules/<id>   --- GET: view, DELETE: remove
