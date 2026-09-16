from django.contrib import messages
from django.core import serializers
from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse

from .models import Experience, Award
from .forms import AwardForm

def index(request):
    context = {
        'name': 'Rozan',
        'npm': '2506547544',
        'study_program': 'S1 Ilmu Komputer',
        'bio': 'Go & C++ Enjoyer. Python & JavaScript Hater.'
    }
    return render(request, 'main/index.html', context)

def show_experience(request):
    context = {
        'name': 'Rozan',
        'experience_list': Experience.objects.all(),
    }
    return render(request, 'main/experience.html', context)

def show_awards(request):
    context = {
        'name': 'Rozan',
        'award_list': Award.objects.all(),
    }
    return render(request, 'main/awards.html', context)

def create_award(request: HttpRequest):
    form = AwardForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'New award has been created!')
        return redirect('main:show_awards')

    context = {
        'name': 'Rozan',
        'form': form,
    }
    return render(request, 'main/award-form.html', context)
