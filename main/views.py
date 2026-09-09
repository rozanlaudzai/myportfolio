from django.shortcuts import render
from .models import Experience

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
        'experience_list': Experience.objects.all()
    }
    return render(request, 'main/experience.html', context)
