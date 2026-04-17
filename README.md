# LibroExpress — Sistema de Gestión de Inventario

Sistema de escritorio para la gestión de inventario, ventas, clientes y proveedores de la librería y papelería **LibroExpress**. Desarrollado en **Python 3** con interfaz gráfica **PySide6** y persistencia en archivos **JSON**.

---

## Requisitos del Sistema

- Python 3.8 o superior
- PySide6 6.10.2 o superior (ver `requirements.txt`)

## Instalación

> [!IMPORTANT]
> Se recomienda trabajar siempre dentro del entorno virtual `venv` para evitar conflictos de dependencias entre PySide6, pytest y pywinauto.

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

> [!TIP]
> En Windows puedes activar el entorno con `venv\Scripts\activate` en `cmd` o con `venv\Scripts\Activate` en PowerShell.

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

> [!NOTE]
> La lógica crítica del negocio se mantiene fuera de la interfaz gráfica. Esto permite probar los módulos con tests unitarios sin depender de PySide6 ni de interacción visual.

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

Los archivos `sales.json`, `recibos/`, `restock_orders.json` y `ordenes_reabastecimiento/` se excluyen del repositorio mediante `.gitignore` al contener datos de ejecución variable.

> [!WARNING]
> Los archivos JSON del proyecto representan el estado operativo de la aplicación. Si se modifican manualmente con formato inválido o datos inconsistentes, algunos módulos pueden fallar al cargar información.

---

## Sprint 4 — Reabastecimiento y Reportes

Historias implementadas en este sprint:

- **HU-10: Órdenes de reabastecimiento**
  - Módulo para seleccionar proveedor, productos y cantidades.
  - Creación y persistencia de órdenes en `restock_orders.json`.
  - Generación automática de archivo `.txt` por orden en `ordenes_reabastecimiento/`.
  - Visualización de órdenes guardadas y descarga manual del archivo para envío al proveedor.

- **HU-11: Reportes de ventas por rango de fechas**
  - Módulo de reportes con filtros de fecha inicial y final.
  - Visualización tabular del detalle de ventas por producto:
    ID venta, fecha, cliente, documento, producto, cantidad, precio unitario, subtotal y método de pago.
  - Resumen en pantalla con número de ventas, subtotal, IVA y total.

- **HU-12: Exportación de reportes**
  - Exportación habilitada solo después de generar y visualizar el reporte.
  - Formatos disponibles: CSV, Excel (`.xlsx`) y PDF.
  - Motor de exportación desacoplado en `reports.py`.

---

## Sprint 5 — Vista General (Dashboard Ejecutivo)

Historias implementadas en este sprint:

- **HU-13: Dashboard de indicadores del negocio**
  - Módulo **Vista General** accesible desde la ventana principal para el rol gerente.
  - Indicadores resumidos en pantalla:
    - **Ventas del dia** (monto con IVA y cantidad de ventas del dia seleccionado).
    - **Producto mas vendido** (por unidades del dia seleccionado; vacio si no hay ventas).
    - **Total ingresos (rango)** (ventas con IVA filtradas por fecha desde/hasta).
  - Estadisticas generales de apoyo: total de ventas del rango, total de unidades vendidas en el rango y periodo consultado.
  - Logica de calculo desacoplada en `reports.py` mediante `build_dashboard_metrics`, reutilizable y cubierta con pruebas unitarias.
  - Se añadieron estilos visuales (CSS/PySide6 QSS) al programa para mejorar la experiencia de usuario en la interfaz del dashboard y formularios.
  - Se crearon pruebas unitarias adicionales para validar el comportamiento del dashboard y la consistencia de los indicadores.

---

## Pruebas Automatizadas UI

La carpeta `libroexpress_tests/pywinauto_tests` contiene la suite de automatizacion visual de los modulos de productos, ventas, clientes, historial de compras, proveedores y reabastecimiento usando **pywinauto**. La suite prioriza flujos visibles, lineales y reproducibles para dejar evidencia clara del comportamiento del sistema.

> [!IMPORTANT]
> Las pruebas se ejecutan sobre una copia temporal del proyecto para no alterar los datos reales del repositorio. El orden de ejecucion es intencional y sigue el flujo funcional solicitado para la entrega.

### Objetivo de la suite

- Validar el flujo visible de productos, ventas, clientes, historial de compras, proveedores y reabastecimiento desde la interfaz real.
- Confirmar que cada accion ejecutada en la UI deja el estado esperado en los archivos `products.json`, `clients.json`, `sales.json`, `suppliers.json` y `restock_orders.json` cuando aplica.
- Ejecutar cada prueba en una copia temporal del proyecto para no alterar los datos reales del repositorio.

