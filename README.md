# Sistema de Inventario - Django

Aplicación web para controlar el stock y los movimientos de productos de un almacén, desarrollada como proyecto del módulo de Django del máster Full Stack de Conquer Blocks.

## Demo

**Enlace:** https://inventario-bryan-onrender-com.onrender.com

| Usuario | Contraseña | Permisos |
|---|---|---|
| `Profesor` | `ConquerX` | Uso completo del inventario (sin acceso al panel de administración) |



> El servidor gratuito se suspende tras 15 minutos sin uso; la primera carga puede tardar alrededor de un minuto.

## Funcionalidades

### Obligatorias

- **Registro de entradas y salidas:** el stock se actualiza automáticamente con cada movimiento y nunca puede quedar en negativo. Los movimientos son inmutables, como en un libro contable.
- **Alerta de stock mínimo:** contador en el menú, página de reposición ordenada por urgencia, distintivo en la lista de productos y aviso inmediato tras cada salida.
- **Filtro por proveedor o categoría:** combinable con búsqueda por nombre o SKU y con la opción de mostrar solo productos con stock bajo.

### Extras

- **Importación masiva por CSV:** crea o actualiza productos por SKU, registra entradas de stock y valida todo el archivo en modo "todo o nada", mostrando los errores con su número de fila.
- **Gráficos de movimientos:** panel con resumen del inventario, entradas y salidas de los últimos 30 días y productos con más salidas.

### Además

- Gestión de productos, categorías y proveedores, con borrado protegido cuando hay registros asociados.
- Autenticación obligatoria en toda la aplicación.
- Panel de administración personalizado.
- Diseño adaptable a móvil y tablet.

## Tecnologías

- **Backend:** Python 3.12 y Django 6.1
- **Base de datos:** PostgreSQL en producción y SQLite en desarrollo
- **Frontend:** Bootstrap 5 y Chart.js
- **Despliegue:** Render, con Gunicorn y WhiteNoise

## Modelos

- `Category`: categorías de productos.
- `Supplier`: proveedores y sus datos de contacto.
- `Product`: productos con SKU único, precio, stock actual y stock mínimo.
- `StockMovement`: entradas y salidas, con usuario y fecha de registro.

## Instalación local

1. Clonar el repositorio:
   `git clone https://github.com/BryanE-sketch/Django---Sistema-de-inventario-.git`
2. Crear un entorno virtual e instalar las dependencias:
   `pip install -r requirements.txt`
3. Copiar `.env.example` a `.env` y rellenar los valores.
4. Aplicar las migraciones:
   `python manage.py migrate`
5. Crear un usuario administrador:
   `python manage.py createsuperuser`
6. Arrancar el servidor:
   `python manage.py runserver`

## Formato del CSV de importación

| Columna | Obligatoria | Ejemplo |
|---|---|---|
| `nombre` | Sí | Bolígrafo azul |
| `sku` | Sí | BOL-001 |
| `categoria` | Sí | Papeleria |
| `proveedor` | Sí | Bryan |
| `precio` | Sí | 1.50 o 1,50 |
| `stock_minimo` | No (por defecto 5) | 10 |
| `entrada` | No (por defecto 0) | 50 |

Desde la propia aplicación se puede descargar una plantilla de ejemplo.

