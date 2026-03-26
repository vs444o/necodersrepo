from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponseForbidden
from django.utils import timezone
from django.conf import settings
import math

from .forms import ExtendedUserCreationForm
from .models import Offer, Application, Notification   # ← added Notification


def home(request):
    return render(request, 'offers/home.html')


@login_required
def find(request):
    offers = list(Offer.objects.select_related('created_by').all())

    if request.user.user_type == 'worker':
        already_applied_ids = set(
            Application.objects
            .filter(worker=request.user)
            .values_list('offer_id', flat=True)
        )
    else:
        already_applied_ids = set()

    is_worker = getattr(request.user, 'user_type', None) == 'worker'
    has_coords = request.user.latitude is not None and request.user.longitude is not None

    if is_worker and has_coords:
        worker_lat = float(request.user.latitude)
        worker_lng = float(request.user.longitude)

        def haversine_km(lat1, lon1, lat2, lon2):
            radius_km = 6371.0
            d_lat = math.radians(lat2 - lat1)
            d_lon = math.radians(lon2 - lon1)
            a = (
                math.sin(d_lat / 2) ** 2
                + math.cos(math.radians(lat1))
                * math.cos(math.radians(lat2))
                * math.sin(d_lon / 2) ** 2
            )
            return radius_km * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        for offer in offers:
            offer.distance_km = None
            if (
                offer.status == 'waiting'
                and offer.latitude is not None
                and offer.longitude is not None
            ):
                offer.distance_km = round(
                    haversine_km(worker_lat, worker_lng, float(offer.latitude), float(offer.longitude)), 1
                )

        offers.sort(key=lambda o: (
            0 if o.status == 'waiting' else 1,
            0 if o.distance_km is not None else 1,
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
    })


@login_required
def post_offer(request):
    if request.method == 'POST':
        offer = Offer.objects.create(
            name=request.user.username,
            created_by=request.user,
            title=request.POST['title'],
            description=request.POST['description'],
            category=request.POST['category'],
            offer_type=request.POST['offer_type'],
            price=request.POST.get('price') or None,
            location=request.POST['location'],
            latitude=request.POST.get('latitude') or None,
            longitude=request.POST.get('longitude') or None,
            status='waiting',
        )
        return redirect('find')

    return render(request, 'offers/post_offer.html', {
        'categories': Offer.CATEGORY_CHOICES,
        'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY,
    })


@login_required
def apply_offer(request, pk):
    if request.method != 'POST':
        return redirect('find')

    if request.user.user_type != 'worker':
        return HttpResponseForbidden('Only workers can apply.')

    offer = get_object_or_404(Offer, pk=pk)

    if offer.status != 'waiting':
        return redirect('find')

    application, created = Application.objects.get_or_create(
        offer=offer,
        worker=request.user,
    )

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

    if getattr(request.user, 'user_type', None) != 'worker':
        return HttpResponseForbidden('Only workers can accept requests.')

    offer = get_object_or_404(Offer, pk=pk)
    if offer.status != 'waiting':
        return redirect('find')

    offer.status = 'accepted'
    offer.accepted_by = request.user
    offer.accepted_at = timezone.now()
    offer.save(update_fields=['status', 'accepted_by', 'accepted_at'])
    return redirect('find')


@login_required
def complete_offer(request, pk):
    if request.method != 'POST':
        return redirect('find')

    offer = get_object_or_404(Offer, pk=pk)
    if offer.status != 'accepted':
        return redirect('find')

    if offer.accepted_by_id != request.user.id:
        return HttpResponseForbidden('Only the accepting worker can complete it.')

    offer.status = 'completed'
    offer.completed_by = request.user
    offer.completed_at = timezone.now()
    offer.save(update_fields=['status', 'completed_by', 'completed_at'])
    return redirect('find')

@login_required
def my_posts(request):
    if request.user.user_type != 'needer':
        return HttpResponseForbidden('This page is only for needers.')

    offers = (
        Offer.objects
        .filter(created_by=request.user)
        .prefetch_related('applications__worker')
        .order_by('-created_at')
    )

    unread = list(request.user.notifications.filter(read=False))

    request.user.notifications.filter(read=False).update(read=True)

    return render(request, 'offers/my_posts.html', {
        'offers': offers,
        'unread': unread,       # shown as banners at the top
    })


def signup_view(request):
    if request.method == 'POST':
        form = ExtendedUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = ExtendedUserCreationForm()

    return render(request, 'registration/signup.html', {
        'form': form,
        'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY,
    })

@login_required
def accept_application(request, pk):
    if request.method != 'POST':
        return redirect('my_posts')

    if request.user.user_type != 'needer':
        return HttpResponseForbidden('Only needers can accept applications.')

    application = get_object_or_404(Application, pk=pk)
    offer = application.offer

    if offer.created_by != request.user:
        return HttpResponseForbidden('You can only manage your own posts.')

    if offer.status != 'waiting':
        return redirect('my_posts')

    application.status = 'accepted'
    application.save(update_fields=['status'])

    Application.objects.filter(
        offer=offer
    ).exclude(pk=application.pk).update(status='rejected')

    offer.status = 'accepted'
    offer.accepted_by = application.worker
    offer.accepted_at = timezone.now()
    offer.save(update_fields=['status', 'accepted_by', 'accepted_at'])

    Notification.objects.create(
        user=application.worker,
        message=f"You were accepted for: {offer.title}!",
    )

    return redirect('my_posts')    

@login_required
def my_jobs(request):
    if request.user.user_type != 'worker':
        return HttpResponseForbidden('This page is only for workers.')

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