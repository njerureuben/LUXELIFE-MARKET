import base64
import json
from datetime import datetime
import os
import re
from random import sample

import requests
from django.db import transaction
from django.db.models import Count
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt

from .forms import RegistrationForm, ProductForm, AdminRegistrationForm, AdminCustomerRegistrationForm, CategoryForm, \
    PaymentForm
from django.contrib.auth import authenticate, login
from django.contrib import messages
from .models import Cart, CartItem, Order, OrderItem, Transaction
from .models import Category, Subcategory, Product
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from .models import Profile
from .forms import ProfileForm, CustomPasswordChangeForm
from dotenv import load_dotenv



# Load environment variables
load_dotenv()

# Retrieve variables from the environment
CONSUMER_KEY = os.getenv("CONSUMER_KEY")
CONSUMER_SECRET = os.getenv("CONSUMER_SECRET")
MPESA_PASSKEY = os.getenv("MPESA_PASSKEY")

MPESA_SHORTCODE = os.getenv("MPESA_SHORTCODE")
CALLBACK_URL = os.getenv("CALLBACK_URL")
MPESA_BASE_URL = os.getenv("MPESA_BASE_URL")

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

# def user(request):
#     return render(request, 'user.html',{'current_page':'user'})

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
    error_message: None = None  # Initialize a variable for error messages

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


@login_required
def user_profile_view(request):
    # Fetch the profile associated with the logged-in user
    profile = get_object_or_404(Profile, user=request.user)

    # Profile form for editing
    profile_form = ProfileForm(instance=profile)
    # Password change form
    password_form = CustomPasswordChangeForm(user=request.user)

    if request.method == 'POST':
        if 'fullname' in request.POST:  # Profile edit form submission
            profile_form = ProfileForm(request.POST, request.FILES, instance=profile)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, "Profile updated successfully!")
                return redirect('user_profile')
            else:
                messages.error(request, "Error updating profile.")
        elif 'new_password1' in request.POST:  # Password change form submission
            password_form = CustomPasswordChangeForm(data=request.POST, user=request.user)
            if password_form.is_valid():
                password_form.save()
                update_session_auth_hash(request, request.user)  # Keep the user logged in
                messages.success(request, "Password changed successfully!")
                return redirect('user_profile')
            else:
                messages.error(request, "Error changing password.")

    return render(request, 'user.html', {
        'profile': profile,  # Ensure profile is passed
        'profile_form': profile_form,
        'password_form': password_form,
    })




# Display the 6 products(Trandy products)
def random_products_view(request):
    """
    View to fetch up to 6 random products.
    """
    all_products = list(Product.objects.all())  # Convert QuerySet to a list
    random_products = sample(all_products, min(len(all_products), 6))  # Sample up to 6 products

    # Prepare data for the response
    data = [
        {
            "id": product.id,
            "item_name": product.item_name,
            "new_price": str(product.new_price),  # Convert Decimal to string for JSON serialization
            "old_price": str(product.old_price) if product.old_price else None,
            "image_url": product.image.url if product.image else None,
        }
        for product in random_products
    ]

    return JsonResponse({"random_products": data})




# Admin Profile
def adminprofile(request):
    return render(request, 'adminprofile.html')

# The check out element
@login_required
def checkout(request):
    cart = Cart.objects.filter(user=request.user).first()

    if request.method == "POST":
        # Collect billing and shipping details
        # (same as your previous code)

        if not cart or cart.items.count() == 0:
            messages.error(request, "Your cart is empty.")
            return redirect("cart")

        try:
            with transaction.atomic():
                # Create the Order
                order = Order.objects.create(
                    user=request.user,
                    total_price=cart.total_price(),
                    # Add other necessary fields for the order
                )

                # Create OrderItems
                for item in cart.items.all():
                    OrderItem.objects.create(
                        order=order,
                        product=item.product,
                        quantity=item.quantity,
                        price=item.product.new_price * item.quantity,
                    )

                # Clear cart after successful order
                cart.items.all().delete()

                # Redirect to payment view (STK Push)
                phone = format_phone_number(request.user.profile.phone_number)  # Assuming user has a phone_number field
                amount = cart.total_price()
                response = initiate_stk_push(phone, amount)

                if response.get("ResponseCode") == "0":
                    checkout_request_id = response["CheckoutRequestID"]
                    messages.success(request, "Order placed successfully! Please complete the payment.")
                    return redirect(f"/payment/?checkout_request_id={checkout_request_id}")  # Pass checkout_request_id for status tracking
                else:
                    error_message = response.get("errorMessage", "Failed to initiate STK Push. Please try again.")
                    messages.error(request, error_message)
                    return redirect("checkout")

        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect("checkout")

    return render(request, "checkout.html", {"cart": cart})


