from django.contrib import messages
from django.core import serializers
from django.db.models import prefetch_related_objects
from django.shortcuts import (
    render,
    redirect,
    get_object_or_404,
)
from django.http import (
    HttpRequest,
    HttpResponse,
)
from django.views.decorators.http import require_http_methods
from django.contrib.auth import (
    login,
    logout,
)
from django.contrib.auth.forms import (
    UserCreationForm,
    AuthenticationForm,
)

from .models import Experience, Award
from .forms import AwardForm, ExperienceForm

@require_http_methods(['GET'])
def index(request):
    context = {
        'name': 'Rozan',
        'npm': '2506547544',
        'study_program': 'S1 Ilmu Komputer',
        'bio': 'Go & C++ Enjoyer. Python & JavaScript Hater.'
    }
    return render(request, 'main/index.html', context)


@require_http_methods(['GET'])
def show_experience(request: HttpRequest):
    json_response = get_experience_json(request)
    experiences = serializers.deserialize(
        'json',
        json_response.content.decode('utf-8'),
    )
    experiences = [experience.object for experience in experiences]
    prefetch_related_objects(experiences, 'skills')

    context = {
        'name': 'Rozan',
        'experience_list': experiences,
        'title_query': request.GET.get('title', '').strip(),
    }
    return render(request, 'main/experience.html', context)


@require_http_methods(['GET'])
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
        'award_list': awards,
        'title_query': title_query,
    }
    return render(request, 'main/awards.html', context)


@require_http_methods(['GET', 'POST'])
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


@require_http_methods(['GET', 'POST'])
def edit_award(request: HttpRequest, award_id):
    award = get_object_or_404(Award, pk=award_id)
    form = AwardForm(
        request.POST if request.method == 'POST' else None,
        instance=award,
    )

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Award successfully updated!')
        return redirect('main:show_awards')

    context = {
        'name': 'Rozan',
        'form': form,
        'award': award,
    }
    return render(request, 'main/award-form.html', context)


@require_http_methods(['GET'])
def get_experience_json(request: HttpRequest):
    title_query = request.GET.get('title', '').strip()
    experiences = Experience.objects.prefetch_related('skills').all()

    if title_query:
        experiences = experiences.filter(title__icontains=title_query)

    experiences_json = serializers.serialize('json', experiences)
    return HttpResponse(experiences_json, content_type='application/json')


@require_http_methods(['GET'])
def get_awards_json(request: HttpRequest):
    title_query = request.GET.get('title', '').strip()
    awards = Award.objects.all()

    if title_query:
        awards = awards.filter(title__icontains=title_query)

    awards_json = serializers.serialize('json', awards)
    return HttpResponse(awards_json, content_type='application/json')


@require_http_methods(['GET', 'POST'])
def delete_award(request: HttpRequest, award_id):
    award = get_object_or_404(Award, pk=award_id)

    if request.method == 'POST':
        award.delete()
        messages.success(request, 'Award successfully deleted!')

    return redirect('main:show_awards')


def _save_record(request, form_class, instance, label, list_view):
    form = form_class(request.POST if request.method == 'POST' else None, instance=instance)
    editing = instance is not None
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'{label} successfully {"updated" if editing else "created"}!')
        return redirect(list_view)
    return render(request, 'main/record-form.html', {
        'name': 'Rozan', 'form': form, 'label': label,
        'editing': editing, 'list_view': list_view,
    })


@require_http_methods(['GET', 'POST'])
def create_experience(request):
    return _save_record(request, ExperienceForm, None, 'Experience', 'main:show_experience')


@require_http_methods(['GET', 'POST'])
def edit_experience(request, experience_id):
    experience = get_object_or_404(Experience, pk=experience_id)
    return _save_record(request, ExperienceForm, experience, 'Experience', 'main:show_experience')


def _delete_record(request, instance, label, list_view):
    if request.method == 'POST':
        instance.delete()
        messages.success(request, f'{label} successfully deleted!')
        return redirect(list_view)
    return render(request, 'main/record-delete.html', {
        'name': 'Rozan', 'record': instance, 'label': label,
        'list_view': list_view,
    })


@require_http_methods(['GET', 'POST'])
def delete_experience(request, experience_id):
    return _delete_record(request, get_object_or_404(Experience, pk=experience_id),
                          'Experience', 'main:show_experience')


@require_http_methods(['GET', 'POST'])
def register(request: HttpRequest):
    form = UserCreationForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Account has been created successfully. Let's login!")
        return redirect('main:login')

    context = {
        'name': 'Rozan',
        'form': form,
    }
    return render(request, 'main/register.html', context)


@require_http_methods(['GET', 'POST'])
def login_user(request: HttpRequest):
    form = AuthenticationForm(request, data=request.POST or None)

    if request.method == 'POST' and form.is_valid():
        login(request, form.get_user())
        return redirect('main:index')

    context = {
        'name': 'Rozan',
        'form': form,
    }
    return render(request, 'main/login.html', context)


def logout_user(request):
    logout(request)
    return redirect('main:index')
