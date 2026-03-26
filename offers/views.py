from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from .models import Offer

def home(request):
    # just renders the about us page, no database needed
    return render(request, 'offers/home.html')

def find(request):
    # this is where all the offers show up
    offers = Offer.objects.all().order_by('-created_at')
    return render(request, 'offers/find.html', {'offers': offers})

def post_offer(request):
    if request.method == 'POST':
        Offer.objects.create(
            name=request.POST['name'],
            title=request.POST['title'],
            description=request.POST['description'],
            category=request.POST['category'],
            offer_type=request.POST['offer_type'],
            price=request.POST.get('price') or None,
            location=request.POST['location'],
        )
        return redirect('find')
    return render(request, 'offers/post_offer.html', {'categories': Offer.CATEGORY_CHOICES})