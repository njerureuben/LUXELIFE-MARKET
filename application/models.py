from django.db import models
from django.contrib.auth.models import User

from django.core.exceptions import ValidationError
import re

from django.db.models.signals import post_save
from django.dispatch import receiver


# This model create user profiles(For the normal Customers)
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    fullname = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    country = models.CharField(max_length=255, blank=True, null=True)
    image = models.ImageField(upload_to='profile_images/', default='profile_images/default.jpg', blank=True)

    def __str__(self):
        return self.user.username

    def save(self, *args, **kwargs):
        # Validate username
        if not re.match(r'^[a-zA-Z0-9]+$', self.user.username):
            raise ValidationError('Username must contain only letters and numbers without spaces.')
        super().save(*args, **kwargs)



# This is the model used to add products to the Database
class Product(models.Model):
    item_name = models.CharField(max_length=255)
    item_description = models.CharField(max_length=255)
    old_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    new_price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='product_images/')
    category = models.ForeignKey('Category', on_delete=models.CASCADE, related_name='products')  # Link to Category
    subcategory = models.ForeignKey('Subcategory', on_delete=models.SET_NULL, null=True, blank=True, related_name='products')  # Optional Subcategory
    color = models.CharField(max_length=50, null=True, blank=True)
    size = models.CharField(max_length=50, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.item_name




# This is the model used to create the categories and the sub categories
class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)
    contains_subcategories = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class Subcategory(models.Model):
    name = models.CharField(max_length=255)
    category = models.ForeignKey(Category, related_name='subcategories', on_delete=models.CASCADE)

    def __str__(self):
        return self.name

# The cart model
class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="cart")
    created_at = models.DateTimeField(auto_now_add=True)

    def total_price(self):
        return sum(item.total_price() for item in self.items.all())

    def __str__(self):
        return f"Cart({self.user.username})"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def total_price(self):
        return self.product.new_price * self.quantity

    def __str__(self):
        return f"{self.product.item_name} (x{self.quantity})"


@receiver(post_save, sender=User)
def create_cart(sender, instance, created, **kwargs):
    if created:
        Cart.objects.create(user=instance)



# Creating Promo code
class PromoCodeType(models.Model):
    name = models.CharField(max_length=255, unique=True)  # Unique name for each promo type
    description = models.TextField(blank=True, null=True)  # Optional description for the promo type

    def __str__(self):
        return self.name