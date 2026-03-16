"""
Aplicación principal del sistema LibroExpress - Sprint 1
Sistema de gestión de inventario de productos con PySide6
"""

import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
                              QWidget, QPushButton, QTableWidget, QTableWidgetItem,
                              QLineEdit, QLabel, QComboBox, QSpinBox, QDoubleSpinBox,
                              QFormLayout, QDialog, QDialogButtonBox, QMessageBox,
                              QGroupBox, QHeaderView, QAbstractItemView)
from PySide6.QtCore import Qt, QTimer, QRegularExpression
from PySide6.QtGui import QFont, QIcon, QRegularExpressionValidator
from products import ProductManager, Product


class ProductFormDialog(QDialog):
    """Diálogo para añadir/editar productos"""
    
    def __init__(self, parent=None, product=None, categories=None):
        super().__init__(parent)
        self.product = product
        self.categories = categories or []
        
        title = "Editar Producto" if product else "Nuevo Producto"
        self.setWindowTitle(title)
        self.setModal(True)
        self.resize(400, 350)
        
        self.setup_ui()
        if product:
            self.populate_fields()
    
    def setup_ui(self):
        """Configura la interfaz del diálogo"""
        layout = QVBoxLayout(self)
        
        # Formulario
        form_layout = QFormLayout()
        
        # Campos del formulario
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Ingrese el nombre del producto")
        
        self.category_combo = QComboBox()
        self.category_combo.setEditable(True)
        self.category_combo.addItem("")
        if self.categories:
            self.category_combo.addItems(self.categories)
        
        self.price_spinbox = QDoubleSpinBox()
        self.price_spinbox.setRange(5000, 10000000)
        self.price_spinbox.setDecimals(0)
        self.price_spinbox.setSuffix(" COP")
        self.price_spinbox.setSingleStep(1000)  # Incrementos de mil en mil
        self.price_spinbox.setValue(5000)  # Valor por defecto
        
        # Conectar evento para procesar el valor cuando termine de editar
        self.price_spinbox.editingFinished.connect(self.process_price_input)
        
        self.quantity_spinbox = QSpinBox()
        self.quantity_spinbox.setRange(0, 99999)
        
        self.isbn_edit = QLineEdit()
        self.isbn_edit.setPlaceholderText("Ej: 978-84-376-0494-7 (opcional)")
        self.isbn_edit.setMaxLength(20)  # Límite de caracteres para ISBN
        
        # Validador para ISBN: solo números, espacios y guiones
        isbn_regex = QRegularExpression("[0-9\\s\\-]*")
        isbn_validator = QRegularExpressionValidator(isbn_regex)
        self.isbn_edit.setValidator(isbn_validator)
        
        self.supplier_edit = QLineEdit()
        self.supplier_edit.setPlaceholderText("Nombre del proveedor (opcional)")
        
        # Añadir campos al formulario
        form_layout.addRow("Nombre del producto:", self.name_edit)
        form_layout.addRow("Categoría:", self.category_combo)
        form_layout.addRow("Precio (Mínimo $5,000):", self.price_spinbox)
        form_layout.addRow("Cantidad disponible:", self.quantity_spinbox)
        form_layout.addRow("Código ISBN:", self.isbn_edit)
        form_layout.addRow("Proveedor:", self.supplier_edit)
        
        layout.addLayout(form_layout)
        
        # Botones
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        layout.addWidget(button_box)
    
    def populate_fields(self):
        """Llena los campos con los datos del producto a editar"""
        if self.product:
            self.name_edit.setText(self.product.name)
            self.category_combo.setCurrentText(self.product.category)
            self.price_spinbox.setValue(self.product.price)
            self.quantity_spinbox.setValue(self.product.quantity)
            self.isbn_edit.setText(self.product.isbn)
            self.supplier_edit.setText(self.product.supplier)
    
    def get_form_data(self):
        """Obtiene los datos del formulario"""
        return {
            'name': self.name_edit.text().strip(),
            'category': self.category_combo.currentText().strip(),
            'price': self.price_spinbox.value(),
            'quantity': self.quantity_spinbox.value(),
            'isbn': self.isbn_edit.text().strip(),
            'supplier': self.supplier_edit.text().strip()
        }
    
    def process_price_input(self):
        """Valida que el precio no sea menor al mínimo de 5,000 COP"""
        current_value = int(self.price_spinbox.value())
        
        # Si el valor es menor que 5000, establecer el mínimo
        if current_value < 5000:
            self.price_spinbox.setValue(5000)
    
    def accept(self):
        """Valida y acepta el diálogo"""
        data = self.get_form_data()
        
        if not data['name']:
            QMessageBox.warning(self, "Error", "El nombre del producto es obligatorio.")
            return
        
        if not data['category']:
            QMessageBox.warning(self, "Error", "La categoría es obligatoria.")
            return
        
        if data['price'] < 5000:
            QMessageBox.warning(self, "Error", "El precio debe ser mayor o igual a $5,000 COP.")
            return
        
        super().accept()


