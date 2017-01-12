import json

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from . models import CronLog


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
        # Try grabbing the POST data.
        try:
            data = dict(request.POST)
            if data == {}:  # No data? Try de-coding the post body
                data = json.loads(request.body.decode("utf8"))

            key = data['key']
            command = data['command']
            message = data['message']
            host = data.get('host', request.get_host())

            # Check for our key
            if key == settings.CRONLOG_KEY and command and message:
                item = CronLog.objects.create(command=command, message=message, host=host)
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
                return JsonResponse({'error': 'Missing Key'}, status=400)

        except KeyError:
            return JsonResponse({'error': 'Invalid Payload'}, status=400)
    return JsonResponse(results)