### Aislamiento de pruebas

El fixture `isolated_project` en `libroexpress_tests/pywinauto_tests/tests/conftest.py` crea una copia temporal del proyecto, reinicia los archivos `products.json`, `clients.json`, `suppliers.json`, `sales.json` y `restock_orders.json` a `[]`, y elimina esa copia al finalizar la prueba. Esto garantiza que los robots no modifiquen los JSON reales del sistema.

> [!NOTE]
> Gracias a este aislamiento, los robots pueden crear, editar y eliminar datos sin contaminar el estado real del proyecto ni afectar evidencia previa almacenada en el repositorio.

### Alcance de este listado

Esta lista describe únicamente los casos de la suite de pruebas UI basada en `pywinauto`, ubicada en `libroexpress_tests/pywinauto_tests/tests/`.

El proyecto también contiene una suite de pruebas unitarias independientes en `libroexpress_tests/unit_tests/tests/`, con archivos como:

- `test_products.py`
- `test_suppliers.py`
- `test_clients.py`
- `test_sales.py`
- `test_restock.py`
- `test_reports.py`

Para ejecutar todas las pruebas unitarias use:

```bash
python -m pytest libroexpress_tests/unit_tests/tests -q
```

### Orden oficial de ejecucion

La suite fuerza el siguiente orden mediante `pytest_collection_modifyitems`:

1. `test_editar_producto_valido.py`
2. `test_producto_invalido_sin_nombre.py`
3. `test_crear_y_eliminar_producto_valido.py`
4. `test_registro_venta_sin_cliente.py`
5. `test_registro_cliente_sin_telefono.py`
6. `test_registro_cliente_valido.py`
7. `test_registro_venta_monto_insuficiente.py`
8. `test_registro_venta_valida.py`
9. `test_historial_compras_sin_cedula.py`
10. `test_historial_compras_con_cedula.py`
11. `test_editar_proveedor_existente.py`
12. `test_reabastecimiento_visualizacion_inicial.py`
13. `test_reabastecimiento_crear_orden_valida.py`
14. `test_reabastecimiento_visualizar_orden.py`
15. `test_reabastecimiento_eliminar_orden.py`

Este orden se definio para reflejar el flujo funcional solicitado y evitar redundancia entre escenarios.

> [!TIP]
> Si necesitas comprobar rapidamente que el orden sigue correcto, usa `python -m pytest libroexpress_tests/pywinauto_tests/tests -vv --collect-only`.

### Escenarios documentados

#### 1. Edicion valida de producto

Archivo: `libroexpress_tests/pywinauto_tests/tests/test_editar_producto_valido.py`

Flujo validado:

- Crea un producto valido desde la ventana principal.
- Cierra la aplicacion y la vuelve a abrir.
- Busca el producto por nombre exacto.
- Edita **categoria**, **precio**, **ISBN** y **proveedor** sin cambiar el nombre.
- Verifica en `products.json` que el producto sigue existiendo y que los nuevos valores fueron persistidos correctamente.

Datos esperados al final:

- El nombre permanece igual.
- La categoria cambia a `Utiles`.
- El precio cambia a `25000`.
- El ISBN cambia a `9781234567890`.
- El proveedor cambia a `Proveedor Editado`.

#### 2. Producto invalido sin nombre

Archivo: `libroexpress_tests/pywinauto_tests/tests/test_producto_invalido_sin_nombre.py`

Flujo validado:

- Abre el formulario de nuevo producto.
- Intenta guardar el producto sin diligenciar el nombre.
- Captura el mensaje de error o validacion mostrado por la UI.
- Verifica que `products.json` siga vacio.

Resultado esperado:

- La interfaz rechaza el registro.
- El mensaje contiene alguna referencia a error, validacion, nombre u obligatoriedad del campo.
- No se persiste ningun producto.

#### 3. Creacion y eliminacion de producto valido

Archivo: `libroexpress_tests/pywinauto_tests/tests/test_crear_y_eliminar_producto_valido.py`

Flujo validado:

- Crea un producto valido desde la UI.
- Cierra la aplicacion y la vuelve a abrir.
- Confirma que el producto fue persistido.
- Busca el producto por nombre exacto.
- Ejecuta la eliminacion desde el boton de la interfaz.
- Verifica que `products.json` quede vacio despues de eliminar.

Resultado esperado:

