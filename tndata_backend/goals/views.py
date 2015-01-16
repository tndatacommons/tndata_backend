from django.shortcuts import render


def index(request):
    context = {}
    return render(request, 'goals/index.html', context)
