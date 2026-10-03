from django.conf import settings
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.urls import reverse


class Category(models.Model):
    name = models.CharField('nombre', max_length=100, unique=True)
    description = models.TextField('descripción', blank=True)

    class Meta:
        verbose_name = 'categoría'
        verbose_name_plural = 'categorías'
        ordering = ['name']

    def __str__(self):
        return self.name


class Supplier(models.Model):
    name = models.CharField('nombre', max_length=150, unique=True)
    contact_name = models.CharField('persona de contacto', max_length=100, blank=True)
    email = models.EmailField('correo electrónico', blank=True)
    phone = models.CharField('teléfono', max_length=20, blank=True)
    address = models.CharField('dirección', max_length=255, blank=True)
    created_at = models.DateTimeField('fecha de alta', auto_now_add=True)

    class Meta:
        verbose_name = 'proveedor'
        verbose_name_plural = 'proveedores'
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField('nombre', max_length=150)
    sku = models.CharField(
        'SKU',
        max_length=50,
        unique=True,
        help_text='Código único que identifica el producto',
    )
    description = models.TextField('descripción', blank=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='products',
        verbose_name='categoría',
    )
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,
        related_name='products',
        verbose_name='proveedor',
    )
    price = models.DecimalField(
        'precio',
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    stock = models.PositiveIntegerField('stock actual', default=0, editable=False)
    min_stock = models.PositiveIntegerField('stock mínimo', default=5)
    created_at = models.DateTimeField('creado', auto_now_add=True)
    updated_at = models.DateTimeField('actualizado', auto_now=True)

    class Meta:
        verbose_name = 'producto'
        verbose_name_plural = 'productos'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.sku})'
    
    def get_absolute_url(self):
        return reverse('inventory:product_detail', args=[self.pk])

    @property
    def is_low_stock(self):
        return self.stock <= self.min_stock


class StockMovement(models.Model):

    class MovementType(models.TextChoices):
        IN = 'IN', 'Entrada'
        OUT = 'OUT', 'Salida'

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='movements',
        verbose_name='producto',
    )
    movement_type = models.CharField(
        'tipo de movimiento',
        max_length=3,
        choices=MovementType.choices,
    )
    quantity = models.PositiveIntegerField(
        'cantidad',
        validators=[MinValueValidator(1)],
    )
    note = models.CharField('nota', max_length=255, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stock_movements',
        verbose_name='registrado por',
    )
    created_at = models.DateTimeField('fecha', auto_now_add=True)

    class Meta:
        verbose_name = 'movimiento de stock'
        verbose_name_plural = 'movimientos de stock'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_movement_type_display()} de {self.quantity} - {self.product.name}'
    
    def clean(self):
        if self.movement_type == self.MovementType.OUT and self.product_id and self.quantity:
            if self.quantity > self.product.stock:
                raise ValidationError({
                    'quantity': f'Stock insuficiente. Disponible: {self.product.stock} unidades.'
                })

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValueError('Los movimientos de stock no se pueden modificar.')

        with transaction.atomic():
            product = Product.objects.select_for_update().get(pk=self.product_id)

            if self.movement_type == self.MovementType.OUT:
                if self.quantity > product.stock:
                    raise ValidationError(
                        f'Stock insuficiente. Disponible: {product.stock} unidades.'
                    )
                product.stock -= self.quantity
            else:
                product.stock += self.quantity

            product.save(update_fields=['stock', 'updated_at'])
            super().save(*args, **kwargs)
            self.product = product