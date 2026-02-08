from django.http import HttpResponse
from django.shortcuts import redirect, render,get_object_or_404
from carts.models import CartItem
from carts.views import _cart_id
from category.models import Category
from store.forms import ReviewForm
from .models import Product, ProductGallery, ReviewRating
from django.db.models import Q
from django.core.paginator import EmptyPage,PageNotAnInteger,Paginator
from django.contrib import messages
# Create your views here.
def store(req ,category_slug=None):
    categories=None
    products=None
    if category_slug != None: #selecting for category
        categories=get_object_or_404(Category,slug=category_slug)
        products=Product.objects.filter(category=categories,is_available=True)
        paginator= Paginator(products,1)#all 6 products will show in store
        page=req.GET.get('page')
        paged_products=paginator.get_page(page)
        product_count=products.count()
    else:#for all products
         products=Product.objects.all().filter(is_available=True).order_by('id')
         paginator= Paginator(products,3)#all 6 products will show in store
         page=req.GET.get('page')
         paged_products=paginator.get_page(page)
         product_count=products.count()


   
    context={
        'products':paged_products,
        'product_count': product_count,
    }
    return render(req,'store/store.html',context)


def product_detail(req,category_slug,product_slug):
    try:
        single_product=Product.objects.get(category__slug=category_slug,slug=product_slug) #to get categories slug
        in_cart=CartItem.objects.filter(cart__cart_id=_cart_id(req),product=single_product).exists() #true or false for add to cart i=for single item
    except Exception as e:
        raise e
    
    #get the review rating
    reviews=ReviewRating.objects.filter(product_id=single_product.id,status=True)

    #get the product gallery
    product_gallery=ProductGallery.objects.filter(product_id=single_product.id)



    context={
        "single_product":single_product,
        'in_cart':in_cart,
        'reviews':reviews,
        'product_gallery':product_gallery,
    }
    return render(req,'store/product_detail.html',context)


def search(req):
    if 'keyword' in req.GET: #if there is value in keyword
        keyword=req.GET['keyword'] #then we will be store in  variable keyword
        if keyword:#if keyword is not blank
            products=Product.objects.order_by('-created_date').filter(Q(description__icontains=keyword) | Q(product_name__icontains=keyword) )#it will found in desc related to keyword  and Q is used for query set we cant use or operator directly it will break the code
            product_count=products.count()
    
    context={
        'products':products,
        'product_count':product_count,
    }

    return render(req,'store/store.html' ,context)


def submit_review(req, product_id):
    url = req.META.get('HTTP_REFERER')

    if req.method == 'POST':
        try:
            reviews = ReviewRating.objects.get(
                user__id=req.user.id,
                product__id=product_id
            )
            form = ReviewForm(req.POST, instance=reviews)
            form.save()
            messages.success(req, 'Thank you! Your review has been updated')
            return redirect(url)

        except ReviewRating.DoesNotExist:
            form = ReviewForm(req.POST)
            if form.is_valid():
                data = ReviewRating()
                data.subject = form.cleaned_data['subject']
                data.rating = form.cleaned_data['rating']
                data.review = form.cleaned_data['review']
                data.ip = req.META.get('REMOTE_ADDR')
                data.product_id = product_id
                data.user_id = req.user.id
                data.save()
                messages.success(req, 'Thank you! Your review has been submitted')
                return redirect(url)
