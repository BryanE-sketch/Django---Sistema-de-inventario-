from django.urls import path

from . import views

app_name = 'inventory'

urlpatterns = [
    path('', views.ProductListView.as_view(), name='product_list'),
    path('productos/nuevo/', views.ProductCreateView.as_view(), name='product_create'),
    path('productos/<int:pk>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('productos/<int:pk>/editar/', views.ProductUpdateView.as_view(), name='product_update'),
]