from .models import Product


def low_stock_alerts(request):
    if not request.user.is_authenticated:
        return {}
    return {'low_stock_count': Product.objects.low_stock().count()}