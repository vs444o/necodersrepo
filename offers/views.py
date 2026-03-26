from django.shortcuts import render, redirect
from .models import Offer

def home(request):
    offers = Offer.objects.all().order_by('-created_at')  # newest first
    return render(request, 'offers/home.html', {'offers': offers})

def post_offer(request):
    if request.method == 'POST':
        # grab what was submitted in the form
        Offer.objects.create(
            name=request.POST['name'],
            title=request.POST['title'],
            description=request.POST['description'],
            category=request.POST['category'],
            offer_type=request.POST['offer_type'],
            price=request.POST.get('price') or None,
            location=request.POST['location'],
        )
        return redirect('home')  # after posting, go back to homepage

    # if it's just a regular page load, show the empty form
    return render(request, 'offers/post_offer.html', {
        'categories': Offer.CATEGORY_CHOICES
    })