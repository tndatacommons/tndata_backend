"""
These views are for internal organizational use.

"""
from django.contrib import messages
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render
from django.views.generic import View
from django.views.generic.detail import DetailView

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

    # TODO: /rules/ --- POST: create new rule.
    #def post(self, request, *args, **kwargs):
        #form = self.form_class(request.POST)
        #if request.is_ajax() and form.is_valid():
            #return HttpResponseRedirect('/success/')
        #return render(request, self.template_name, {'form': form})


class RuleDetailView(DetailView):
    model = Rule

    def post(self, request, *args, **kwargs):
        """DELETE a rule. It's still do hard to build a `delete` method :( """
        obj = self.get_object()
        messages.success(request, "Deleted: {0}".format(obj))
        obj.delete()
        return JsonResponse({})
