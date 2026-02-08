from django.http import HttpResponse
from django.shortcuts import render
from store.models import Product, ReviewRating
def home(req):
    products=Product.objects.all().filter(is_available=True).order_by('created_date')

     #get the review rating
    for product  in products:
        reviews=ReviewRating.objects.filter(product_id=product.id,status=True)
    context={
        'products':products,
        'reviews':reviews,
    }
    return render(req,'home.html',context)