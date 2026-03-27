from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponseForbidden
from django.utils import timezone
from django.conf import settings
import math

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

        return render(request, 'offers/home.html', {
            'offers': offers,
            'unread': unread,
        })
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

        def haversine_km(lat1, lon1, lat2, lon2):
            radius_km = 6371.0
            d_lat = math.radians(lat2 - lat1)
            d_lon = math.radians(lon2 - lon1)
            a = math.sin(d_lat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon/2)**2
            return radius_km * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        for offer in offers:
            if offer.latitude and offer.longitude:
                offer.distance_km = round(haversine_km(worker_lat, worker_lng, float(offer.latitude), float(offer.longitude)), 1)
            else:
                offer.distance_km = None
        
        offers.sort(key=lambda o: (o.status != 'waiting', o.distance_km if o.distance_km is not None else 9999))
    
    return render(request, 'offers/find.html', {'offers': offers, 'already_applied_ids': already_applied_ids})

@login_required
def post_offer(request):
    if request.method == 'POST':
        lat = request.POST.get('latitude')
        lng = request.POST.get('longitude')
        
        Offer.objects.create(
            name=request.user.username,
            created_by=request.user,
            title=request.POST['title'],
            description=request.POST['description'],
            category=request.POST['category'],
            offer_type=request.POST['offer_type'],
            location=request.POST['location'],
            city=request.POST.get('city'),
            # Rounding to 6 decimals for database constraints
            latitude=round(float(lat), 6) if lat else None,
            longitude=round(float(lng), 6) if lng else None,
            status='waiting',
        )
        return redirect('home')
    return render(request, 'offers/post_offer.html', {'categories': Offer.CATEGORY_CHOICES})

def signup_view(request):
    if request.method == 'POST':
        form = ExtendedUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            # Rounding coordinates to fix the "no more than 6 decimal places" error
            if user.latitude: user.latitude = round(float(user.latitude), 6)
            if user.longitude: user.longitude = round(float(user.longitude), 6)
            user.save()
            login(request, user)
            return redirect('home')
    else:
        form = ExtendedUserCreationForm()
    return render(request, 'registration/signup.html', {
        'form': form, 
        'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY
    })

@login_required
def accept_application(request, pk):
    application = get_object_or_404(Application, pk=pk)
    if application.offer.created_by == request.user:
        application.status = 'accepted'
        application.save()
        application.offer.status = 'accepted'
        application.offer.accepted_by = application.worker
        application.offer.save()
        Notification.objects.create(user=application.worker, message=f"Accepted for {application.offer.title}")
    return redirect('home')

@login_required
def apply_offer(request, pk):
    offer = get_object_or_404(Offer, pk=pk)
    if request.user.user_type == 'worker':
        Application.objects.get_or_create(offer=offer, worker=request.user)
        Notification.objects.create(user=offer.created_by, message=f"{request.user.username} applied to {offer.title}")
    return redirect('find')

@login_required
def accept_offer(request, pk):
    offer = get_object_or_404(Offer, pk=pk)
    if request.user.user_type == 'worker':
        offer.status = 'accepted'
        offer.accepted_by = request.user
        offer.save()
    return redirect('find')

@login_required
def complete_offer(request, pk):
    offer = get_object_or_404(Offer, pk=pk)
    if offer.accepted_by == request.user:
        offer.status = 'completed'
        offer.save()
    return redirect('find')

@login_required
def my_posts(request):
    offers = Offer.objects.filter(created_by=request.user)
    return render(request, 'offers/my_posts.html', {'offers': offers})

@login_required
def my_jobs(request):
    applications = Application.objects.filter(worker=request.user)
    return render(request, 'offers/my_jobs.html', {'applications': applications})