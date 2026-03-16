# LibroExpress - Sistema de Gestión de Inventario

## Sprint 1: Módulo básico de inventario de productos

Sistema de gestión para la librería y papelería LibroExpress desarrollado con **Python** y **PySide6**, almacenando la información en archivos **JSON**.

## 🚀 Características Implementadas

### ✅ Funcionalidades Sprint 1

1. **Registrar productos**
   - Formulario completo para ingresar nuevos productos
   - Campos: nombre, categoría, precio, cantidad, ISBN, proveedor
   - Validación de datos obligatorios
   - Almacenamiento automático en JSON

2. **Visualizar productos** 
   - Tabla completa con todos los productos del inventario
   - Información mostrada: nombre, categoría, ISBN, precio, proveedor, cantidad
   - Ordenación por columnas
   - Colores alternados para mejor legibilidad

3. **Buscar productos**
   - Búsqueda en tiempo real mientras escribes
   - Criterios de búsqueda: nombre, categoría o ambos
   - Filtrado instantáneo de resultados
   - Botón para limpiar búsqueda

4. **Editar información de productos**
   - Selección de productos desde la tabla
   - Formulario de edición con datos pre-cargados
   - Actualización inmediata en el inventario
   - Confirmación de cambios

5. **Actualización automática del inventario**
   - Refresco automático después de cada operación
   - Botón manual de actualización
   - Sincronización con archivo JSON
   - Contador de productos en barra de estado

### 📋 Requisitos del Sistema

- **Python 3.8+**
- **PySide6** 6.10.2+

## 🛠️ Instalación y Configuración

1. **Clonar o descargar el proyecto**
   ```bash
   cd LibroExpress-sistem
   ```

2. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

3. **Ejecutar la aplicación**
   ```bash
   python main.py
   ```

## 📁 Estructura del Proyecto

```
LibroExpress-sistem/
│
├── main.py              # Aplicación principal con GUI PySide6
├── products.py          # Lógica de gestión de productos y JSON
├── products.json        # Base de datos JSON con productos
├── requirements.txt     # Dependencias Python
│
└── README.md           # Documentación del proyecto
```

## 💻 Uso de la Aplicación

### Interfaz Principal
- **Tabla de inventario**: Muestra todos los productos registrados
- **Barra de búsqueda**: Filtrar productos por nombre o categoría
- **Botones de acción**: Nuevo, Editar, Eliminar, Actualizar

### Gestión de Productos

#### ➕ Añadir Nuevo Producto
1. Clic en **"Nuevo Producto"**
2. Completar el formulario:
   - **Nombre**: Obligatorio
   - **Categoría**: Obligatorio (se puede escribir nueva categoría)
   - **Precio**: En euros, obligatorio
   - **Cantidad**: Stock disponible
   - **ISBN**: Código del libro (opcional)
   - **Proveedor**: Nombre del distribuidor (opcional)
3. Clic en **"OK"** para guardar

#### ✏️ Editar Producto Existente
1. Seleccionar producto en la tabla
2. Clic en **"Editar Producto"**
3. Modificar campos necesarios
4. Clic en **"OK"** para actualizar

#### 🔍 Buscar Productos
1. Escribir en el campo de búsqueda
2. Seleccionar tipo de búsqueda:
   - **Todos**: Busca en nombre y categoría
   - **Nombre**: Solo en nombres de productos
   - **Categoría**: Solo en categorías
3. Los resultados se filtran automáticamente

#### 🗑️ Eliminar Productos
1. Seleccionar producto en la tabla
2. Clic en **"Eliminar Producto"**
3. Confirmar la eliminación

## 🗄️ Almacenamiento de Datos

Los productos se almacenan en `products.json` con la siguiente estructura:

```json
{
  "id": "PROD_20260315120001",
  "name": "Nombre del producto",
  "category": "Categoría",
  "price": 12.50,
  "quantity": 25,
  "isbn": "978-84-376-0494-7",
  "supplier": "Proveedor",
  "created_at": "2026-03-15T12:00:00",
  "updated_at": "2026-03-15T12:00:00"
}
```

## 🧪 Pruebas del Sistema

Ejecutar el script de pruebas para verificar funcionalidades básicas:

```bash
python test_system.py
```

## 🔧 Arquitectura Técnica

### Módulos Principales

#### `products.py`
- **Clase `Product`**: Modelo de datos del producto
- **Clase `ProductManager`**: Gestión CRUD y persistencia JSON
- Operaciones: crear, leer, actualizar, eliminar, buscar

#### `main.py`
- **Clase `MainWindow`**: Interfaz principal PySide6
- **Clase `ProductFormDialog`**: Formulario de productos
- Gestión de eventos y actualización de UI

## 🎯 Funcionalidades Técnicas Destacadas

### ✨ Características Avanzadas
- **IDs únicos automaticos**: Generación de identificadores únicos por producto
- **Validación de formularios**: Control de datos obligatorios y formatos
- **Búsqueda en tiempo real**: Filtrado instantáneo mientras escribes
- **Ordenación de tabla**: Clic en cabeceras para ordenar
- **Selección de filas completas**: Mejor experiencia de usuario
- **Confirmación de eliminación**: Prevención de borrado accidental
- **Barra de estado informativa**: Contador de productos y mensajes
- **Manejo de errores**: Captura y muestra de errores de usuario

### 🛡️ Robustez del Sistema
- **Manejo de archivos JSON**: Creación automática si no existe
- **Codificación UTF-8**: Soporte completo para caracteres especiales
- **Validación de datos**: Control de tipos y rangos de valores
- **Recuperación de errores**: Sistema resiliente ante fallos

## 📝 Próximos Sprints

**Sprint 2** podría incluir:
- Gestión de clientes
- Sistema de ventas
- Reportes básicos
- Backup automático

**Sprint 3** podría incluir:
- Gestión de proveedores
- Control de stock mínimo
- Historial de transacciones
- Exportación de datos

## 🤝 Contribución

Este es un proyecto educativo para aprender desarrollo de aplicaciones de escritorio con Python y PySide6.

## 📄 Licencia

Proyecto desarrollado con fines educativos.