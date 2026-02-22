from django.views.generic import ListView, DetailView
from ..models import Product
from ..selectors.product_selectors import get_catalog_products, get_catalog_categories

class ProductListView(ListView):
    model = Product
    template_name = 'shop/product_list.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        return get_catalog_products(
            category=self.request.GET.get('category', ''),
            sort=self.request.GET.get('sort', ''),
        )


    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['categories'] = get_catalog_categories()
        ctx['current_category'] = self.request.GET.get('category', '')
        ctx['current_sort'] = self.request.GET.get('sort', '')
        return ctx

class ProductDetailView(DetailView):
    model = Product
    template_name = 'shop/product_detail.html'
    context_object_name = 'product'