from .models import Category
from .models import Cart

def categories_context(request):
    categories = Category.objects.prefetch_related('subcategories').all()
    return {'categories': categories}


def cart_count(request):
    """
    Context processor to return the cart count for the logged-in user.
    """
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
        count = cart.items.count() if cart else 0
    else:
        count = 0
    return {'cart_count': count}