class MainWindow(QMainWindow):
    """Ventana principal del sistema LibroExpress"""
    
    def __init__(self):
        super().__init__()
        self.product_manager = ProductManager()
        self.setup_ui()
        self.load_products()
        
        # Timer para actualización automática
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.refresh_products)
    
    def setup_ui(self):
        """Configura la interfaz principal"""
        self.setWindowTitle("LibroExpress - Sistema de Inventario")
        self.setMinimumSize(1000, 700)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        
        # Título
        title_label = QLabel("Sistema de Gestión de Inventario - LibroExpress")
        title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label)
        
        # Panel de búsqueda
        search_group = QGroupBox("Búsqueda de Productos")
        search_layout = QHBoxLayout(search_group)
        
        search_layout.addWidget(QLabel("Buscar:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Ingrese nombre o categoría...")
        self.search_edit.textChanged.connect(self.search_products)
        search_layout.addWidget(self.search_edit)
        
        self.search_type_combo = QComboBox()
        self.search_type_combo.addItems(["Todos", "Nombre", "Categoría"])
        self.search_type_combo.currentTextChanged.connect(self.search_products)
        search_layout.addWidget(self.search_type_combo)
        
        clear_search_btn = QPushButton("Limpiar")
        clear_search_btn.clicked.connect(self.clear_search)
        search_layout.addWidget(clear_search_btn)
        
        main_layout.addWidget(search_group)
        
        # Panel de botones
        button_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("Nuevo Producto")
        self.add_btn.clicked.connect(self.add_product)
        
        self.edit_btn = QPushButton("Editar Producto")
        self.edit_btn.clicked.connect(self.edit_product)
        self.edit_btn.setEnabled(False)
        
        self.delete_btn = QPushButton("Eliminar Producto")
        self.delete_btn.clicked.connect(self.delete_product)
        self.delete_btn.setEnabled(False)
        
        self.refresh_btn = QPushButton("Actualizar")
        self.refresh_btn.clicked.connect(self.refresh_products)
        
        button_layout.addWidget(self.add_btn)
        button_layout.addWidget(self.edit_btn)
        button_layout.addWidget(self.delete_btn)
        button_layout.addWidget(self.refresh_btn)
        button_layout.addStretch()
        
        main_layout.addLayout(button_layout)
        
        # Tabla de productos
        self.products_table = QTableWidget()
        self.setup_table()
        main_layout.addWidget(self.products_table)
        
        # Barra de estado
        self.statusBar().showMessage("Sistema iniciado correctamente")
    
    def setup_table(self):
        """Configura la tabla de productos"""
        headers = ["ID", "Nombre", "Categoría", "ISBN", "Precio", "Proveedor", "Cantidad"]
        self.products_table.setColumnCount(len(headers))
        self.products_table.setHorizontalHeaderLabels(headers)
        
        # Configurar el comportamiento de la tabla
        self.products_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.products_table.setAlternatingRowColors(True)
        self.products_table.setSortingEnabled(True)
        
        # Deshabilitar edición directa en celdas (solo edición por formulario)
        self.products_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        # Ocultar columna ID
        self.products_table.setColumnHidden(0, True)
        
        # Configurar el ancho de las columnas
        header = self.products_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Nombre
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Categoría
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # ISBN
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Precio
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Proveedor
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Cantidad
        
        # Configurar el header vertical (números de fila del lado izquierdo)
        vertical_header = self.products_table.verticalHeader()
        vertical_header.setSectionResizeMode(QHeaderView.Fixed)  # Altura fija de filas
        vertical_header.setDefaultSectionSize(30)  # Altura estándar de 30px
        vertical_header.setMinimumSectionSize(25)   # Altura mínima
        vertical_header.setMaximumSectionSize(40)   # Altura máxima
        
        # Conectar eventos de selección
        self.products_table.selectionModel().selectionChanged.connect(self.on_selection_changed)
    
    def load_products(self, products=None):
        """Carga los productos en la tabla"""
        if products is None:
            products = self.product_manager.get_all_products()
        
        self.products_table.setRowCount(len(products))
        
        for row, product in enumerate(products):
            self.products_table.setItem(row, 0, QTableWidgetItem(product.id))
            self.products_table.setItem(row, 1, QTableWidgetItem(product.name))
            self.products_table.setItem(row, 2, QTableWidgetItem(product.category))
            self.products_table.setItem(row, 3, QTableWidgetItem(product.isbn))
            self.products_table.setItem(row, 4, QTableWidgetItem(f"${product.price:,.0f} COP"))
            self.products_table.setItem(row, 5, QTableWidgetItem(product.supplier))
            self.products_table.setItem(row, 6, QTableWidgetItem(str(product.quantity)))
        
        # Actualizar contador en barra de estado
        self.statusBar().showMessage(f"Total de productos: {len(products)}")
    
    def on_selection_changed(self):
        """Maneja el cambio de selección en la tabla"""
        has_selection = bool(self.products_table.selectionModel().selectedRows())
        self.edit_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)
    
    def get_selected_product(self):
        """Obtiene el producto seleccionado"""
        selected_rows = self.products_table.selectionModel().selectedRows()
        if selected_rows:
            row = selected_rows[0].row()
            product_id = self.products_table.item(row, 0).text()
            return self.product_manager.get_product_by_id(product_id)
        return None
    
    def add_product(self):
        """Abre el diálogo para añadir un nuevo producto"""
        categories = self.product_manager.get_categories()
        dialog = ProductFormDialog(self, categories=categories)
        
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_form_data()
            try:
                self.product_manager.add_product(**data)
                self.refresh_products()
                QMessageBox.information(self, "Éxito", "Producto añadido correctamente.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al añadir producto: {str(e)}")
    
    def edit_product(self):
        """Abre el diálogo para editar el producto seleccionado"""
        product = self.get_selected_product()
        if not product:
            return
        
        categories = self.product_manager.get_categories()
        dialog = ProductFormDialog(self, product=product, categories=categories)
        
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_form_data()
            try:
                self.product_manager.update_product(product.id, **data)
                self.refresh_products()
                QMessageBox.information(self, "Éxito", "Producto actualizado correctamente.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al actualizar producto: {str(e)}")
    
    def delete_product(self):
        """Elimina el producto seleccionado"""
        product = self.get_selected_product()
        if not product:
            return
        
        reply = QMessageBox.question(
            self, "Confirmar eliminación",
            f"¿Está seguro de que desea eliminar el producto '{product.name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.product_manager.delete_product(product.id)
                self.refresh_products()
                QMessageBox.information(self, "Éxito", "Producto eliminado correctamente.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al eliminar producto: {str(e)}")
    
    def refresh_products(self):
        """Actualiza la lista de productos"""
        self.product_manager.load_products()
        if self.search_edit.text():
            self.search_products()
        else:
            self.load_products()
    
    def search_products(self):
        """Realiza la búsqueda de productos"""
        query = self.search_edit.text().strip()
        if not query:
            self.load_products()
            return
        
        search_type_map = {
            "Nombre": "name",
            "Categoría": "category",
            "Todos": "all"
        }
        
        search_type = search_type_map.get(self.search_type_combo.currentText(), "all")
        results = self.product_manager.search_products(query, search_type)
        self.load_products(results)
    
    def clear_search(self):
        """Limpia la búsqueda"""
        self.search_edit.clear()
        self.search_type_combo.setCurrentText("Todos")
        self.load_products()


def main():
    """Función principal"""
    app = QApplication(sys.argv)
    
    # Establecer el estilo de la aplicación
    app.setStyle('Fusion')
    
    # Crear y mostrar la ventana principal
    window = MainWindow()
    window.show()
    
    # Ejecutar la aplicación
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