'''
Below is the MPESA Handling Section
'''
# Phone number formatting and validation
def format_phone_number(phone):
    phone = phone.replace("+", "")
    if re.match(r"^254\d{9}$", phone):
        return phone
    elif phone.startswith("0") and len(phone) == 10:
        return "254" + phone[1:]
    else:
        raise ValueError("Invalid phone number format")

# Generate M-Pesa access token
def generate_access_token():
    try:
        credentials = f"{CONSUMER_KEY}:{CONSUMER_SECRET}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()

        headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/json",
        }
        response = requests.get(
            f"{MPESA_BASE_URL}/oauth/v1/generate?grant_type=client_credentials",
            headers=headers,
        ).json()

        if "access_token" in response:
            return response["access_token"]
        else:
            raise Exception("Access token missing in response.")

    except requests.RequestException as e:
        raise Exception(f"Failed to connect to M-Pesa: {str(e)}")

# Initiate STK Push and handle response
def initiate_stk_push(phone, amount):
    try:
        token = generate_access_token()
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        stk_password = base64.b64encode(
            (MPESA_SHORTCODE + MPESA_PASSKEY + timestamp).encode()
        ).decode()

        request_body = {
            "BusinessShortCode": MPESA_SHORTCODE,
            "Password": stk_password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amount,
            "PartyA": phone,
            "PartyB": MPESA_SHORTCODE,
            "PhoneNumber": phone,
            "CallBackURL": CALLBACK_URL,
            "AccountReference": "account",
            "TransactionDesc": "Payment for goods",
        }

        response = requests.post(
            f"{MPESA_BASE_URL}/mpesa/stkpush/v1/processrequest",
            json=request_body,
            headers=headers,
        ).json()

        return response

    except Exception as e:
        print(f"Failed to initiate STK Push: {str(e)}")
        return e

# Payment View
def payment_view(request):
    if request.method == "POST":
        form = PaymentForm(request.POST)
        if form.is_valid():
            try:
                phone = format_phone_number(form.cleaned_data["phone_number"])
                amount = form.cleaned_data["amount"]
                response = initiate_stk_push(phone, amount)
                print(response)

                # If 0 means that the STK has been sent successfully
                if response.get("ResponseCode") == "0":
                    checkout_request_id = response["CheckoutRequestID"]
                    return render(request, "pending.html", {"checkout_request_id": checkout_request_id})
                # STK has not been sent
                else:
                    error_message = response.get("errorMessage", "Failed to send STK push. Please try again.")
                    return render(request, "payment_form.html", {"form": form, "error_message": error_message})

            except ValueError as e:
                return render(request, "payment_form.html", {"form": form, "error_message": str(e)})
            except Exception as e:
                return render(request, "payment_form.html", {"form": form, "error_message": f"An unexpected error occurred: {str(e)}"})

    else:
        form = PaymentForm()

    return render(request, "payment_form.html", {"form": form})

# Query STK Push status
def query_stk_push(checkout_request_id):
    print("Quering...")
    try:
        token = generate_access_token()
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password = base64.b64encode(
            (MPESA_SHORTCODE + MPESA_PASSKEY + timestamp).encode()
        ).decode()

        request_body = {
            "BusinessShortCode": MPESA_SHORTCODE,
            "Password": password,
            "Timestamp": timestamp,
            "CheckoutRequestID": checkout_request_id
        }

        response = requests.post(
            f"{MPESA_BASE_URL}/mpesa/stkpushquery/v1/query",
            json=request_body,
            headers=headers,
        )
        print(response.json())
        return response.json()

    except requests.RequestException as e:
        print(f"Error querying STK status: {str(e)}")
        return {"error": str(e)}

