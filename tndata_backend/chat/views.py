from django.contrib.auth import get_user_model
from django.shortcuts import render
from django.views.generic import TemplateView


class IndexView(TemplateView):
    template_name = "chat/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        users = get_user_model().objects.all()
        if self.request.user and self.request.user.is_authenticated():
            users = users.exclude(pk=self.request.user.id)
        context['users'] = users
        return context


def chat_view(request, with_username):
    context = {'with_username': with_username}
    return render(request, "chat/chat.html", context)
