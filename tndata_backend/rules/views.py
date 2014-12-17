"""
These views are for internal organizational use.

"""
from django.http import JsonResponse
from django.shortcuts import render
from django.views.generic import View

from . models import Rule
from . import rulesets


class RulesDataView(View):
    http_method_names = ['get', 'head']

    def get(self, request):
        return JsonResponse(rulesets.ruleset.export())


class RulesView(View):
    http_method_names = ['get', 'head', 'post']

    def get(self, request):
        context = {
            'rules': Rule.objects.all()
        }
        return render(request, 'rules/index.html', context)

    # TODO:
    #def post(self, request, *args, **kwargs):
        #form = self.form_class(request.POST)
        #if request.is_ajax() and form.is_valid():
            #return HttpResponseRedirect('/success/')
        #return render(request, self.template_name, {'form': form})


# TODO: Probably need a RulesView with .get .post methods to save rules that
# are created (and will probably need a RulesForm... depends on how we store these)
#
# /rules/       --- GET: list existing rules with links to delete.
#               --- POST: create new rule.
# /rules/<id>   --- GET: view, DELETE: remove
