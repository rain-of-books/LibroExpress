# LibroExpress — Sistema de Gestión de Inventario

Sistema de escritorio para la gestión de inventario, ventas, clientes y proveedores de la librería y papelería **LibroExpress**. Desarrollado en **Python 3** con interfaz gráfica **PySide6** y persistencia en archivos **JSON**.

---

## Requisitos del Sistema

- Python 3.8 o superior
- PySide6 6.10.2 o superior (ver `requirements.txt`)

## Instalación

```bash
# 1. Crear entorno virtual
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux / macOS

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Ejecutar la aplicación
python main.py
```

---

## Estructura del Proyecto

```
LibroExpress/
├── main.py           # Capa de presentación: ventana principal y todos los diálogos PySide6
├── products.py       # Modelo Product + ProductManager (CRUD, persistencia JSON)
├── sales.py          # Modelo Sale + SaleManager (ventas, stock, generación de recibos)
├── clients.py        # Modelo Client + ClientManager (CRUD, búsqueda por documento)
├── suppliers.py      # Modelo Supplier + SupplierManager (CRUD, lista para combos)
├── database.py       # Utilidades de persistencia compartidas
├── products.json     # Almacén de productos (versionado)
├── clients.json      # Almacén de clientes (versionado)
├── suppliers.json    # Almacén de proveedores (versionado)
├── requirements.txt  # Dependencias Python
├── recibos/          # Comprobantes .txt generados por venta (no versionado)
└── sales.json        # Registro de ventas (no versionado)
```

---

## Arquitectura

El proyecto sigue una separación en dos capas:

- **Capa de dominio** (`products.py`, `sales.py`, `clients.py`, `suppliers.py`): modelos de datos, lógica de negocio y acceso/persistencia JSON. Cada módulo expone una clase `Manager` con métodos CRUD e identificadores únicos con formato `PREFIJO_AAAAMMDDHHMMSSXXXXXX`.
- **Capa de presentación** (`main.py`): clases `QDialog` y `QMainWindow` de PySide6. Cada operación de negocio se delega al `Manager` correspondiente; la UI solo gestiona entrada/salida de datos.

---

## Historial de Sprints

### Sprint 1 — Módulo de Inventario de Productos

**Objetivo:** Implementar el CRUD completo de productos con interfaz de escritorio.

**Implementación técnica:**
- Modelo `Product` con campos: `id`, `name`, `category`, `price`, `quantity`, `isbn`, `supplier`, `created_at`, `updated_at`. Generación de ID con timestamp y sufijo aleatorio (`PROD_YYYYMMDDHHMMSSXXXXXX`).
- `ProductManager`: métodos `add_product`, `update_product`, `delete_product`, `get_all_products`, `search_products`. Persistencia en `products.json` con codificación UTF-8.
- `MainWindow`: tabla `QTableWidget` con soporte de ordenación por columnas y filas con colores alternados.
- `ProductFormDialog`: formulario `QFormLayout` con validación de campos obligatorios (nombre, categoría, precio) y combo editable para categorías existentes.
- Búsqueda en tiempo real conectada a la señal `textChanged` del campo de búsqueda; filtrado por nombre, categoría o ambos.
- Barra de estado con contador de productos y mensajes de confirmación tras cada operación.
- Confirmación explícita mediante `QMessageBox` antes de eliminar un producto.

---

### Sprint 2 — Registro de Ventas y Recibos

**Objetivo:** Implementar el flujo completo de ventas con descuento automático de stock, aplicación de IVA y generación de comprobante.

**Implementación técnica:**
- Modelo `Sale` con campos: `id`, `items` (lista de `SaleItem`), `total`, `payment_method`, `received_amount`, `receipt_file`, `created_at`. Cada `SaleItem` almacena `product_id`, `product_name`, `quantity`, `unit_price`, `subtotal`.
- `SaleManager.create_sale()`: valida stock disponible por ítem, descuenta `quantity` de cada `Product`, calcula `total` neto, genera el recibo en texto plano y persiste la venta en `sales.json`.
- Constante `IVA_RATE = 0.19`; el total mostrado al usuario siempre incluye el 19% de IVA. Para pagos en efectivo se valida que el monto recibido sea mayor o igual al total con IVA.
- `SalesDialog`:
  - Combo de productos filtrado a los que tengan `quantity > 0`.
  - Buscador por nombre integrado con señal `textChanged` para filtrar el combo en tiempo real.
  - Tabla de ítems seleccionados con columnas: producto, cantidad, precio unitario, subtotal.
  - Etiqueta de total actualizada en cada cambio con desglose de IVA.
  - Validaciones en `accept()`: al menos un producto, monto recibido suficiente (efectivo).
