from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect, render
from django.views.generic import TemplateView
from django_rq import get_connection


class IndexView(TemplateView):
    template_name = "chat/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # users = get_user_model().objects.all()
        # if self.request.user and self.request.user.is_authenticated():
            # users = users.exclude(pk=self.request.user.id)
        # context['users'] = users
        return context


def chat_view(request, with_user):
    context = {'with_user': with_user}
    return render(request, "chat/chat.html", context)


@user_passes_test(lambda u: u.is_authenticated() and u.is_staff)
def debug_messages(request):
    key = 'websocket-debug'
    conn = get_connection('default')

    if request.method == "POST" and request.POST.get("submit") == "Clear":
        conn.delete(key)
        return redirect('chat:debug')

    context = {}
    if settings.DEBUG or settings.STAGING:
        num = int(request.GET.get('num', 1000))
        messages = [
            m.decode('utf-8').split("|")
            for m in conn.lrange(key, 0, num)
        ]

        context = {
            'chat_messages': messages,
            'num_options': [1000, 500, 100, 50, 10],
            'num': num,
        }
    return render(request, "chat/debug.html", context)
