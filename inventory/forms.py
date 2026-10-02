from django import forms

from .models import Category, Product, Supplier


class BootstrapFormMixin:

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = 'form-select'
            else:
                field.widget.attrs['class'] = 'form-control'


class ProductForm(BootstrapFormMixin, forms.ModelForm):

    class Meta:
        model = Product
        fields = ['name', 'sku', 'description', 'category', 'supplier', 'price', 'min_stock']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class CategoryForm(BootstrapFormMixin, forms.ModelForm):

    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class SupplierForm(BootstrapFormMixin, forms.ModelForm):

    class Meta:
        model = Supplier
        fields = ['name', 'contact_name', 'email', 'phone', 'address']