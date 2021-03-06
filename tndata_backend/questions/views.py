from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.http import JsonResponse
from django.db.models import Q

from .forms import AnswerForm, QuestionForm
from .models import Answer, Question

# ----------------------------------------------------------------------------
# TODO: vote on question
# TODO: vote on answer
# ----------------------------------------------------------------------------


def index(request):
    """List the latest questions + a link to ask a new one."""
    questions = Question.objects.filter(published=True).order_by("created_on")
    context = {
        'is_user_authenticated': request.user.is_authenticated(),
        'latest_questions': questions[:10],
    }
    return render(request, 'questions/index.html', context)


def search(request):
    """Returns json with search results."""
    query = request.GET.get('q', '')
    print("Search query: " + query)
    if query:
        qset = Q()
        for term in query.split():
            qset |= Q(title__contains=term)
            
        questions = Question.objects.filter(qset)
        
        questionList = []
        count = 0
        for question in questions:
            data = {
                'id': question.id,
                'title': question.title,
                'title_slug': question.title_slug
            }
            questionList.append(data)
            count += 1
            if count == 4:
                break
        
        return JsonResponse({'results': questionList})
    else:
        return JsonResponse({'results': []})


def question_details(request, pk, title_slug):
    """List a question + all it's answers."""
    question = get_object_or_404(Question, pk=pk, title_slug=title_slug)
    context = {
        'question': question,
        'answers': question.answer_set.all(),
        'form': AnswerForm(),
    }
    return render(request, 'questions/question_details.html', context)


@login_required
def post_answer(request, pk, title_slug):
    # list the question + form to answer it
    question = get_object_or_404(Question, pk=pk, title_slug=title_slug)
    if request.method == "POST":
        form = AnswerForm(request.POST)
        if form.is_valid():
            answer = form.save(commit=False)
            answer.question = question
            answer.user = request.user
            answer.save()
            messages.success(request, "Your answer has been posted.")
            return redirect(answer.get_absolute_url())
    else:
        form = AnswerForm()

    context = {
        'question': question,
        'answers': None,
        'form': form,
    }
    return render(request, 'questions/question_details.html', context)


@login_required
def ask_question(request, title=""):
    """Handle the POST requests to create a question."""
    if request.method == "POST":
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            if request.user.is_authenticated():
                question.user = request.user
                question.published = True
                messages.success(request, "Your question as been published.")
            else:
                msg = (
                    "Your question as been saved, and will be posted once "
                    "it has been reviewed."
                )
                messages.success(request, msg)
            question.save()
            return redirect(question.get_absolute_url())
    else:
        form = QuestionForm(initial={'title': title})

    print("Received title: " + title)
    context = {
        'has_title': bool(title),
        'title': title + "?",
        'form': form,
    }
    return render(request, 'questions/ask.html', context)


@login_required
def upvote_question(request, pk, title_slug):
    """Upvoting a question only handles POST requests, and this only
    works for authenticated users. All other requests will just redirect
    back to the question details."""

    question = get_object_or_404(Question, pk=pk, title_slug=title_slug)

    # Check that the user hasn't already voted...
    has_voted = question.voters.filter(pk=request.user.id).exists()
    if request.method == "POST" and not has_voted:
        question.voters.add(request.user)
        question.votes += 1
        question.save()
    return redirect(question.get_absolute_url())


@login_required
def upvote_answer(request, pk, title_slug, answer_pk):
    answer = get_object_or_404(
        Answer,
        question__pk=pk,
        question__title_slug=title_slug,
        pk=answer_pk
    )

    # Check that the user hasn't already voted...
    has_voted = answer.voters.filter(pk=request.user.id).exists()
    if request.method == "POST" and not has_voted:
        answer.voters.add(request.user)
        answer.votes += 1
        answer.save()
    return redirect(answer.get_absolute_url())

