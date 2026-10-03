import csv
import io
from decimal import Decimal, InvalidOperation

from django.db import transaction

from .models import Category, Product, StockMovement, Supplier

REQUIRED_COLUMNS = ['nombre', 'sku', 'categoria', 'proveedor', 'precio']
MAX_LENGTHS = {'nombre': 150, 'sku': 50, 'categoria': 100, 'proveedor': 150}


class CSVImportError(Exception):

    def __init__(self, errors):
        self.errors = errors
        super().__init__('El archivo CSV contiene errores.')


def _read_csv(uploaded_file):
    try:
        content = uploaded_file.read().decode('utf-8-sig')
    except UnicodeDecodeError:
        raise CSVImportError(['El archivo debe estar guardado con codificación UTF-8.'])

    try:
        dialect = csv.Sniffer().sniff(content[:2048], delimiters=',;')
    except csv.Error:
        dialect = csv.excel

    reader = csv.DictReader(io.StringIO(content), dialect=dialect)
    if not reader.fieldnames:
        raise CSVImportError(['El archivo está vacío.'])

    reader.fieldnames = [name.strip().lower() for name in reader.fieldnames]
    missing = [column for column in REQUIRED_COLUMNS if column not in reader.fieldnames]
    if missing:
        raise CSVImportError([f'Faltan columnas obligatorias: {", ".join(missing)}.'])

    return reader


def _parse_price(value):
    price = Decimal(value.replace(',', '.'))
    if price < 0:
        raise InvalidOperation
    return price.quantize(Decimal('0.01'))


def _parse_positive_int(value, default):
    if not value:
        return default
    number = int(value)
    if number < 0:
        raise ValueError
    return number


def _get_or_create_by_name(model, name):
    instance = model.objects.filter(name__iexact=name).first()
    if instance is None:
        instance = model.objects.create(name=name)
    return instance


def import_products_from_csv(uploaded_file, user):
    reader = _read_csv(uploaded_file)
    errors = []
    summary = {'created': 0, 'updated': 0, 'movements': 0}

    with transaction.atomic():
        for line, raw_row in enumerate(reader, start=2):
            row = {key: (value or '').strip() for key, value in raw_row.items() if key}

            if not any(row.values()):
                continue

            empty = [column for column in REQUIRED_COLUMNS if not row.get(column)]
            if empty:
                errors.append(f'Fila {line}: faltan valores en {", ".join(empty)}.')
                continue

            too_long = [column for column, limit in MAX_LENGTHS.items() if len(row[column]) > limit]
            if too_long:
                errors.append(f'Fila {line}: texto demasiado largo en {", ".join(too_long)}.')
                continue

            try:
                price = _parse_price(row['precio'])
            except InvalidOperation:
                errors.append(f'Fila {line}: el precio "{row["precio"]}" no es válido.')
                continue

            try:
                min_stock = _parse_positive_int(row.get('stock_minimo'), default=5)
                quantity = _parse_positive_int(row.get('entrada'), default=0)
            except ValueError:
                errors.append(f'Fila {line}: stock_minimo y entrada deben ser números enteros positivos.')
                continue

            category = _get_or_create_by_name(Category, row['categoria'])
            supplier = _get_or_create_by_name(Supplier, row['proveedor'])

            product, created = Product.objects.update_or_create(
                sku=row['sku'],
                defaults={
                    'name': row['nombre'],
                    'category': category,
                    'supplier': supplier,
                    'price': price,
                    'min_stock': min_stock,
                },
            )
            summary['created' if created else 'updated'] += 1

            if quantity > 0:
                StockMovement.objects.create(
                    product=product,
                    movement_type=StockMovement.MovementType.IN,
                    quantity=quantity,
                    note='Importación CSV',
                    created_by=user,
                )
                summary['movements'] += 1

        if errors:
            raise CSVImportError(errors)

    return summary