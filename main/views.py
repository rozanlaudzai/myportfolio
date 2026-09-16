from django.contrib import messages
from django.core import serializers
from django.shortcuts import render, redirect, get_object_or_404
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

def show_awards(request: HttpRequest):
    json_response = get_awards_json(request)

    awards = serializers.deserialize(
        'json',
        json_response.content.decode('utf-8'),
    )

    awards = [award.object for award in awards]

    title_query = request.GET.get('title', '').strip()

    context = {
        'name': 'Rozan',
        'award_list': Award.objects.all(),
        'title_query': title_query,
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

def get_awards_json(request: HttpRequest):
    title_query = request.GET.get('title', '').strip()
    awards = Award.objects.all()

    if title_query:
        awards = awards.filter(title__icontains=title_query)

    awards_json = serializers.serialize('json', awards)
    return HttpResponse(awards_json, content_type='application/json')

def delete_award(request: HttpRequest, award_id):
    award = get_object_or_404(Award, pk=award_id)

    if request.method == 'POST':
        award.delete()
        messages.success(request, 'Award successfully deleted!')

    return redirect('main:show_awards')