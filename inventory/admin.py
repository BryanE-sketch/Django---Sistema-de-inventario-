from django.contrib import admin
from django.db.models import Count

from .models import Category, Product, StockMovement, Supplier

admin.site.site_header = 'Sistema de Inventario'
admin.site.site_title = 'Inventario'
admin.site.index_title = 'Panel de administración'


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'product_count')
    search_fields = ('name',)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(num_products=Count('products'))

    @admin.display(description='nº de productos', ordering='num_products')
    def product_count(self, obj):
        return obj.num_products


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_name', 'email', 'phone', 'product_count')
    search_fields = ('name', 'contact_name', 'email')

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(num_products=Count('products'))

    @admin.display(description='nº de productos', ordering='num_products')
    def product_count(self, obj):
        return obj.num_products


class StockMovementInline(admin.TabularInline):
    model = StockMovement
    extra = 0
    fields = ('created_at', 'movement_type', 'quantity', 'note', 'created_by')
    readonly_fields = fields
    can_delete = False
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'sku',
        'category',
        'supplier',
        'price',
        'stock',
        'min_stock',
        'low_stock',
    )
    list_filter = ('category', 'supplier')
    search_fields = ('name', 'sku')
    list_select_related = ('category', 'supplier')
    readonly_fields = ('stock', 'created_at', 'updated_at')
    inlines = [StockMovementInline]
    fieldsets = (
        (None, {'fields': ('name', 'sku', 'description')}),
        ('Clasificación', {'fields': ('category', 'supplier')}),
        ('Precio y stock', {'fields': ('price', 'stock', 'min_stock')}),
        ('Fechas', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

    @admin.display(boolean=True, description='¿stock bajo?')
    def low_stock(self, obj):
        return obj.is_low_stock


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'product', 'movement_type', 'quantity', 'created_by')
    list_filter = ('movement_type', 'product__category', 'product__supplier')
    search_fields = ('product__name', 'product__sku', 'note')
    date_hierarchy = 'created_at'
    autocomplete_fields = ('product',)
    fields = ('product', 'movement_type', 'quantity', 'note')

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.fields
        return ()

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def has_delete_permission(self, request, obj=None):
        return False