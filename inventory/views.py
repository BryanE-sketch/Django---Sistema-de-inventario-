from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Count, F, ProtectedError
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import CategoryForm, ProductForm, StockMovementForm, SupplierForm
from .models import Category, Product, StockMovement, Supplier

class ProtectedDeleteMixin:
    protected_message = 'No se puede eliminar porque tiene productos asociados.'

    def form_valid(self, form):
        name = str(self.object)
        try:
            response = super().form_valid(form)
        except ProtectedError:
            messages.error(self.request, self.protected_message)
            return redirect(self.success_url)
        messages.success(self.request, f'"{name}" eliminado correctamente.')
        return response




class ProductListView(LoginRequiredMixin, ListView):
    model = Product
    template_name = 'inventory/product_list.html'
    context_object_name = 'products'
    paginate_by = 10

    def get_queryset(self):
        return Product.objects.select_related('category', 'supplier')


class ProductDetailView(LoginRequiredMixin, DetailView):
    model = Product
    template_name = 'inventory/product_detail.html'
    context_object_name = 'product'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['movements'] = self.object.movements.select_related('created_by')[:20]
        return context


class ProductCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'inventory/product_form.html'
    success_message = 'Producto "%(name)s" creado correctamente.'


class ProductUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'inventory/product_form.html'
    success_message = 'Producto "%(name)s" actualizado correctamente.'




class CategoryListView(LoginRequiredMixin, ListView):
    model = Category
    template_name = 'inventory/category_list.html'
    context_object_name = 'categories'

    def get_queryset(self):
        return Category.objects.annotate(num_products=Count('products'))


class CategoryCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = 'inventory/form.html'
    success_url = reverse_lazy('inventory:category_list')
    success_message = 'Categoría "%(name)s" creada correctamente.'
    extra_context = {
        'title': 'Nueva categoría',
        'cancel_url': reverse_lazy('inventory:category_list'),
    }


class CategoryUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = 'inventory/form.html'
    success_url = reverse_lazy('inventory:category_list')
    success_message = 'Categoría "%(name)s" actualizada correctamente.'
    extra_context = {
        'title': 'Editar categoría',
        'cancel_url': reverse_lazy('inventory:category_list'),
    }


class CategoryDeleteView(LoginRequiredMixin, ProtectedDeleteMixin, DeleteView):
    model = Category
    template_name = 'inventory/confirm_delete.html'
    success_url = reverse_lazy('inventory:category_list')
    protected_message = 'No se puede eliminar esta categoría porque tiene productos asociados.'
    extra_context = {
        'cancel_url': reverse_lazy('inventory:category_list'),
    }




class SupplierListView(LoginRequiredMixin, ListView):
    model = Supplier
    template_name = 'inventory/supplier_list.html'
    context_object_name = 'suppliers'

    def get_queryset(self):
        return Supplier.objects.annotate(num_products=Count('products'))


class SupplierCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Supplier
    form_class = SupplierForm
    template_name = 'inventory/form.html'
    success_url = reverse_lazy('inventory:supplier_list')
    success_message = 'Proveedor "%(name)s" creado correctamente.'
    extra_context = {
        'title': 'Nuevo proveedor',
        'cancel_url': reverse_lazy('inventory:supplier_list'),
    }


class SupplierUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Supplier
    form_class = SupplierForm
    template_name = 'inventory/form.html'
    success_url = reverse_lazy('inventory:supplier_list')
    success_message = 'Proveedor "%(name)s" actualizado correctamente.'
    extra_context = {
        'title': 'Editar proveedor',
        'cancel_url': reverse_lazy('inventory:supplier_list'),
    }


class SupplierDeleteView(LoginRequiredMixin, ProtectedDeleteMixin, DeleteView):
    model = Supplier
    template_name = 'inventory/confirm_delete.html'
    success_url = reverse_lazy('inventory:supplier_list')
    protected_message = 'No se puede eliminar este proveedor porque tiene productos asociados.'
    extra_context = {
        'cancel_url': reverse_lazy('inventory:supplier_list'),
    }




class StockMovementListView(LoginRequiredMixin, ListView):
    model = StockMovement
    template_name = 'inventory/movement_list.html'
    context_object_name = 'movements'
    paginate_by = 20

    def get_queryset(self):
        return StockMovement.objects.select_related('product', 'created_by')


class StockMovementCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = StockMovement
    form_class = StockMovementForm
    template_name = 'inventory/form.html'

    def get_initial(self):
        initial = super().get_initial()
        product_id = self.request.GET.get('product')
        movement_type = self.request.GET.get('type')
        if product_id and product_id.isdigit():
            initial['product'] = product_id
        if movement_type in StockMovement.MovementType.values:
            initial['movement_type'] = movement_type
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Registrar movimiento de stock'
        product_id = self.request.GET.get('product')
        if product_id and product_id.isdigit():
            context['cancel_url'] = reverse('inventory:product_detail', args=[product_id])
        else:
            context['cancel_url'] = reverse('inventory:movement_list')
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        product = self.object.product
        if product.is_low_stock:
            messages.warning(
                self.request,
                f'Atención: {product.name} está en o por debajo del stock mínimo '
                f'({product.stock} de {product.min_stock} unidades).',
            )
        return response

    def get_success_url(self):
        return self.object.product.get_absolute_url()

    def get_success_message(self, cleaned_data):
        movement = self.object
        return (
            f'{movement.get_movement_type_display()} de {movement.quantity} unidades registrada. '
            f'Stock actual de {movement.product.name}: {movement.product.stock}.'
        )


class LowStockListView(LoginRequiredMixin, ListView):
    template_name = 'inventory/low_stock_list.html'
    context_object_name = 'products'

    def get_queryset(self):
        return (
            Product.objects.low_stock()
            .select_related('category', 'supplier')
            .annotate(shortage=F('min_stock') - F('stock'))
            .order_by('-shortage', 'name')
        )