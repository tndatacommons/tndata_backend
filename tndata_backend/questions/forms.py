from django import forms
from .models import Answer, Question


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['title', 'content', 'keywords']
    
    class Media:
        js = (
            "foundation/js/vendor/jquery.js",
            "js/question_form.js",
        )


class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['content', ]
