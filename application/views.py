from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count, Max
from django.http import JsonResponse

from .forms import RegistrationForm, ProductForm, AdminRegistrationForm, AdminCustomerRegistrationForm, CategoryForm
from django.contrib.auth import authenticate, login
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.shortcuts import render
from django.shortcuts import render, get_object_or_404
from .models import Product, Category, Subcategory, Cart, CartItem
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import render
from .models import Category, Subcategory, Product
from .models import Profile, Category, Subcategory, Product
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


# Create your views here.
def index(request):
    grouped_data = []

    # Query all products
    products = Product.objects.all()

    # Group products by subcategory (if exists)
    subcategory_groups = (
        products.filter(subcategory__isnull=False)
        .values('subcategory__id', 'subcategory__name')
        .annotate(count=Count('id'))
    )

    for group in subcategory_groups:
        # Fetch the first product from this subcategory for the image
        representative_product = products.filter(subcategory__id=group['subcategory__id']).first()
        grouped_data.append({
            'name': group['subcategory__name'],  # Subcategory name
            'qty': group['count'],               # Number of products
            'image': representative_product.image.url if representative_product else None,
        })

    # Group remaining products by category (those without subcategories)
    category_groups = (
        products.filter(subcategory__isnull=True)
        .values('category__id', 'category__name')
        .annotate(count=Count('id'))
    )

    for group in category_groups:
        # Fetch the first product from this category for the image
        representative_product = products.filter(category__id=group['category__id']).first()
        grouped_data.append({
            'name': group['category__name'],  # Category name
            'qty': group['count'],           # Number of products
            'image': representative_product.image.url if representative_product else None,
        })

    return render(request, 'index.html', {'grouped_data': grouped_data})



def admin_data(request):
    return render(request, 'admin_data.html')

def customer_data(request):
    return render(request, 'customer_data.html')

def admin_category(request):
    return render(request, 'admin_category.html')

def contact(request):
    return render(request, 'contact.html',{'current_page':'contact'})

@login_required
def cart(request):
    # Fetch the user's cart
    cart = Cart.objects.filter(user=request.user).first()

    # Pass the cart to the template
    return render(request, 'cart.html', {
        'cart': cart,
        'current_page': 'cart'
    })

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        cart_item.quantity += 1
        cart_item.save()

    return JsonResponse({
        'message': f"{product.item_name} added to your cart!",
        'cart_count': cart.items.count(),  # Update cart count dynamically
    })

@login_required
def update_cart_item(request, item_id):
    if request.method == 'POST':
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        quantity = int(request.POST.get('quantity', cart_item.quantity))
        if quantity > 0:
            cart_item.quantity = quantity
            cart_item.save()
        else:
            cart_item.delete()  # Remove item if quantity is set to 0
    return redirect('cart')


@login_required
def remove_from_cart(request, item_id):
    # Fetch the cart item, ensuring it belongs to the logged-in user
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart_item.delete()  # Delete the item from the cart
    return redirect('cart')  # Redirect to the cart page


@login_required
def cart_count(request):
    cart = Cart.objects.filter(user=request.user).first()
    count = cart.items.count() if cart else 0
    return JsonResponse({'cart_count': count})



def shop(request):
    return render(request, 'shop.html',{'current_page':'shop'})

def terms(request):
    return render(request, 'terms.html')

def detail(request):
    return render(request, 'detail.html',{'current_page':'detail'})

def checkout(request):
    return render(request, 'checkout.html',{'current_page':'checkout'})

def user(request):
    return render(request, 'user.html',{'current_page':'user'})

def register(request): # request.POST,
    if request.method == 'POST':
        form = RegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()  # Password is automatically hashed here
            messages.success(request, 'Customer created successfully! You can now log in.',extra_tags='customer_register_success')
            # messages.success(request, 'Account created successfully! You can now log in.')
            return redirect('login')  # Replace with your login URL name
        else:
            messages.error(request, 'An error has occurred.')
    else:
        form = RegistrationForm()

    return render(request, 'register.html', {'form': form, 'current_page': 'register'})


# this handles the user logins
def login_user(request):
    error_message = None  # Initialize a variable for error messages

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            # Handle the 'next' parameter
            next_url = request.GET.get('next')
            if next_url:  # If 'next' is present, redirect there
                return redirect(next_url)

            # Redirect based on user role if no 'next' parameter
            return redirect('products' if user.is_staff else 'index')
        else:
            error_message = 'Invalid username or password.'  # Set error message

    # Render the login page with the specific error message
    return render(request, 'login.html', {'error_message': error_message})



