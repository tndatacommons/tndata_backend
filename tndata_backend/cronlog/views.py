import json

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from . models import CronLog


def get_payload(request):
    """Given a request object, extract the data we want. Return a tuple
    of the form:

        (key, command, message, host)

    """
    _default_host = request.get_host()

    # Try grabbing directlyf rom the POST data.
    key = request.POST.get('key')
    command = request.POST.get('command')
    message = request.POST.get('message')
    host = request.POST.get('host', _default_host)

    # No data? Try de-coding the post body
    if not any([key, command, message]) and dict(request.POST) == {}:
        try:
            data = json.loads(request.body.decode("utf8"))
            key = data['key']
            command = data['command']
            message = data['message']
            host = data.get('host', _default_host)
        except KeyError:
            command = None
            message = None

    return (key, command, message, host)


# -----------------------------------------------------------------------------
# This pseudo-api doesn't use CSRF protection, because we want to insert
# data from a curl command so that request MUST include the folowing key.
#
# e.g.
#       curl --data 'whatever' http://.../cronlog/add/),
#
# -----------------------------------------------------------------------------
@csrf_exempt
def add_entry(request):
    results = {}
    if request.method == "POST":
        key, command, message, host = get_payload(request)

        # Check for our key
        if key == settings.CRONLOG_KEY and command and message:
            params = {
                'command': command,
                'message': message,
                'host': host,
            }
            item = CronLog.objects.create(**params)
            return JsonResponse({
                'command': item.command,
                'message': item.message,
                'host': item.host,
                'created_on': item.created_on,
            })
        elif key == settings.CRONLOG_KEY:
            results = {'error': 'command and message are required'}
            return JsonResponse(results, status=400)
        else:
            return JsonResponse({'error': 'Invalid Payload'}, status=400)
    return JsonResponse(results)
