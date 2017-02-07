from django.conf import settings
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import TemplateView
from django_rq import get_connection

from .models import ChatGroup
from .utils import generate_room_name


class IndexView(TemplateView):
    template_name = "chat/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # users = get_user_model().objects.all()
        # if self.request.user and self.request.user.is_authenticated():
        #     users = users.exclude(pk=self.request.user.id)
        # context['users'] = users
        context['groups'] = ChatGroup.objects.all()
        return context


@login_required
def chat_view(request, recipient_id):
    context = {
        'room': generate_room_name([request.user.id, recipient_id]),
        'show_debug_stuff': request.user.is_staff or (request.user.id in [264, 1009, 995])
    }
    return render(request, "chat/chat.html", context)


@login_required
def group_chat_view(request, pk, slug):
    from clog.clog import clog
    clog(slug, title="pk={}".format(pk))
    group = get_object_or_404(ChatGroup, pk=pk, slug=slug, members=request.user)
    context = {'group': group}
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
