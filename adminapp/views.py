from django.contrib.auth.models import User
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from application.forms import ProductForm, AdminRegistrationForm, CategoryForm,AdminUpdateForm, AdminCustomerRegistrationForm
from application.models import Profile, Category, Subcategory, Product

# Admin Dashboard
def admin_dashboard(request):
    return render(request, 'admin_dashboard.html')


#Admin Products Data
def productsdata(request):
    products = Product.objects.all()
    context = {'productsdata': products}
    return render(request, 'productsdata.html',context)


def categorydata(request):
    categories = Category.objects.all()
    context = {'categorydata': categories}
    return render(request, 'categorydata.html',context)

def adminproducts(request):
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
            return redirect('adminproducts')  # Replace with the URL name of your choice
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProductForm()

    return render(request, 'adminproducts.html', {'form': form})

def adminupdateproduct(request, pk):
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
            return redirect('productsdata')  # Redirect to product list view
        else:
            # Display an error message for validation errors
            messages.error(request, 'Please correct the errors below.')

    else:
        # Pre-fill the form
        form = ProductForm(instance=product)

    return render(request, 'adminupdateproduct.html', {'form': form, 'product': product})

def admindeleteproduct(request, pk):
        # Fetch and delete the product instance
        product = get_object_or_404(Product, pk=pk)
        try:
            product.delete()
            messages.success(request, 'Product deleted successfully!')
        except Exception as e:
            messages.error(request, 'Error deleting product: {}'.format(e))
        return redirect('productsdata')

def admincategory(request):
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
                return redirect('admincategory')

            # Save subcategories if applicable
            if contains_subcategories:
                # Ensure there are subcategories entered
                if not subcategories:
                    messages.error(request, "You must provide subcategory(s).")
                    return redirect('admincategory')

                for subcategory_name in subcategories:
                    if subcategory_name.strip():  # Ensure no empty subcategory names
                        Subcategory.objects.create(name=subcategory_name.strip(), category=category)

            messages.success(request, "Categories saved successfully.")
            return redirect('admincategory')
    else:
        form = CategoryForm()

    return render(request, 'admincategory.html', {'form': form})

def adminupdatecategory(request, id):
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
            return redirect('categorydata')  # Redirect to category list or wherever you want after update
        else:
            messages.error(request, 'There were errors in the form. Please check.')
    else:
        form = CategoryForm(initial={'category_name': category.name, 'contains_subcategories': category.contains_subcategories})

    return render(request, 'adminupdatecategory.html', {'form': form, 'category': category, 'subcategories': subcategories})

def createadmin(request):
    if request.method == 'POST':
        form = AdminRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()  # Password is automatically hashed here
            messages.success(request, 'Admin created successfully!')
            return redirect('createadmin')  # Replace with your login URL name
        else:
            messages.error(request, 'An error has occurred.')
    else:
        form = AdminRegistrationForm()

    return render(request, 'createadmin.html', {'form': form})

def admindata(request):
    # Filter profiles where the related user is a staff or superuser
    data = Profile.objects.filter(user__is_staff=True)  # or user__is_superuser=True if needed
    context = {'data': data}
    return render(request, 'admindata.html', context)

def deleteadmin(request, pk):
    admin = get_object_or_404(Profile, pk=pk)
    try:
        admin.delete()
        messages.success(request, 'Admin deleted successfully!')
    except Exception as e:
        messages.error(request, 'Error deleting product: {}'.format(e))
    return redirect('admindata')

def adminupdate(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = AdminUpdateForm(request.POST, request.FILES, instance=user.profile, user_instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Admin updated successfully.')
            return redirect('admindata')  # Replace with the appropriate URL
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AdminUpdateForm(instance=user.profile, user_instance=user)
    return render(request, 'adminupdate.html', {'form': form, 'user': user})

def createcustomer(request):
    if request.method == 'POST':
        form = AdminCustomerRegistrationForm(request.POST)
        if form.is_valid():
            form.save()  # Password is automatically hashed here
            messages.success(request, 'Account created successfully! You can now log in.')
            return redirect('createcustomer')  # Replace with your login URL name
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AdminCustomerRegistrationForm()

    return render(request, 'createcustomer.html', {'form': form, 'current_page': 'createcustomer'})

def customerdata(request):
    # Filter profiles where the related user is a staff or superuser
    data = Profile.objects.filter(user__is_staff=False)  # or user__is_superuser=True if needed
    context = {'data': data}
    return render(request, 'customerdata.html', context)

def adminsignin(request):
    return render(request, 'adminsignin.html')