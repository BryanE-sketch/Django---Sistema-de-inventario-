from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Count, ProtectedError
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import CategoryForm, ProductForm, SupplierForm
from .models import Category, Product, Supplier


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