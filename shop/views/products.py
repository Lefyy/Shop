from django.views.generic import ListView, DetailView
from django.db.models import Count
from ..models import Product, Category

class ProductListView(ListView):
    model = Product
    template_name = 'shop/product_list.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        qs = Product.objects.select_related('category')

        if cat := self.request.GET.get('category'):
            qs = qs.filter(category_id=cat)

        sort = self.request.GET.get('sort')

        if sort == 'price_asc':
            qs = qs.order_by('price')
        elif sort == 'price_desc':
            qs = qs.order_by('-price')
        elif sort == 'popularity':
            qs = qs.annotate(order_count=Count('orderitem')).order_by('-order_count')

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['categories'] = Category.objects.all()
        ctx['current_category'] = self.request.GET.get('category', '')
        ctx['current_sort'] = self.request.GET.get('sort', '')
        return ctx

class ProductDetailView(DetailView):
    model = Product
    template_name = 'shop/product_detail.html'
    context_object_name = 'product'