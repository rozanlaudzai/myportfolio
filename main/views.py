import datetime
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
    JsonResponse,
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
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

from .models import (
    Experience,
    Award,
)
from .forms import (
    AwardForm,
    ExperienceForm,
)


login_url = '/login/'


def is_editor(request: HttpRequest) -> bool:
    return request.user.groups.filter(name='Editor').exists()


@require_http_methods(['GET'])
def index(request: HttpRequest):
    last_login = request.COOKIES.get('last_login', 'There is no login session yet.')
    context = {
        'name': 'Rozan',
        'npm': '2506547544',
        'study_program': 'S1 Ilmu Komputer',
        'bio': 'Go & C++ Enjoyer. Python & JavaScript Hater.',
        'last_login': last_login,
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
        'is_editor': is_editor(request),
    }
    return render(request, 'main/experience.html', context)


@require_http_methods(['GET'])
def show_awards(request: HttpRequest):
    title_query = request.GET.get('title', '').strip()

    context = {
        'name': 'Rozan',
        'title_query': title_query,
        'is_editor': is_editor(request),
        'form': AwardForm(),
    }

    return render(request, 'main/awards.html', context)


@require_http_methods(['POST'])
def create_award_ajax(request: HttpRequest):
    if not request.user.is_superuser:
        return JsonResponse(
            {'message': 'Only the portfolio owner can add awards.'}, status=403,
        )

    form = AwardForm(request.POST)
    if form.is_valid():
        award = form.save()
        return JsonResponse(
            {'message': 'Award successfully added.', 'pk': str(award.pk)},
            status=201,
        )
    return JsonResponse({'errors': form.errors.get_json_data()}, status=400)


@login_required(login_url=login_url)
@require_http_methods(['GET', 'POST'])
def create_award(request: HttpRequest):
    if not request.user.is_superuser:
        raise PermissionDenied

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


@login_required(login_url=login_url)
@require_http_methods(['GET', 'POST'])
def edit_award(request: HttpRequest, award_id):
    if not request.user.is_superuser and not is_editor(request):
        raise PermissionDenied

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
    awards = Award.objects.prefetch_related('starred_by').all()

    if title_query:
        awards = awards.filter(title__icontains=title_query)

    data = []
    for award in awards:
        starred_users = award.starred_by.all()
        is_starred = request.user in starred_users if request.user.is_authenticated else False
        starred_by_names = ', '.join([u.username for u in starred_users])

        data.append({
            'pk': str(award.id),
            'fields': {
                'title': award.title,
                'issuer': award.issuer,
                'description': award.description,
                'awarded_at': award.awarded_at,
                'star_count': starred_users.count(),
                'is_starred': is_starred,
                'starred_by_names': starred_by_names,
            }
        })

    return JsonResponse(data, safe=False)


@login_required(login_url=login_url)
@require_http_methods(['GET', 'POST'])
def delete_award(request: HttpRequest, award_id):
    if not request.user.is_superuser:
        raise PermissionDenied

    award = get_object_or_404(Award, pk=award_id)

    if request.method == 'POST':
        award.delete()
        messages.success(request, 'Award successfully deleted!')

    return redirect('main:show_awards')


@login_required(login_url=login_url)
@require_http_methods(['GET', 'POST'])
def _save_record(request: HttpRequest, form_class, instance, label, list_view):
    if not request.user.is_superuser and not is_editor(request):
        raise PermissionDenied

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


@login_required(login_url=login_url)
@require_http_methods(['GET', 'POST'])
def create_experience(request: HttpRequest):
    if not request.user.is_superuser:
        raise PermissionDenied

    return _save_record(request, ExperienceForm, None, 'Experience', 'main:show_experience')


@login_required(login_url=login_url)
@require_http_methods(['GET', 'POST'])
def edit_experience(request: HttpRequest, experience_id):
    if not request.user.is_superuser and not is_editor(request):
        raise PermissionDenied

    experience = get_object_or_404(Experience, pk=experience_id)
    return _save_record(request, ExperienceForm, experience, 'Experience', 'main:show_experience')


@login_required(login_url=login_url)
@require_http_methods(['GET', 'POST'])
def _delete_record(request: HttpRequest, instance, label, list_view):
    if not request.user.is_superuser:
        raise PermissionDenied

    if request.method == 'POST':
        instance.delete()
        messages.success(request, f'{label} successfully deleted!')
        return redirect(list_view)
    return render(request, 'main/record-delete.html', {
        'name': 'Rozan', 'record': instance, 'label': label,
        'list_view': list_view,
    })


@login_required(login_url=login_url)
@require_http_methods(['GET', 'POST'])
def delete_experience(request: HttpRequest, experience_id):
    if not request.user.is_superuser:
        raise PermissionDenied

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
        user = form.get_user()
        login(request, user)
        response = redirect('main:index')
        response.set_cookie('last_login', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        return response

    context = {
        'name': 'Rozan',
        'form': form,
    }
    return render(request, 'main/login.html', context)


@require_http_methods(['GET'])
def logout_user(request):
    logout(request)
    response = redirect('main:index')
    response.delete_cookie('last_login')
    return response


@login_required(login_url=login_url)
@require_http_methods(['GET', 'POST'])
def toggle_star(request: HttpRequest, award_id):
    award = get_object_or_404(Award, pk=award_id)

    if request.method == 'POST':
        # Kalau akun ini sudah pernah memberi star, batalkan star-nya.
        # Kalau belum, tambahkan star.
        if request.user in award.starred_by.all():
            award.starred_by.remove(request.user)
        else:
            award.starred_by.add(request.user)

    return redirect('main:show_awards')

