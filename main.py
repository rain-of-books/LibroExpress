"""
Aplicación principal del sistema LibroExpress - Sprint 2
Sistema de gestión de inventario y ventas con PySide6
"""

import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
                              QWidget, QPushButton, QTableWidget, QTableWidgetItem,
                              QLineEdit, QLabel, QComboBox, QSpinBox, QDoubleSpinBox,
                              QFormLayout, QDialog, QDialogButtonBox, QMessageBox,
                              QGroupBox, QHeaderView, QAbstractItemView, QTextEdit)
from PySide6.QtCore import Qt, QTimer, QRegularExpression
from PySide6.QtGui import QFont, QRegularExpressionValidator
from products import ProductManager
from sales import SaleManager, generate_receipt_text, IVA_RATE


class ProductFormDialog(QDialog):
    """Diálogo para añadir o editar productos."""

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
        """Configura la interfaz del diálogo."""
        layout = QVBoxLayout(self)

        form_layout = QFormLayout()

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
        self.price_spinbox.setSingleStep(1000)
        self.price_spinbox.setValue(5000)
        self.price_spinbox.editingFinished.connect(self.process_price_input)

        self.quantity_spinbox = QSpinBox()
        self.quantity_spinbox.setRange(0, 99999)

        self.isbn_edit = QLineEdit()
        self.isbn_edit.setPlaceholderText("Ej: 978-84-376-0494-7 (opcional)")
        self.isbn_edit.setMaxLength(20)

        isbn_regex = QRegularExpression("[0-9\\s\\-]*")
        isbn_validator = QRegularExpressionValidator(isbn_regex)
        self.isbn_edit.setValidator(isbn_validator)

        self.supplier_edit = QLineEdit()
        self.supplier_edit.setPlaceholderText("Nombre del proveedor (opcional)")

        form_layout.addRow("Nombre del producto:", self.name_edit)
        form_layout.addRow("Categoría:", self.category_combo)
        form_layout.addRow("Precio (Mínimo $5,000):", self.price_spinbox)
        form_layout.addRow("Cantidad disponible:", self.quantity_spinbox)
        form_layout.addRow("Código ISBN:", self.isbn_edit)
        form_layout.addRow("Proveedor:", self.supplier_edit)

        layout.addLayout(form_layout)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def populate_fields(self):
        """Llena los campos con los datos del producto a editar."""
        if self.product:
            self.name_edit.setText(self.product.name)
            self.category_combo.setCurrentText(self.product.category)
            self.price_spinbox.setValue(self.product.price)
            self.quantity_spinbox.setValue(self.product.quantity)
            self.isbn_edit.setText(self.product.isbn)
            self.supplier_edit.setText(self.product.supplier)

    def get_form_data(self):
        """Obtiene los datos del formulario."""
        return {
            "name": self.name_edit.text().strip(),
            "category": self.category_combo.currentText().strip(),
            "price": self.price_spinbox.value(),
            "quantity": self.quantity_spinbox.value(),
            "isbn": self.isbn_edit.text().strip(),
            "supplier": self.supplier_edit.text().strip(),
        }

    def process_price_input(self):
        """Valida que el precio no sea menor al mínimo permitido."""
        if int(self.price_spinbox.value()) < 5000:
            self.price_spinbox.setValue(5000)

    def accept(self):
        """Valida y acepta el diálogo."""
        data = self.get_form_data()

        if not data["name"]:
            QMessageBox.warning(self, "Error", "El nombre del producto es obligatorio.")
            return

        if not data["category"]:
            QMessageBox.warning(self, "Error", "La categoría es obligatoria.")
            return

        if data["price"] < 5000:
            QMessageBox.warning(self, "Error", "El precio debe ser mayor o igual a $5,000 COP.")
            return

        super().accept()


