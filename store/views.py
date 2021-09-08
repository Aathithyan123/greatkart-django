from django.core.checks import messages
from store.forms import ReviewFrom
from carts.models import CartItem
from category.models import Category
from django.shortcuts import get_object_or_404, redirect, render
from category.models import Category
from carts.views import _cart_id
from .models import Product, ProductGallery, ReviewRating
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib import messages
from orders.models import OrderProduct

# Create your views here.
def store(request, category_slug=None):
    categories = None
    products = None

    if category_slug != None:
        categories = get_object_or_404(Category, slug=category_slug)
        products = Product.objects.filter(category=categories, is_available = True)
        paginator = Paginator(products, 1)
        page = request.GET.get('page')
        paged_products = paginator.get_page(page)
        products_count = products.count()
    else:
        products = Product.objects.all().filter(is_available = True ).order_by('id')
        paginator = Paginator(products, 3)
        page = request.GET.get('page')
        paged_products = paginator.get_page(page)
        products_count = products.count()
    
    context = {
        'products': paged_products,
        'products_count':products_count
    }
    return render(request, 'store/store.html', context)

def product_detail(request, category_slug, product_slug): 
    try:
        single_product = Product.objects.get(category__slug = category_slug, slug=product_slug)
        in_cart = CartItem.objects.filter(cart__cart_id=_cart_id(request), product= single_product).exists()
    except Exception as e:
        raise e
    if(request.user.is_authenticated):
        try:
            orderproduct = OrderProduct.objects.filter(user=request.user, product_id=single_product.id).exists()
        except OrderProduct.DoesNotExist:
            orderproduct = None
    else:
        orderproduct = None

    #Get the reviews
    reviews = ReviewRating.objects.filter(product_id = single_product.id, status = True)

    #Get the product gallery
    product_gallery = ProductGallery.objects.filter(product_id=single_product.id)

    context = {
         'single_product': single_product,
         'in_cart'       : in_cart,
         'orderproduct': orderproduct,
         'reviews' : reviews,
         'product_gallery': product_gallery,
    }   

    return render(request, 'store/product_detail.html', context)

def search(request):
    products_count = 0
    if 'keyword' in request.GET:
        keyword = request.GET['keyword']
        if keyword:
            products = Product.objects.order_by('-created_date').filter(Q(description__icontains=keyword) | Q(product_name__icontains=keyword))
            products_count = products.count()
    
    context = {
        'products' : products,
        'products_count':products_count
    }

    return render(request, 'store/store.html', context)

def submit_review(request, product_id):
    url = request.META.get('HTTP_REFERER')
    if request.method == 'POST':
        try:
            reviews = ReviewRating.objects.get(user__id=request.user.id, product__id=product_id)
            form = ReviewFrom(request.POST, instance=reviews)
            form.save()
            messages.success(request, 'Thank you! Your reviwes has ben updated.')
            return redirect(url)
        except ReviewRating.DoesNotExist:
            form = ReviewFrom(request.POST)
            if form.is_valid():
                data = ReviewRating()
                data.subject = form.cleaned_data['subject']
                data.rating = form.cleaned_data['rating']
                data.review = form.cleaned_data['review']
                data.ip = request.META.get('REMOTE_ADDR')
                data.product_id = product_id
                data.user_id = request.user.id
                data.save()
                messages.success(request,'Thank  you! your review has been submitted.')
                return redirect(url)