from django.urls import path

from . import views

app_name = 'inventory'

urlpatterns = [
    # Productos
    path('', views.ProductListView.as_view(), name='product_list'),
    path('productos/nuevo/', views.ProductCreateView.as_view(), name='product_create'),
    path('productos/importar/', views.ProductImportView.as_view(), name='product_import'),
    path('productos/plantilla-csv/', views.download_csv_template, name='product_csv_template'),
    path('productos/<int:pk>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('productos/<int:pk>/editar/', views.ProductUpdateView.as_view(), name='product_update'),

    # Categorías
    path('categorias/', views.CategoryListView.as_view(), name='category_list'),
    path('categorias/nueva/', views.CategoryCreateView.as_view(), name='category_create'),
    path('categorias/<int:pk>/editar/', views.CategoryUpdateView.as_view(), name='category_update'),
    path('categorias/<int:pk>/eliminar/', views.CategoryDeleteView.as_view(), name='category_delete'),

    # Proveedores
    path('proveedores/', views.SupplierListView.as_view(), name='supplier_list'),
    path('proveedores/nuevo/', views.SupplierCreateView.as_view(), name='supplier_create'),
    path('proveedores/<int:pk>/editar/', views.SupplierUpdateView.as_view(), name='supplier_update'),
    path('proveedores/<int:pk>/eliminar/', views.SupplierDeleteView.as_view(), name='supplier_delete'),
    
    # Movimientos de stock
    path('movimientos/', views.StockMovementListView.as_view(), name='movement_list'),
    path('movimientos/nuevo/', views.StockMovementCreateView.as_view(), name='movement_create'),
    
    
    # Alertas
    path('alertas/', views.LowStockListView.as_view(), name='low_stock'),
    
    
    # Panel
    path('panel/', views.DashboardView.as_view(), name='dashboard'),
]