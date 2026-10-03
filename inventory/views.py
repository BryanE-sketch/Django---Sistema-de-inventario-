import csv
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Count, DecimalField, F, ProtectedError, Q, Sum
from django.db.models.functions import TruncDate
from django.http import HttpResponse
from django.shortcuts import redirect
from django.template.defaultfilters import pluralize
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    FormView,
    ListView,
    TemplateView,
    UpdateView,
)

from .forms import (
    CategoryForm,
    CSVImportForm,
    ProductFilterForm,
    ProductForm,
    StockMovementForm,
    SupplierForm,
)
from .models import Category, Product, StockMovement, Supplier
from .services import CSVImportError, import_products_from_csv

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
        queryset = Product.objects.select_related('category', 'supplier')
        self.filter_form = ProductFilterForm(self.request.GET or None)

        if self.filter_form.is_valid():
            data = self.filter_form.cleaned_data
            if data['q']:
                queryset = queryset.filter(
                    Q(name__icontains=data['q']) | Q(sku__icontains=data['q'])
                )
            if data['category']:
                queryset = queryset.filter(category=data['category'])
            if data['supplier']:
                queryset = queryset.filter(supplier=data['supplier'])
            if data['low_stock']:
                queryset = queryset.low_stock()

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = self.filter_form
        context['is_filtered'] = any(
            value for key, value in self.request.GET.items() if key != 'page'
        )
        return context


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




class ProductImportView(LoginRequiredMixin, FormView):
    form_class = CSVImportForm
    template_name = 'inventory/product_import.html'
    success_url = reverse_lazy('inventory:product_list')
    max_errors_shown = 20

    def form_valid(self, form):
        try:
            summary = import_products_from_csv(form.cleaned_data['file'], self.request.user)
        except CSVImportError as error:
            for message in error.errors[:self.max_errors_shown]:
                form.add_error(None, message)
            hidden = len(error.errors) - self.max_errors_shown
            if hidden > 0:
                form.add_error(None, f'... y {hidden} errores más.')
            return self.form_invalid(form)

            created = summary['created']
            updated = summary['updated']
            movements = summary['movements']
            messages.success(
        self.request,
            f'Importación completada: {created} producto{pluralize(created)} creado{pluralize(created)}, '
            f'{updated} actualizado{pluralize(updated)} y '
            f'{movements} entrada{pluralize(movements)} de stock registrada{pluralize(movements)}.',
        )
        return super().form_valid(form)


@login_required
def download_csv_template(request):
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="plantilla_productos.csv"'
    response.write('\ufeff')
    writer = csv.writer(response)
    writer.writerow(['nombre', 'sku', 'categoria', 'proveedor', 'precio', 'stock_minimo', 'entrada'])
    writer.writerow(['Bolígrafo azul', 'BOL-001', 'Papeleria', 'Bryan', '1.50', '10', '50'])
    return response



class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'inventory/dashboard.html'
    days = 30

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['totals'] = Product.objects.aggregate(
            total_products=Count('id'),
            total_units=Sum('stock'),
            inventory_value=Sum(
                F('stock') * F('price'),
                output_field=DecimalField(max_digits=14, decimal_places=2),
            ),
        )

        today = timezone.localdate()
        start = today - timedelta(days=self.days - 1)
        recent = StockMovement.objects.filter(created_at__date__gte=start)

        daily_rows = (
            recent.annotate(day=TruncDate('created_at'))
            .values('day', 'movement_type')
            .annotate(total=Sum('quantity'))
            .order_by()
        )
        all_days = [start + timedelta(days=offset) for offset in range(self.days)]
        entries = dict.fromkeys(all_days, 0)
        exits = dict.fromkeys(all_days, 0)
        for row in daily_rows:
            if row['movement_type'] == StockMovement.MovementType.IN:
                entries[row['day']] = row['total']
            else:
                exits[row['day']] = row['total']

        top_exits = (
            recent.filter(movement_type=StockMovement.MovementType.OUT)
            .values('product__name')
            .annotate(total=Sum('quantity'))
            .order_by('-total')[:5]
        )

        context['days'] = self.days
        context['chart_data'] = {
            'labels': [day.strftime('%d/%m') for day in all_days],
            'entries': [entries[day] for day in all_days],
            'exits': [exits[day] for day in all_days],
            'top_labels': [row['product__name'] for row in top_exits],
            'top_values': [row['total'] for row in top_exits],
        }
        return context