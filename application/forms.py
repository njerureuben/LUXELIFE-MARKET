from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile, Product, Category, Subcategory, PromoCodeType
from django.contrib.auth.forms import PasswordChangeForm


# This is the registration for a normal Customer
class RegistrationForm(UserCreationForm):
    fullname = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your full name'
        })
    )
    username = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your username'
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address'
        })
    )
    phone = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your phone number'
        })
    )
    address = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your address'
        })
    )
    country = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your country'
        })
    )
    image = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control'
        })
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password'
        })
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm your password'
        })
    )

    class Meta:
        model = User
        fields = ['fullname', 'username', 'email', 'password1', 'password2', 'phone', 'address', 'country', 'image']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            # Create and save the profile instance
            Profile.objects.create(
                user=user,
                fullname=self.cleaned_data['fullname'],
                phone=self.cleaned_data['phone'],
                address=self.cleaned_data['address'],
                country=self.cleaned_data['country'],
                image=self.cleaned_data.get('image')  # Save the uploaded image
            )
        return user

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['fullname', 'phone', 'address', 'country', 'image']
        widgets = {
            'fullname': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Full Name'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Phone'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Address'}),
            'country': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Country'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }

class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

# this is the product form
class ProductForm(forms.ModelForm):
    item_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter Product Name'
        })
    )
    old_price = forms.DecimalField(
        required=False,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Old Price'
        })
    )
    new_price = forms.DecimalField(
        required=True,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'New Price'
        })
    )
    category_or_subcategory = forms.ChoiceField(
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    color = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter Color (e.g., Red, Blue)'
        })
    )
    size = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter Size (e.g., S, M, L)'
        })
    )
    quantity = forms.IntegerField(
        required=True,
        min_value=0,  # Ensure quantity is non-negative
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter Quantity'
        })
    )

    class Meta:
        model = Product
        fields = ['item_name', 'item_description', 'old_price', 'new_price', 'image', 'color', 'size', 'quantity']

        widgets = {
            'item_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Enter Product Description'
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        category_choices = []

        # Build the category or subcategory choices
        for category in Category.objects.all():
            subcategories = category.subcategories.all()
            if subcategories.exists():
                # Add subcategories if they exist
                category_choices.extend([(f'sub_{sub.id}', f'{sub.name} | {category.name}') for sub in subcategories])
            else:
                # Add the main category if no subcategories exist
                category_choices.append((f'cat_{category.id}', category.name))

        self.fields['category_or_subcategory'].choices = category_choices

        # Pre-select the current category or subcategory
        if self.instance.pk:  # Check if the form is bound to an existing product
            if self.instance.subcategory:
                # Set the initial value to the subcategory
                self.fields['category_or_subcategory'].initial = f'sub_{self.instance.subcategory.id}'
            elif self.instance.category:
                # Set the initial value to the category
                self.fields['category_or_subcategory'].initial = f'cat_{self.instance.category.id}'




# This is the registration for Admins
class AdminRegistrationForm(UserCreationForm):
    fullname = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your full name'
        })
    )
    username = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your username'
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address'
        })
    )
    phone = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your phone number'
        })
    )
    address = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your address'
        })
    )
    country = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your country'
        })
    )
    image = forms.ImageField(
        required=False,  # Make it optional
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control'
        })
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password'
        })
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm your password'
        })
    )

    class Meta:
        model = User
        fields = ['fullname', 'username', 'email', 'password1', 'password2', 'phone', 'address', 'country', 'image']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.is_staff = True
        user.is_superuser = True
        if commit:
            user.save()
            # Create and save the profile instance
            Profile.objects.create(
                user=user,
                fullname=self.cleaned_data['fullname'],
                phone=self.cleaned_data['phone'],
                address=self.cleaned_data['address'],
                country=self.cleaned_data['country'],
                image=self.cleaned_data.get('image')  # Save the uploaded image
            )
        return user



class AdminCustomerRegistrationForm(UserCreationForm):
    fullname = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your full name'
        })
    )

    username = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your username'
        })
    )

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address'
        })
    )
    phone = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your phone number'
        })
    )
    address = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your address'
            # 'rows': 3
        })
    )
    country = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your country'
        })
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password'
        })
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm your password'
        })
    )

    class Meta:
        model = User
        fields = ['fullname', 'username', 'email', 'password1', 'password2', 'phone', 'address', 'country']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            # Create and save the profile instance
            Profile.objects.create(
                user=user,
                fullname=self.cleaned_data['fullname'],
                phone=self.cleaned_data['phone'],
                address=self.cleaned_data['address'],
                country=self.cleaned_data['country']
            )
        return user

# Category form
class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category  # Specify the model this form is for
        fields = ['category_name', 'contains_subcategories']  # Add the fields to be used in the form

    # Customizing widgets if needed
    category_name = forms.CharField(
        label="Category Name",
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter category name',
            'required': 'required',
        })
    )

    contains_subcategories = forms.BooleanField(
        label="Contains Sub Categories?",
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'id': 'containsSubCategory',
        })
    )

class PromoCodeTypeForm(forms.ModelForm):
    class Meta:
        model = PromoCodeType
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Promo Code Type'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Enter Description'}),
        }

class PaymentForm(forms.Form):
    phone_number = forms.CharField(
        label='Phone Number',
        max_length=15,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Enter Phone Number',
                'pattern': r'\d+',  # Only numeric values
                'title': 'Please enter a valid phone number',
            }
        )
    )
    amount = forms.IntegerField(
        label='Amount',
        min_value=1,
        max_value=250000,
        widget=forms.NumberInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Enter Amount',
            }
        )
    )