def products(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            # Save the product
            product = form.save(commit=False)
            selected_choice = form.cleaned_data['category_or_subcategory']

            # Determine if it's a category or subcategory
            if selected_choice.startswith('sub_'):
                subcategory_id = int(selected_choice.split('_')[1])
                product.subcategory = Subcategory.objects.get(id=subcategory_id)
                product.category = product.subcategory.category  # Infer the category from subcategory
            elif selected_choice.startswith('cat_'):
                category_id = int(selected_choice.split('_')[1])
                product.category = Category.objects.get(id=category_id)
                product.subcategory = None  # No subcategory

            product.save()
            messages.success(request, 'Product added successfully!')
            return redirect('products')  # Replace with the URL name of your choice
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProductForm()

    return render(request, 'products.html', {'form': form})




# Admin Registration field
def admin_register(request):
    if request.method == 'POST':
        form = AdminRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()  # Password is automatically hashed here
            messages.success(request, 'Account created successfully! You can now log in.')
            return redirect('admin_register')  # Replace with your login URL name
        else:
            messages.error(request, 'An error has occurred.')
    else:
        form = AdminRegistrationForm()

    return render(request, 'admin_register.html', {'form': form, 'current_page': 'admin_register'})


def admin_customer(request):
    if request.method == 'POST':
        form = AdminCustomerRegistrationForm(request.POST)
        if form.is_valid():
            form.save()  # Password is automatically hashed here
            messages.success(request, 'Account created successfully! You can now log in.')
            return redirect('admin_customer')  # Replace with your login URL name
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AdminCustomerRegistrationForm()

    return render(request, 'admin_customer.html', {'form': form, 'current_page': 'admin_customer'})


def admin_data(request):
    # Filter profiles where the related user is a staff or superuser
    data = Profile.objects.filter(user__is_staff=True)  # or user__is_superuser=True if needed
    context = {'data': data}
    return render(request, 'admin_data.html', context)


def customer_data(request):
    # Filter profiles where the related user is a staff or superuser
    data = Profile.objects.filter(user__is_staff=False)  # or user__is_superuser=True if needed
    context = {'data': data}
    return render(request, 'customer_data.html', context)

# Categories
def category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category_name = form.cleaned_data['category_name']
            contains_subcategories = form.cleaned_data['contains_subcategories']
            subcategories = request.POST.getlist('subcategories[]')  # Dynamically added subcategories

            # Save the category
            category, created = Category.objects.get_or_create(
                name=category_name,
                defaults={'contains_subcategories': contains_subcategories}
            )
            if not created:
                messages.error(request, "Category already exists.")
                return redirect('category')

            # Save subcategories if applicable
            if contains_subcategories:
                # Ensure there are subcategories entered
                if not subcategories:
                    messages.error(request, "You must provide subcategory(s).")
                    return redirect('category')

                for subcategory_name in subcategories:
                    if subcategory_name.strip():  # Ensure no empty subcategory names
                        Subcategory.objects.create(name=subcategory_name.strip(), category=category)

            messages.success(request, "Categories saved successfully.")
            return redirect('category')
    else:
        form = CategoryForm()

    return render(request, 'category.html', {'form': form})


# View to list all categories
def category_data(request):
    categories = Category.objects.all()  # Fetch all categories
    return render(request, 'category_data.html', {'categories': categories})


# Update category
def update_category(request, id):
    category = get_object_or_404(Category, id=id)

    # Retrieve existing subcategories
    subcategories = category.subcategories.all()  # assuming Category has a related field to Subcategory

    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category_name = form.cleaned_data['category_name']
            contains_subcategories = form.cleaned_data['contains_subcategories']

            # Update category name and the subcategory flag
            category.name = category_name
            category.contains_subcategories = contains_subcategories
            category.save()

            # Handle subcategories only if the category contains them
            subcategory_names = request.POST.getlist('subcategories[]')

            # Remove subcategories that were not included in the form submission
            current_subcategories = category.subcategories.all()
            for subcategory in current_subcategories:
                if subcategory.name not in subcategory_names:
                    subcategory.delete()

            if contains_subcategories:
                # Add or update subcategories
                for subcategory_name in subcategory_names:
                    subcategory, created = Subcategory.objects.get_or_create(name=subcategory_name, category=category)

            else:
                # If there are no subcategories, clear all associated subcategories
                category.subcategories.set([])

            messages.success(request, 'Category updated successfully!')
            return redirect('category_data')  # Redirect to category list or wherever you want after update
        else:
            messages.error(request, 'There were errors in the form. Please check.')
    else:
        form = CategoryForm(initial={'category_name': category.name, 'contains_subcategories': category.contains_subcategories})

    return render(request, 'update_category.html', {'form': form, 'category': category, 'subcategories': subcategories})




# View to handle category deletion
def delete(request, id):
    category = get_object_or_404(Category, id=id)
    try:
        category.delete()
        messages.success(request, 'Category deleted successfully.')
    except Exception as e:
        messages.error(request, 'Category not deleted.')
    return redirect('category_data')



# View to list all products
def product_data(request):
    # Fetch all products from the database
    products = Product.objects.all()
    return render(request, 'product_data.html', {'product_data': products})

# Update Products
def update_product(request, pk):
    product = get_object_or_404(Product, pk=pk)  # Fetch the product to update
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            # Temporarily save the product to handle category and subcategory
            product = form.save(commit=False)

            # Process the category_or_subcategory field
            category_or_subcategory = form.cleaned_data['category_or_subcategory']

            if category_or_subcategory.startswith('sub_'):
                subcategory_id = int(category_or_subcategory.split('_')[1])
                product.subcategory = Subcategory.objects.get(id=subcategory_id)
                product.category = product.subcategory.category  # Infer the main category
            elif category_or_subcategory.startswith('cat_'):
                category_id = int(category_or_subcategory.split('_')[1])
                product.category = Category.objects.get(id=category_id)
                product.subcategory = None  # Clear subcategory if only category is selected

            # Save the product
            product.save()
            messages.success(request, 'Product updated successfully!')
            return redirect('product_data')  # Redirect to the product list view
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        # Pre-fill the form
        form = ProductForm(instance=product)

    return render(request, 'update_product.html', {'form': form, 'product': product})


def delete_product(request, pk):
    # Fetch and delete the product instance
    product = get_object_or_404(Product, pk=pk)
    try:
        product.delete()
        messages.success(request, 'Product deleted successfully!')
    except Exception as e:
        messages.error(request, 'Error deleting product: {}'.format(e))
    return redirect('product_data')

# This is the shop view template
# That carries all the products
def shop_view(request, category_id=None, subcategory_id=None):
    categories = Category.objects.all()  # Fetch all categories for the dropdown
    products = Product.objects.none()  # Default to no products
    selected_category = None
    selected_subcategory = None
    no_products_message = None

    if category_id:
        # Fetch the selected category
        selected_category = get_object_or_404(Category, id=category_id) #If the product has category_id fetch it

        if selected_category.contains_subcategories:
            # Category has subcategories, fetch products from subcategories
            subcategories = Subcategory.objects.filter(category=selected_category)
            products = Product.objects.filter(subcategory__in=subcategories)
        else:
            # Category has no subcategories, fetch products directly assigned to this category
            products = Product.objects.filter(category=selected_category)

        if not products.exists():
            no_products_message = f"No products available in the category '{selected_category.name}'."

    elif subcategory_id:
        # Fetch the selected subcategory
        selected_subcategory = get_object_or_404(Subcategory, id=subcategory_id)
        selected_category = selected_subcategory.category  # Get the parent category
        products = Product.objects.filter(subcategory=selected_subcategory)

        if not products.exists():
            no_products_message = f"No products available in the subcategory '{selected_subcategory.name}'."

    # Implement pagination
    paginator = Paginator(products, 8)  # Show 8 products per page
    page_number = request.GET.get('page')  # Get the page number from the query string
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)  # Show the first page if page number is not an integer
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)  # Show the last page if page is out of range

    return render(request, 'shop.html', {
        'categories': categories,
        'page_obj': page_obj,  # Paginated products
        'selected_category': selected_category,
        'selected_subcategory': selected_subcategory,
        'no_products_message': no_products_message,
    })

def promocode(request):
    return render(request, 'promocode.html',{'current_page':'promocode'})


def promotype(request):
    return render(request, 'promotype.html',{'current_page':'promotype'})