# View to query the STK status and return it to the frontend
def stk_status_view(request):
    if request.method == 'POST':
        try:
            # Parse the JSON body
            data = json.loads(request.body)
            checkout_request_id = data.get('checkout_request_id')
            print("CheckoutRequestID:", checkout_request_id)

            # Query the STK push status using your backend function
            status = query_stk_push(checkout_request_id)

            # Return the status as a JSON response
            return JsonResponse({"status": status})
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON body"}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=405)


from django.db import transaction


@csrf_exempt
def payment_callback(request):
    if request.method != "POST":
        return HttpResponseBadRequest("Only POST requests are allowed")

    try:
        callback_data = json.loads(request.body)  # Parse the request body
        result_code = callback_data["Body"]["stkCallback"]["ResultCode"]

        if result_code == 0:
            # Payment was successful
            # Extract order details from the POST data
            first_name = request.POST.get("first_name")
            last_name = request.POST.get("last_name")
            email = request.POST.get("email")
            phone_number = request.POST.get("phone_number")
            address_line1 = request.POST.get("address_line1")
            zip_code = request.POST.get("zip_code")

            # Retrieve the cart
            user = request.user
            cart = user.cart

            # Create an order
            order = Order.objects.create(
                user=user,
                total_amount=cart.total_price(),
                status="Completed",  # Or Pending if you want to mark as pending until payment confirmation
                payment_method="M-Pesa",  # Or another method if applicable
            )

            # Create order items based on cart items
            for item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    total_price=item.product.new_price * item.quantity
                )

                # Update the product stock after purchase
                product = item.product
                if product.quantity >= item.quantity:
                    product.quantity -= item.quantity
                    product.save()
                else:
                    raise ValueError(f"Insufficient stock for product {product.item_name}")

            # Clear the cart after successful order placement
            cart.items.all().delete()

            return JsonResponse({"ResultCode": 0, "ResultDesc": "Payment successful, order placed"})

        # Payment failed
        return JsonResponse({"ResultCode": result_code, "ResultDesc": "Payment failed"})

    except (json.JSONDecodeError, KeyError) as e:
        return HttpResponseBadRequest(f"Invalid request data: {str(e)}")
    except ValueError as e:
        return HttpResponseBadRequest(f"Error in payment callback: {str(e)}")







@csrf_exempt
def update_order_status(request):
    data = json.loads(request.body)
    checkout_request_id = data.get("checkout_request_id")
    status = data.get("status")

    # Update the order status
    try:
        order = Order.objects.get(checkout_request_id=checkout_request_id)
        order.status = status
        order.save()

        # If payment is successful, clear the cart
        if status == "paid":
            cart = Cart.objects.get(user=request.user)
            cart.items.clear()  # Clear cart after payment

        return JsonResponse({"message": "Order status updated successfully"})
    except Order.DoesNotExist:
        return JsonResponse({"message": "Order not found"}, status=404)
    except Exception as e:
        return JsonResponse({"message": str(e)}, status=500)



def create_order(request):
    if request.method == 'POST':
        # Get form data
        data = json.loads(request.body)
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        email = data.get('email')
        phone_number = data.get('phone_number')
        address_line1 = data.get('address_line1')
        zip_code = data.get('zip_code')

        # Assuming you have a Cart model to get the current cart
        cart = Cart.objects.get(user=request.user)

        # Create order
        order = Order.objects.create(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone_number=phone_number,
            address_line1=address_line1,
            zip_code=zip_code,
            cart=cart,
            total_price=cart.total_price,
        )

        # Update cart as "ordered"
        cart.status = "ordered"
        cart.save()

        # Return a JSON response with the checkout_request_id
        return JsonResponse({'success': True, 'checkout_request_id': order.id})

    return JsonResponse({'success': False}, status=400)