class SalesDialog(QDialog):
    """Diálogo para registrar una nueva venta."""

    def __init__(self, products, parent=None):
        super().__init__(parent)
        self.products = [product for product in products if product.quantity > 0]
        self.selected_items = {}

        self.setWindowTitle("Registrar Venta")
        self.setModal(True)
        self.resize(760, 520)

        self.setup_ui()
        self.load_available_products()
        self.update_total()

    def setup_ui(self):
        """Construye la pantalla de registro de ventas."""
        layout = QVBoxLayout(self)

        title_label = QLabel("Registro de ventas")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        selector_group = QGroupBox("Selección de productos")
        selector_layout = QHBoxLayout(selector_group)

        selector_layout.addWidget(QLabel("Producto:"))
        self.product_combo = QComboBox()
        selector_layout.addWidget(self.product_combo, 1)

        selector_layout.addWidget(QLabel("Cantidad:"))
        self.quantity_spinbox = QSpinBox()
        self.quantity_spinbox.setRange(1, 9999)
        selector_layout.addWidget(self.quantity_spinbox)

        self.add_item_btn = QPushButton("Agregar")
        self.add_item_btn.clicked.connect(self.add_sale_item)
        selector_layout.addWidget(self.add_item_btn)

        layout.addWidget(selector_group)

        self.items_table = QTableWidget()
        self.items_table.setColumnCount(5)
        self.items_table.setHorizontalHeaderLabels(
            ["ID", "Producto", "Cantidad", "Precio unitario", "Subtotal"]
        )
        self.items_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.items_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.items_table.setAlternatingRowColors(True)
        self.items_table.setColumnHidden(0, True)

        header = self.items_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        layout.addWidget(self.items_table)

        actions_layout = QHBoxLayout()
        self.remove_item_btn = QPushButton("Quitar producto")
        self.remove_item_btn.clicked.connect(self.remove_selected_item)
        actions_layout.addWidget(self.remove_item_btn)
        actions_layout.addStretch()
        layout.addLayout(actions_layout)

        summary_group = QGroupBox("Resumen de la venta")
        summary_layout = QFormLayout(summary_group)

        self.payment_combo = QComboBox()
        self.payment_combo.addItems(["Efectivo", "Tarjeta"])
        summary_layout.addRow("Método de pago:", self.payment_combo)

        self.received_label = QLabel("Monto recibido:")
        self.received_spinbox = QDoubleSpinBox()
        self.received_spinbox.setRange(0, 999999999)
        self.received_spinbox.setDecimals(0)
        self.received_spinbox.setSuffix(" COP")
        self.received_spinbox.setSingleStep(1000)
        self.received_spinbox.setValue(0)
        summary_layout.addRow(self.received_label, self.received_spinbox)

        self.payment_combo.currentTextChanged.connect(self.on_payment_method_changed)

        self.total_label = QLabel("$0 COP")
        total_font = QFont()
        total_font.setPointSize(12)
        total_font.setBold(True)
        self.total_label.setFont(total_font)
        summary_layout.addRow("Total:", self.total_label)

        layout.addWidget(summary_group)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.button(QDialogButtonBox.Ok).setText("Confirmar venta")
        button_box.button(QDialogButtonBox.Cancel).setText("Cancelar")
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def load_available_products(self):
        """Carga los productos disponibles para vender."""
        self.product_combo.clear()

        for product in self.products:
            label = f"{product.name} | Stock: {product.quantity} | ${product.price:,.0f} COP"
            self.product_combo.addItem(label, product.id)

        has_products = self.product_combo.count() > 0
        self.add_item_btn.setEnabled(has_products)
        self.product_combo.setEnabled(has_products)
        self.quantity_spinbox.setEnabled(has_products)

        if not has_products:
            self.product_combo.addItem("No hay productos con stock disponible", "")

    def get_product_by_id(self, product_id):
        """Obtiene un producto de la lista cargada en el diálogo."""
        for product in self.products:
            if product.id == product_id:
                return product
        return None

    def add_sale_item(self):
        """Agrega un producto a la venta y recalcula el total."""
        product_id = self.product_combo.currentData()
        product = self.get_product_by_id(product_id)
        quantity = self.quantity_spinbox.value()

        if not product:
            QMessageBox.warning(self, "Error", "Seleccione un producto válido.")
            return

        current_quantity = self.selected_items.get(product_id, {}).get("quantity", 0)
        new_quantity = current_quantity + quantity

        if new_quantity > product.quantity:
            QMessageBox.warning(
                self,
                "Stock insuficiente",
                f"No puede vender más de {product.quantity} unidades de '{product.name}'.",
            )
            return

        self.selected_items[product_id] = {
            "product": product,
            "quantity": new_quantity,
        }
        self.refresh_items_table()

    def remove_selected_item(self):
        """Elimina el producto seleccionado de la venta."""
        selected_rows = self.items_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Error", "Seleccione un producto de la venta.")
            return

        row = selected_rows[0].row()
        product_id = self.items_table.item(row, 0).text()
        self.selected_items.pop(product_id, None)
        self.refresh_items_table()

    def refresh_items_table(self):
        """Actualiza la tabla del carrito de venta."""
        items = list(self.selected_items.values())
        self.items_table.setRowCount(len(items))

        for row, item in enumerate(items):
            product = item["product"]
            quantity = item["quantity"]
            subtotal = product.price * quantity

            self.items_table.setItem(row, 0, QTableWidgetItem(product.id))
            self.items_table.setItem(row, 1, QTableWidgetItem(product.name))
            self.items_table.setItem(row, 2, QTableWidgetItem(str(quantity)))
            self.items_table.setItem(row, 3, QTableWidgetItem(f"${product.price:,.0f} COP"))
            self.items_table.setItem(row, 4, QTableWidgetItem(f"${subtotal:,.0f} COP"))

        self.update_total()

    def _get_net_total(self) -> float:
        """Calcula el subtotal neto sin IVA."""
        return sum(
            item["product"].price * item["quantity"]
            for item in self.selected_items.values()
        )

    def _get_total_with_iva(self) -> float:
        """Calcula el total final con IVA incluido."""
        from sales import IVA_RATE

        net = self._get_net_total()
        iva = round(net * IVA_RATE)
        return net + iva

    def update_total(self):
        """Muestra el total final con IVA incluido."""
        from sales import IVA_RATE

        net = self._get_net_total()
        iva = round(net * IVA_RATE)
        total_with_iva = net + iva
        self.total_label.setText(
            f"${total_with_iva:,.0f} COP  (IVA 19%: ${iva:,.0f} COP)"
        )

    def on_payment_method_changed(self, method: str):
        """Muestra el campo de monto recibido solo para pago en efectivo."""
        is_cash = method == "Efectivo"
        self.received_label.setVisible(is_cash)
        self.received_spinbox.setVisible(is_cash)
        if not is_cash:
            self.received_spinbox.setValue(0)

    def get_sale_data(self):
        """Retorna la información necesaria para persistir la venta."""
        items = []
        for product_id, item in self.selected_items.items():
            items.append({
                "product_id": product_id,
                "quantity": item["quantity"],
            })

        return {
            "items": items,
            "payment_method": self.payment_combo.currentText(),
            "received_amount": self.received_spinbox.value(),
        }

    def accept(self):
        """Valida que la venta esté completa antes de confirmar."""
        if not self.selected_items:
            QMessageBox.warning(self, "Error", "Agregue al menos un producto a la venta.")
            return

        if self.payment_combo.currentText() == "Efectivo":
            total_with_iva = self._get_total_with_iva()
            received = self.received_spinbox.value()
            if received < total_with_iva:
                QMessageBox.warning(
                    self,
                    "Monto insuficiente",
                    f"El monto recibido (${received:,.0f} COP) es menor al total "
                    f"a pagar con IVA (${total_with_iva:,.0f} COP).",
                )
                return

        super().accept()


