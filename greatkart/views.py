from django.shortcuts import render
from store.models import Product, ReviewRating

def home(req):
    products = Product.objects.filter(is_available=True).order_by('created_date')

    reviews = ReviewRating.objects.filter(status=True)

    context = {
        'products': products,
        'reviews': reviews,
    }

    return render(req, 'home.html', context)
