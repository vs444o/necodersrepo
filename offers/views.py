from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponseForbidden
from django.utils import timezone
from django.conf import settings

from .forms import ExtendedUserCreationForm
from .models import Offer, Application, Notification


def home(request):
    if request.user.is_authenticated and request.user.user_type == 'needer':
        offers = (
            Offer.objects
            .filter(created_by=request.user)
            .prefetch_related('applications__worker')
            .order_by('-created_at')
        )
        unread = list(request.user.notifications.filter(read=False))
        request.user.notifications.filter(read=False).update(read=True)
        return render(request, 'offers/home.html', {'offers': offers, 'unread': unread})
    if request.user.is_authenticated and request.user.user_type == 'worker':
        applications = Application.objects.filter(worker=request.user)
        stats = {
            'applied': applications.filter(status='pending').count(),
            'accepted': applications.filter(status='accepted').count(),
            'completed': applications.filter(status='completed').count(),
        }
        unread = list(request.user.notifications.filter(read=False))
        request.user.notifications.filter(read=False).update(read=True)
        return render(request, 'offers/home.html', {'stats': stats, 'unread': unread})
    return render(request, 'offers/home.html')


@login_required
def find(request):
    offers = list(Offer.objects.select_related('created_by').all())
    already_applied_ids = set()

    if request.user.user_type == 'worker':
        already_applied_ids = set(
            Application.objects.filter(worker=request.user).values_list('offer_id', flat=True)
        )

    if request.user.user_type == 'worker' and request.user.latitude and request.user.longitude:
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
            0 if o.status == 'waiting' else 1,
            o.distance_km if o.distance_km is not None else float('inf'),
            -o.created_at.timestamp(),
        ))
    else:
        for offer in offers:
            offer.distance_km = None
        offers.sort(key=lambda o: o.created_at, reverse=True)

    return render(request, 'offers/find.html', {
        'offers': offers,
        'already_applied_ids': already_applied_ids,
        'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY,
    })


@login_required
def post_offer(request):
    if request.method == 'POST':
        lat = request.POST.get('latitude')
        lng = request.POST.get('longitude')
        location = (request.POST.get('location') or '').strip()
        if location and (not lat or not lng):
            return render(request, 'offers/post_offer.html', {
                'categories': Offer.CATEGORY_CHOICES,
                'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY,
                'error': 'Pick an address from Google suggestions so we can save the exact location.',
            })
        Offer.objects.create(
            name=request.user.username,
            created_by=request.user,
            title=request.POST['title'],
            description=request.POST['description'],
            category=request.POST['category'],
            offer_type=request.POST['offer_type'],
            price=request.POST.get('price') or None,
            location=location,
            city=request.POST.get('city'),
            # Rounding to 6 decimals for database constraints
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
def apply_offer(request, pk):
    if request.method != 'POST':
        return redirect('find')
    offer = get_object_or_404(Offer, pk=pk)
    if request.user.user_type != 'worker':
        return HttpResponseForbidden()
    application, created = Application.objects.get_or_create(offer=offer, worker=request.user)
    if created and offer.created_by:
        Notification.objects.create(
            user=offer.created_by,
            message=f"{request.user.username} applied for your request: {offer.title}",
        )
    return redirect('find')


@login_required
def accept_offer(request, pk):
    if request.method != 'POST':
        return redirect('find')
    offer = get_object_or_404(Offer, pk=pk)
    if request.user.user_type != 'worker':
        return HttpResponseForbidden()
    if offer.status != 'waiting':
        return redirect('find')
    offer.status = 'accepted'
    offer.accepted_by = request.user
    offer.accepted_at = timezone.now()
    offer.save(update_fields=['status', 'accepted_by', 'accepted_at'])
    return redirect('find')


@login_required
def accept_application(request, pk):
    if request.method != 'POST':
        return redirect('home')
    application = get_object_or_404(Application, pk=pk)
    offer = application.offer
    if offer.created_by != request.user:
        return HttpResponseForbidden()
    if offer.status != 'waiting':
        return redirect('home')

    application.status = 'accepted'
    application.save(update_fields=['status'])

    Application.objects.filter(offer=offer).exclude(pk=application.pk).update(status='rejected')

    offer.status = 'accepted'
    offer.accepted_by = application.worker
    offer.accepted_at = timezone.now()
    offer.save(update_fields=['status', 'accepted_by', 'accepted_at'])

    Notification.objects.create(
        user=application.worker,
        message=f"You were accepted for: {offer.title}!",
    )
    return redirect('home')


@login_required
def complete_offer(request, pk):
    if request.method != 'POST':
        return redirect('find')
    offer = get_object_or_404(Offer, pk=pk)
    if offer.accepted_by != request.user:
        return HttpResponseForbidden()
    offer.status = 'completed'
    offer.completed_by = request.user
    offer.completed_at = timezone.now()
    offer.save(update_fields=['status', 'completed_by', 'completed_at'])
    return redirect('find')


@login_required
def my_posts(request):
    if request.user.user_type != 'needer':
        return HttpResponseForbidden()
    offers = (
        Offer.objects
        .filter(created_by=request.user)
        .prefetch_related('applications__worker')
        .order_by('-created_at')
    )
    unread = list(request.user.notifications.filter(read=False))
    request.user.notifications.filter(read=False).update(read=True)
    return render(request, 'offers/my_posts.html', {'offers': offers, 'unread': unread})


@login_required
def my_jobs(request):
    if request.user.user_type != 'worker':
        return HttpResponseForbidden()
    applications = (
        Application.objects
        .filter(worker=request.user)
        .select_related('offer', 'offer__created_by')
        .order_by('-created_at')
    )
    unread = list(request.user.notifications.filter(read=False))
    request.user.notifications.filter(read=False).update(read=True)
    return render(request, 'offers/my_jobs.html', {
        'applications': applications,
        'unread': unread,
    })


def signup_view(request):
    if request.method == 'POST':
        form = ExtendedUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            if user.latitude:
                user.latitude = round(float(user.latitude), 6)
            if user.longitude:
                user.longitude = round(float(user.longitude), 6)
            user.save()
            login(request, user)
            return redirect('home')
    else:
        form = ExtendedUserCreationForm()
    return render(request, 'registration/signup.html', {
        'form': form,
        'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY,
    })