class ReceiptDialog(QDialog):
    """Diálogo que muestra el recibo de una venta confirmada."""

    def __init__(self, sale, parent=None):
        super().__init__(parent)
        self.sale = sale

        self.setWindowTitle("Recibo de Venta")
        self.setModal(True)
        self.resize(520, 600)

        self.setup_ui()

    def setup_ui(self):
        """Construye el comprobante de la venta."""
        layout = QVBoxLayout(self)

        title_label = QLabel("Comprobante de venta")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        info_label = QLabel(
            f"Venta: {self.sale.id}\n"
            f"Fecha: {self.sale.created_at}\n"
            f"Método de pago: {self.sale.payment_method}"
        )
        layout.addWidget(info_label)

        receipt_text = QTextEdit()
        receipt_text.setReadOnly(True)
        receipt_text.setFont(QFont("Courier New", 10))
        receipt_text.setPlainText(self.build_receipt_text())
        layout.addWidget(receipt_text)

        close_button = QPushButton("Cerrar")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button, alignment=Qt.AlignRight)

    def build_receipt_text(self):
        """Genera el texto del recibo con formato de factura."""
        return generate_receipt_text(self.sale)


class MainWindow(QMainWindow):
    """Ventana principal del sistema LibroExpress."""

    def __init__(self):
        super().__init__()
        self.product_manager = ProductManager()
        self.sale_manager = SaleManager(self.product_manager)
        self.setup_ui()
        self.load_products()

        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.refresh_products)

    def setup_ui(self):
        """Configura la interfaz principal."""
        self.setWindowTitle("LibroExpress - Sistema de Inventario y Ventas")
        self.setMinimumSize(1000, 700)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)

        title_label = QLabel("Sistema de Gestión de Inventario y Ventas - LibroExpress")
        title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label)

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

        button_layout = QHBoxLayout()

        self.add_btn = QPushButton("Nuevo Producto")
        self.add_btn.clicked.connect(self.add_product)

        self.edit_btn = QPushButton("Editar Producto")
        self.edit_btn.clicked.connect(self.edit_product)
        self.edit_btn.setEnabled(False)

        self.delete_btn = QPushButton("Eliminar Producto")
        self.delete_btn.clicked.connect(self.delete_product)
        self.delete_btn.setEnabled(False)

        self.sale_btn = QPushButton("Registrar Venta")
        self.sale_btn.clicked.connect(self.register_sale)

        self.refresh_btn = QPushButton("Actualizar")
        self.refresh_btn.clicked.connect(self.refresh_products)

        button_layout.addWidget(self.add_btn)
        button_layout.addWidget(self.edit_btn)
        button_layout.addWidget(self.delete_btn)
        button_layout.addWidget(self.sale_btn)
        button_layout.addWidget(self.refresh_btn)
        button_layout.addStretch()

        main_layout.addLayout(button_layout)

        self.products_table = QTableWidget()
        self.setup_table()
        main_layout.addWidget(self.products_table)

        self.statusBar().showMessage("Sistema iniciado correctamente")

    def setup_table(self):
        """Configura la tabla de productos."""
        headers = ["ID", "Nombre", "Categoría", "ISBN", "Precio", "Proveedor", "Cantidad"]
        self.products_table.setColumnCount(len(headers))
        self.products_table.setHorizontalHeaderLabels(headers)
        self.products_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.products_table.setAlternatingRowColors(True)
        self.products_table.setSortingEnabled(True)
        self.products_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.products_table.setColumnHidden(0, True)

        header = self.products_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)

        vertical_header = self.products_table.verticalHeader()
        vertical_header.setSectionResizeMode(QHeaderView.Fixed)
        vertical_header.setDefaultSectionSize(30)
        vertical_header.setMinimumSectionSize(25)
        vertical_header.setMaximumSectionSize(40)

        self.products_table.selectionModel().selectionChanged.connect(self.on_selection_changed)

    def load_products(self, products=None):
        """Carga los productos en la tabla."""
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

        self.statusBar().showMessage(f"Total de productos: {len(products)}")

    def on_selection_changed(self):
        """Maneja el cambio de selección en la tabla."""
        has_selection = bool(self.products_table.selectionModel().selectedRows())
        self.edit_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)

    def get_selected_product(self):
        """Obtiene el producto seleccionado."""
        selected_rows = self.products_table.selectionModel().selectedRows()
        if selected_rows:
            row = selected_rows[0].row()
            product_id = self.products_table.item(row, 0).text()
            return self.product_manager.get_product_by_id(product_id)
        return None

    def add_product(self):
        """Abre el diálogo para añadir un nuevo producto."""
        categories = self.product_manager.get_categories()
        dialog = ProductFormDialog(self, categories=categories)

        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_form_data()
            try:
                self.product_manager.add_product(**data)
                self.refresh_products()
                QMessageBox.information(self, "Éxito", "Producto añadido correctamente.")
            except Exception as error:
                QMessageBox.critical(self, "Error", f"Error al añadir producto: {error}")

    def edit_product(self):
        """Abre el diálogo para editar el producto seleccionado."""
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
            except Exception as error:
                QMessageBox.critical(self, "Error", f"Error al actualizar producto: {error}")

    def delete_product(self):
        """Elimina el producto seleccionado."""
        product = self.get_selected_product()
        if not product:
            return

        reply = QMessageBox.question(
            self,
            "Confirmar eliminación",
            f"¿Está seguro de que desea eliminar el producto '{product.name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            try:
                self.product_manager.delete_product(product.id)
                self.refresh_products()
                QMessageBox.information(self, "Éxito", "Producto eliminado correctamente.")
            except Exception as error:
                QMessageBox.critical(self, "Error", f"Error al eliminar producto: {error}")

    def register_sale(self):
        """Abre el flujo de registro de ventas del Sprint 2."""
        self.product_manager.load_products()
        available_products = self.product_manager.get_all_products()

        if not any(product.quantity > 0 for product in available_products):
            QMessageBox.warning(
                self,
                "Sin stock",
                "No hay productos disponibles para registrar una venta.",
            )
            return

        dialog = SalesDialog(available_products, self)
        if dialog.exec() != QDialog.Accepted:
            return

        sale_data = dialog.get_sale_data()

        try:
            sale = self.sale_manager.create_sale(
                sale_data["items"],
                sale_data["payment_method"],
                sale_data.get("received_amount", 0.0),
            )
            self.refresh_products()
            total_with_iva = sale.total + round(sale.total * IVA_RATE)
            self.statusBar().showMessage(
                f"Venta registrada correctamente - Total: ${total_with_iva:,.0f} COP"
            )
            ReceiptDialog(sale, self).exec()
        except Exception as error:
            QMessageBox.critical(self, "Error", f"No se pudo registrar la venta: {error}")

    def refresh_products(self):
        """Actualiza la lista de productos."""
        self.product_manager.load_products()
        if self.search_edit.text():
            self.search_products()
        else:
            self.load_products()

    def search_products(self):
        """Realiza la búsqueda de productos."""
        query = self.search_edit.text().strip()
        if not query:
            self.load_products()
            return

        search_type_map = {
            "Nombre": "name",
            "Categoría": "category",
            "Todos": "all",
        }

        search_type = search_type_map.get(self.search_type_combo.currentText(), "all")
        results = self.product_manager.search_products(query, search_type)
        self.load_products(results)

    def clear_search(self):
        """Limpia la búsqueda."""
        self.search_edit.clear()
        self.search_type_combo.setCurrentText("Todos")
        self.load_products()


def main():
    """Función principal."""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