- El producto existe despues de la creacion.
- El producto desaparece despues de la eliminacion.
- La persistencia queda consistente con la accion visual ejecutada.

#### 4. Registro de venta sin cliente

Archivo: `libroexpress_tests/pywinauto_tests/tests/test_registro_venta_sin_cliente.py`

Flujo validado:

- El sistema inicia con el producto editado ya cargado en `products.json`.
- Se abre el modulo `Registrar Venta`.
- Se busca el producto `Producto Valido` y se agrega a la venta.
- Se escribe un monto recibido valido para la transaccion.
- Se intenta confirmar la venta sin haber buscado ni registrado un cliente.

Resultado esperado:

- La interfaz bloquea la venta por falta de cliente.
- `sales.json` permanece vacio.

#### 4.1 Registro de cliente sin telefono desde ventas

Archivo: `libroexpress_tests/pywinauto_tests/tests/test_registro_cliente_sin_telefono.py`

Flujo validado:

- Desde `Registrar Venta` se abre el formulario `Registrar Cliente`.
- Se diligencian nombre, documento y correo.
- El campo telefono se deja vacio.
- Se intenta guardar el cliente.

Resultado esperado:

- La interfaz muestra error o validacion por campo obligatorio.
- `clients.json` permanece vacio.

#### 4.2 Registro de cliente valido desde ventas

Archivo: `libroexpress_tests/pywinauto_tests/tests/test_registro_cliente_valido.py`

Flujo validado:

- Desde `Registrar Venta` se abre `Registrar Cliente`.
- Se diligencian todos los campos requeridos correctamente.
- Se guarda el cliente y luego se cierra el sistema.

Resultado esperado:

- El cliente se persiste en `clients.json`.
- La operacion termina con confirmacion exitosa.

#### 4.3 Venta invalida por monto insuficiente

Archivo: `libroexpress_tests/pywinauto_tests/tests/test_registro_venta_monto_insuficiente.py`

Flujo validado:

- El sistema inicia con un cliente valido y el producto `Producto Valido` ya cargados.
- En `Registrar Venta` se busca el cliente existente.
- Se busca el producto y se agrega a la venta.
- En `Resumen de la venta`, campo `Monto recibido`, se escribe `25000`.
- Se intenta confirmar la venta.

Resultado esperado:

- La interfaz rechaza la venta por monto insuficiente.
- `sales.json` permanece vacio.
- El stock del producto no cambia.

#### 4.4 Venta valida con cliente existente

Archivo: `libroexpress_tests/pywinauto_tests/tests/test_registro_venta_valida.py`

Flujo validado:

- El sistema inicia con un cliente valido y el producto `Producto Valido` ya cargados.
- En `Registrar Venta` se busca el cliente existente por cédula.
- Se busca el producto y se agrega a la venta.
- En `Resumen de la venta`, campo `Monto recibido`, se escribe `30000`.
- Se confirma la venta y se cierra el comprobante generado.

Resultado esperado:

- La venta se persiste en `sales.json`.
- El producto queda registrado dentro de la venta.
- El stock baja de `5` a `4`.
- El flujo termina con comprobante de venta valido.

#### 5. Historial de compras sin cedula

Archivo: `libroexpress_tests/pywinauto_tests/tests/test_historial_compras_sin_cedula.py`

Flujo validado:

- El sistema inicia con el producto `Producto Valido` ya actualizado luego del flujo de venta.
- Se abre el modulo `Historial Compras`.
- Se pulsa `Buscar` sin ingresar cédula.
- Se captura el mensaje de error o validacion mostrado por la interfaz.

Resultado esperado:

- La interfaz bloquea la busqueda sin documento.
- El sistema muestra un mensaje de error o validacion.
- El flujo se cierra sin alterar ventas ni clientes.

#### 5.1 Historial de compras con cedula

Archivo: `libroexpress_tests/pywinauto_tests/tests/test_historial_compras_con_cedula.py`

Flujo validado:

- El sistema inicia con cliente, producto y venta ya cargados.
- Se abre `Historial Compras`.
- Se escribe la cédula del cliente existente.
- Se pulsa `Buscar` y luego `Ver Factura` para ejecutar el flujo visual completo.

Resultado esperado:

- La tabla del historial muestra al menos una compra asociada al cliente.
- El flujo de visualizacion se ejecuta sin bloquear la prueba.

#### 6. Edicion de proveedor existente

Archivo: `libroexpress_tests/pywinauto_tests/tests/test_editar_proveedor_existente.py`

Flujo validado:

- El sistema inicia con un proveedor existente llamado `Proveedor Editado` asociado a `Producto Valido`.
- Se abre el modulo `Proveedores`.
- Se selecciona el proveedor existente y se pulsa `Editar`.
- Se completan los campos `telefono`, `correo` y `direccion`.
- Se guarda y se cierra el flujo.

Resultado esperado:

- La interfaz permite completar la informacion faltante del proveedor.
- El flujo termina sin bloqueo y con confirmacion visual.

#### 7. Reabastecimiento sin productos agregados

Archivo: `libroexpress_tests/pywinauto_tests/tests/test_reabastecimiento_visualizacion_inicial.py`

Flujo validado:

- El sistema inicia con `Proveedor Editado` y `Producto Valido` asociados.
- Se abre el modulo `Reabastecimiento`.
- Se pulsa `Crear orden` sin agregar productos a la orden.
- Se captura el mensaje de error o validacion.

Resultado esperado:

- La interfaz rechaza la creacion de la orden vacia.
- El flujo se cierra correctamente despues del mensaje.

#### 7.1 Creacion valida de orden de reabastecimiento

Archivo: `libroexpress_tests/pywinauto_tests/tests/test_reabastecimiento_crear_orden_valida.py`

Flujo validado:

- Se abre `Reabastecimiento`.
- Se agrega `Producto Valido` a la orden.
- Se pulsa `Crear orden`.
- Se captura el mensaje de confirmacion y se cierra el flujo.

Resultado esperado:

- La orden se crea correctamente.
- `restock_orders.json` registra al menos una orden.

#### 7.2 Visualizacion de orden creada

Archivo: `libroexpress_tests/pywinauto_tests/tests/test_reabastecimiento_visualizar_orden.py`

Flujo validado:

- Se abre `Reabastecimiento`.
- Se selecciona una orden ya creada en la tabla de ordenes guardadas.
- Se pulsa `Visualizar orden`.
- Se ejecuta el flujo de vista previa y luego se cierra.

Resultado esperado:

- La interfaz permite ejecutar el flujo de visualizacion de la orden seleccionada.
- La prueba valida el recorrido completo sin depender estrictamente de la detección del popup por UIA.

#### 7.3 Eliminacion de orden creada

Archivo: `libroexpress_tests/pywinauto_tests/tests/test_reabastecimiento_eliminar_orden.py`

Flujo validado:

- Se abre `Reabastecimiento`.
- Se selecciona una orden ya creada.
- Se pulsa `Eliminar orden`.
- Ante el dialogo de confirmacion se confirma con `Yes` y se cierra el mensaje final.

Resultado esperado:

- La orden se elimina del sistema.
- El flujo contempla fallback por teclado para confirmar `Yes` cuando el cuadro de confirmacion no es detectable por UIA.

### Soporte de automatizacion agregado en la app

Para hacer estable el escenario de eliminacion automatizada, `main.py` incluye dos ayudas de interfaz:

- Soporte de busqueda exacta para que un nombre buscado deje listo el producto correcto para editar o eliminar.
- Confirmacion automatica del dialogo de borrado cuando la app se ejecuta con la variable de entorno `LIBROEXPRESS_UI_AUTO_CONFIRM_DELETE=1`.

Esta variable se establece unicamente al lanzar la app desde `libroexpress_tests/pywinauto_tests/pages/main_window.py`, por lo que el comportamiento normal para uso manual no cambia.

> [!CAUTION]
> La confirmacion automatica de eliminacion existe solo para la ejecucion controlada de robots UI. No debe reutilizarse como atajo funcional fuera del contexto de pruebas automatizadas.

### Ejecucion en consola

Desde la raiz del proyecto:

```bash
venv\Scripts\activate
python -m pytest libroexpress_tests/pywinauto_tests/tests -vv
```

Para verificar solo el orden recolectado por `pytest`:

```bash
python -m pytest libroexpress_tests/pywinauto_tests/tests -vv --collect-only
```

### Cobertura intencional

La suite UI actual cubre los flujos lineales definidos para productos, ventas, clientes, historial de compras, proveedores y reabastecimiento. En algunos escenarios se prioriza la validacion del recorrido visual completo sobre la inspeccion estricta de popups cuando Pywinauto presenta limitaciones de detección en ciertos dialogos modales.

> [!WARNING]
> Ejecutar pruebas pywinauto mientras manipulas manualmente la misma ventana puede interferir con el foco, los dialogos y el resultado de la automatizacion.

---

## Notas

Proyecto desarrollado con fines académicos en el marco de Ingeniería de Software III.