- `generate_receipt_text(sale)`: genera el comprobante en texto plano con cabecera de tienda, línea por ítem, subtotales, IVA y total, guardado en `recibos/<id_venta>.txt`.
- `ReceiptDialog`: muestra el comprobante en `QTextEdit` de solo lectura con fuente monoespaciada (`Courier New`).
- La tabla de inventario en `MainWindow` se actualiza automáticamente tras cada venta.

---

### Sprint 3 — Clientes, Historial de Compras y Proveedores

**Objetivo:** Vincular ventas a clientes, permitir consultar el historial de compras por documento y gestionar el catálogo de proveedores.

**Implementación técnica:**

**HU-07 — Registro y búsqueda de clientes:**
- Modelo `Client` con campos: `id`, `name`, `document`, `email`, `phone`, `created_at`, `updated_at`. ID con prefijo `CLI_`.
- `ClientManager`: `add_client` lanza `ValueError` si el documento ya existe; `get_client_by_document` para búsqueda O(n) por cédula; `update_client` y `delete_client`. Persistencia en `clients.json`.
- `ClientFormDialog`: formulario con validación de todos los campos obligatorios y formato de correo mediante `re.fullmatch`.
- `SalesDialog` extendido: sección de búsqueda de cliente por cédula en la parte superior; si no existe, abre `ClientFormDialog` para registrarlo en el mismo flujo. El campo `selected_client` debe estar asignado para que `accept()` proceda.

**HU-08 — Historial de compras:**
- `SaleManager.get_sales_by_client_document(document)`: filtra las ventas cargadas desde `sales.json` por el campo `client_document`.
- `Sale.to_dict()` y `from_dict()` incluyen `client_document` y `client_name` para persistencia y deserialización.
- `generate_receipt_text()` imprime los datos del cliente en el encabezado del comprobante.
- `PurchaseHistoryDialog`: campo de cédula + botón de búsqueda; tabla con columnas ID, fecha, productos, detalles, nombre de archivo de factura y total con IVA. Doble clic sobre una fila o botón "Ver Factura" abre `ReceiptDialog` con el objeto `Sale` correspondiente.

**HU-09 — Gestión de proveedores:**
- Modelo `Supplier` con campos: `id`, `name`, `phone`, `email`, `address`, `created_at`, `updated_at`. ID con prefijo `SUP_`.
- `SupplierManager`: CRUD completo + `get_supplier_names()` que retorna lista de nombres para poblar combos. Persistencia en `suppliers.json`.
- `SupplierFormDialog`: formulario con validación de nombre obligatorio y formato de correo.
- `SupplierManagementDialog`: tabla con todas las columnas del proveedor; botones Nuevo, Editar, Eliminar con confirmación de eliminación.
- `ProductFormDialog` actualizado: campo proveedor reemplazado por `QComboBox` editable poblado desde `SupplierManager.get_supplier_names()`.

---

## Almacenamiento de Datos

Todos los modelos se serializan a JSON mediante métodos `to_dict()` / `from_dict()`. Ejemplo de estructura de un producto:

```json
{
  "id": "PROD_20260315120001ABC123",
  "name": "Diccionario de la RAE",
  "category": "Diccionarios",
  "price": 45000,
  "quantity": 12,
  "isbn": "978-84-376-0494-7",
  "supplier": "Editorial Planeta",
  "created_at": "2026-03-15T12:00:01",
  "updated_at": "2026-03-15T12:00:01"
}
```

Los archivos `sales.json` y `recibos/` se excluyen del repositorio mediante `.gitignore` al contener datos de ejecución variable.

---

## Sprint 4 — Pendiente

Funcionalidades planificadas para el siguiente ciclo:

- Control de stock mínimo con alertas visuales en inventario.
- Exportación de datos (CSV / Excel / PDF).
- Reportes avanzados de ventas por período.
- Indicadores de clientes frecuentes.

---

## Notas

Proyecto desarrollado con fines académicos en el marco de Ingeniería de Software III.