from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, update_session_auth_hash
from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponseForbidden
from django.utils import timezone
from django.conf import settings
from django.views.decorators.http import require_POST
from django.db.models import Avg
from django.contrib import messages
from .forms import NeederSignupForm, WorkerSignupForm
from .models import Offer, Application, Notification, Rating, WorkerProfile
from .emails import send_notification_email

def home(request):
    if request.user.is_authenticated and request.user.user_type == 'worker':
        return redirect('dashboard')

    if request.user.is_authenticated and request.user.user_type == 'needer':
        offers = (
            Offer.objects
            .filter(created_by=request.user)
            .prefetch_related('applications__worker', 'applications__worker__worker_profile')
            .order_by('-created_at')
        )
        rated_offer_ids = set(
            Rating.objects.filter(needer=request.user).values_list('offer_id', flat=True)
        )
        unread = list(request.user.notifications.filter(read=False))
        request.user.notifications.filter(read=False).update(read=True)
        return render(request, 'offers/home.html', {
            'offers': offers,
            'unread': unread,
            'rated_offer_ids': rated_offer_ids,
        })

    return render(request, 'offers/home.html')


@login_required
def find(request):
    return redirect('dashboard')


@login_required
def post_offer(request):
    if request.method == 'POST':
        lat = request.POST.get('latitude')
        lng = request.POST.get('longitude')
        location = (request.POST.get('location') or '').strip()
        offer_type = request.POST.get('offer_type')
        price = None
        if offer_type == 'paid':
            price = request.POST.get('price') or None

        if location and (not lat or not lng):
            return render(request, 'offers/post_offer.html', {
                'categories': Offer.CATEGORY_CHOICES,
                'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY,
                'error': 'Моля, изберете адрес от предложенията.',
            })

        Offer.objects.create(
            name=request.user.username,
            created_by=request.user,
            title=request.POST['title'],
            description=request.POST['description'],
            category=request.POST['category'],
            offer_type=offer_type,
            price=price,
            location=location,
            city=request.POST.get('city', ''),
            latitude=round(float(lat), 6) if lat else None,
            longitude=round(float(lng), 6) if lng else None,
            status='waiting',
        )
        return redirect('home')

    return render(request, 'offers/post_offer.html', {
        'categories': Offer.CATEGORY_CHOICES,
        'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY,
    })


@login_required
def dashboard(request):
    if request.user.user_type != 'worker':
        return HttpResponseForbidden()

    applications = (
        Application.objects
        .filter(worker=request.user)
        .select_related('offer', 'offer__created_by')
        .order_by('-created_at')
    )

    total_jobs = applications.count()
    completed_jobs = applications.filter(offer__status='completed').count()
    upcoming_jobs = applications.filter(offer__status__in=['waiting', 'accepted']).count()

    unique_needers_helped = (
        Offer.objects
        .filter(accepted_by=request.user, status='completed')
        .values('created_by')
        .distinct()
        .count()
    )

    upcoming_applications = applications.filter(offer__status__in=['waiting', 'accepted'])

    rating_agg = Rating.objects.filter(worker=request.user).aggregate(avg=Avg('overall_score'))
    avg_rating = rating_agg['avg']

    offers = list(Offer.objects.filter(status='waiting').select_related('created_by'))
    already_applied_ids = set(
        Application.objects.filter(worker=request.user).values_list('offer_id', flat=True)
    )

    if request.user.latitude and request.user.longitude:
        worker_lat = float(request.user.latitude)
        worker_lng = float(request.user.longitude)

        def simple_distance(lat1, lon1, lat2, lon2):
            dlat = (lat2 - lat1) * 111
            dlon = (lon2 - lon1) * 75
            return round((dlat**2 + dlon**2) ** 0.5, 1)

        for offer in offers:
            if offer.latitude and offer.longitude:
                offer.distance_km = simple_distance(
                    worker_lat, worker_lng,
                    float(offer.latitude), float(offer.longitude)
                )
            else:
                offer.distance_km = None

        offers.sort(key=lambda o: (
            o.distance_km if o.distance_km is not None else float('inf'),
            -o.created_at.timestamp(),
        ))
    else:
        for offer in offers:
            offer.distance_km = None
        offers.sort(key=lambda o: o.created_at, reverse=True)

    return render(request, 'offers/dashboard.html', {
        'total_jobs': total_jobs,
        'completed_jobs': completed_jobs,
        'upcoming_jobs': upcoming_jobs,
        'unique_needers_helped': unique_needers_helped,
        'upcoming_applications': upcoming_applications,
        'offers': offers,
        'already_applied_ids': already_applied_ids,
        'avg_rating': avg_rating,
    })


