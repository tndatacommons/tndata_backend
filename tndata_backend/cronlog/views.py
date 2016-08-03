from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from . models import CronLog


# This pseudo-api doesn't use CSRF protection, because we want to insert
# data from a curl command (e.g. curl --data 'whatever' http://.../cronlog/add/),
# so that request MUST include the folowing key.
KEY = "las98a890se4na908sdfanm32"


@csrf_exempt
def add_entry(request):
    results = {}

    if (
        request.method == "POST" and
        request.POST.get('key') == KEY and
        request.POST.get('command') and
        request.POST.get('message')
    ):
        item = CronLog.objects.create(
            command=request.POST['command'],
            message=request.POST['message']
        )
        return JsonResponse({
            'command': item.command,
            'message': item.message,
            'created_on': item.created_on,
        })
    elif request.method == "POST" and request.POST.get('key') is None:
        return JsonResponse({'error': 'Missing Key'}, status=400)
    elif (
        request.method == "POST" and
        ('command' not in request.POST or 'message' not in request.POST)
    ):
        results = {'error': 'command and message are required'}
        return JsonResponse(results, status=400)
    return JsonResponse(results)
