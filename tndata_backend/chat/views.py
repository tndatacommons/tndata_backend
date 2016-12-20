from django.contrib.auth import get_user_model
from django.shortcuts import render
from django.views.generic import TemplateView


class IndexView(TemplateView):
    template_name = "chat/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['users'] = get_user_model().objects.all()
        return context


def chat_view(request, with_username):
    context = {'with_username': with_username}
    return render(request, "chat/chat.html", context)