@login_required
def apply_offer(request, pk):
    if request.method != 'POST':
        return redirect('dashboard')
    offer = get_object_or_404(Offer, pk=pk)
    if request.user.user_type != 'worker':
        return HttpResponseForbidden()
    application, created = Application.objects.get_or_create(offer=offer, worker=request.user)
    if created and offer.created_by:
        notif_text = f"{request.user.username} applied for: {offer.title}"
        Notification.objects.create(
            user=offer.created_by,
            message=f"{request.user.username} кандидатства за: {offer.title}",
        )
        send_notification_email(offer.created_by, notif_text)
    return redirect('dashboard')


@login_required
def accept_offer(request, pk):
    if request.method != 'POST':
        return redirect('dashboard')
    offer = get_object_or_404(Offer, pk=pk)
    if request.user.user_type != 'worker' or offer.status != 'waiting':
        return HttpResponseForbidden()
    offer.status = 'accepted'
    offer.accepted_by = request.user
    offer.save(update_fields=['status', 'accepted_by'])
    return redirect('dashboard')


@login_required
def accept_application(request, pk):
    if request.method != 'POST':
        return redirect('home')
    application = get_object_or_404(Application, pk=pk)
    offer = application.offer
    if offer.created_by != request.user or offer.status != 'waiting':
        return HttpResponseForbidden()

    application.status = 'accepted'
    application.save(update_fields=['status'])

    Application.objects.filter(offer=offer).exclude(pk=application.pk).update(status='rejected')

    offer.status = 'accepted'
    offer.accepted_by = application.worker
    offer.save(update_fields=['status', 'accepted_by'])

    Notification.objects.create(
        user=application.worker,
        message=f"Приети сте за: {offer.title}! Телефон на търсещия помощ: {offer.created_by.phone}",
    )
    send_notification_email(application.worker, f"You were accepted for: {offer.title}!")
    return redirect('home')


@login_required
def reject_application(request, pk):
    if request.method != 'POST':
        return redirect('my_posts')
    application = get_object_or_404(Application, pk=pk)
    offer = application.offer
    if offer.created_by != request.user:
        return HttpResponseForbidden()
    application.status = 'rejected'
    application.save(update_fields=['status'])
    Notification.objects.create(
        user=application.worker,
        message=f"Кандидатурата ви за \"{offer.title}\" беше отхвърлена.",
    )
    return redirect('my_posts')


@login_required
def withdraw_application(request, pk):
    if request.method != 'POST':
        return redirect('my_jobs')
    application = get_object_or_404(Application, pk=pk, worker=request.user)
    offer = application.offer
    if offer.status == 'accepted' and offer.accepted_by == request.user:
        offer.status = 'waiting'
        offer.accepted_by = None
        offer.save(update_fields=['status', 'accepted_by'])
    application.delete()
    messages.success(request, 'Оттеглихте кандидатурата си успешно.')
    return redirect('my_jobs')


@login_required
def complete_offer(request, pk):
    if request.method != 'POST':
        return redirect('my_jobs')
    offer = get_object_or_404(Offer, pk=pk)
    if offer.accepted_by != request.user:
        return HttpResponseForbidden()
    offer.status = 'completed'
    offer.completed_at = timezone.now()
    offer.completed_by = request.user
    offer.save(update_fields=['status', 'completed_at', 'completed_by'])
    return redirect('my_jobs')


