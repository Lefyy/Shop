from django.utils import timezone
from django.db.models import Sum, F, ExpressionWrapper, DecimalField

from ..models import OrderItem


def get_period_start(period: str):
    now = timezone.now()

    if period == 'day':
        return now.replace(hour=0, minute=0, second=0, microsecond=0)
    if period == 'month':
        return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if period == 'year':
        return now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

    return None


def get_statistics(period="all"):
    period_start = get_period_start(period)

    filters = {}
    if period_start:
        filters['order__created_date__gte'] = period_start

    line_total = ExpressionWrapper(
        F('quantity') * F('unit_price'),
        output_field=DecimalField(max_digits=18, decimal_places=2)
    )

    base_qs = OrderItem.objects.filter(**filters)

    top_products = list(
        base_qs.values('product__id', 'product__name')
        .annotate(total_qty=Sum('quantity'))
        .order_by('-total_qty')[:10]
    )

    top_products_revenue = list(
        base_qs.values('product__id', 'product__name')
        .annotate(total_revenue=Sum(line_total))
        .order_by('-total_revenue')[:10]
    )

    total_revenue = (
        base_qs.aggregate(total_revenue=Sum(line_total))
        .get('total_revenue') or 0
    )

    top_categories = list(
        base_qs.values('product__category__id', 'product__category__name')
        .annotate(total_qty=Sum('quantity'))
        .order_by('-total_qty')[:10]
    )

    top_customers = list(
        base_qs.values('order__customer__id', 'order__customer__user__username')
        .annotate(total_spent=Sum(line_total))
        .order_by('-total_spent')[:10]
    )

    return {
        "top_products": top_products,
        "top_products_revenue": top_products_revenue,
        "total_revenue": total_revenue,
        "top_categories": top_categories,
        "top_customers": top_customers,
    }