@login_required
def my_posts(request):
    if request.user.user_type != 'needer':
        return HttpResponseForbidden()
    offers = (
        Offer.objects
        .filter(created_by=request.user)
        .prefetch_related('applications__worker', 'applications__worker__worker_profile')
        .order_by('-created_at')
    )
    rated_offer_ids = set(Rating.objects.filter(needer=request.user).values_list('offer_id', flat=True))
    unread = list(request.user.notifications.filter(read=False))
    request.user.notifications.filter(read=False).update(read=True)
    return render(request, 'offers/my_posts.html', {
        'offers': offers,
        'rated_offer_ids': rated_offer_ids,
        'unread': unread,
    })


@login_required
def my_jobs(request):
    if request.user.user_type != 'worker':
        return HttpResponseForbidden()
    applications = (
        Application.objects
        .filter(worker=request.user)
        .select_related('offer')
        .order_by('-created_at')
    )
    unread = list(request.user.notifications.filter(read=False))
    request.user.notifications.filter(read=False).update(read=True)
    return render(request, 'offers/my_jobs.html', {
        'applications': applications,
        'unread': unread,
    })


@login_required
@require_POST
def rate_offer(request, pk):
    offer = get_object_or_404(Offer, pk=pk, created_by=request.user, status='completed')
    if Rating.objects.filter(offer=offer).exists():
        return redirect('home')

    def get_score(name):
        return max(1.0, min(5.0, float(request.POST.get(name, 5.0))))

    perf = get_score('performance')
    beh = get_score('behaviour')
    spd = get_score('speed')

    Rating.objects.create(
        offer=offer,
        worker=offer.accepted_by,
        needer=request.user,
        performance=perf,
        behaviour=beh,
        speed=spd,
        overall_score=round((perf + beh + spd) / 3, 1)
    )
    return redirect('home')


@login_required
def profile(request):
    return render(request, 'offers/profile.html')


@login_required
def profile_change(request, field):
    if request.method != 'POST':
        return redirect('profile')

    value1 = request.POST.get('value1', '').strip()
    value2 = request.POST.get('value2', '').strip()

    if field == 'password':
        old_password = request.POST.get('old_password', '')
        if not request.user.check_password(old_password):
            messages.error(request, 'Грешна стара парола.')
            return redirect('profile')
        if value1 != value2:
            messages.error(request, 'Новите пароли не съвпадат.')
            return redirect('profile')
        request.user.set_password(value1)
        request.user.save()
        update_session_auth_hash(request, request.user)
        messages.success(request, 'Паролата е сменена успешно.')
        return redirect('profile')

    if value1 != value2:
        messages.error(request, 'Стойностите не съвпадат.')
        return redirect('profile')

    if field == 'username':
        request.user.username = value1
        request.user.save()
    elif field == 'email':
        request.user.email = value1
        request.user.save()
    elif field == 'address':
        request.user.address = value1
        request.user.save()
    elif field == 'phone':
        if request.user.user_type == 'worker':
            prof, _ = WorkerProfile.objects.get_or_create(user=request.user)
            prof.phone = value1
            prof.save()
        else:
            request.user.phone = value1
            request.user.save()
    elif field == 'skills':
        if request.user.user_type == 'worker':
            prof, _ = WorkerProfile.objects.get_or_create(user=request.user)
            prof.skills = value1
            prof.save()

    messages.success(request, 'Промяната е запазена успешно.')
    return redirect('profile')


def signup_needer(request):
    if request.method == 'POST':
        form = NeederSignupForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.phone = request.POST.get('phone', '')
            user.save()
            login(request, user)
            return redirect('home')
    else:
        form = NeederSignupForm()
    return render(request, 'registration/signup.html', {
        'form': form,
        'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY,
        'signup_kind': 'needer',
    })


def signup_worker(request):
    if request.method == 'POST':
        form = WorkerSignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = WorkerSignupForm()
    return render(request, 'registration/signup.html', {
        'form': form,
        'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY,
        'signup_kind': 'worker',
    })