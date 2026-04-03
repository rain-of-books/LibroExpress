"""
Aplicación principal del sistema LibroExpress - Sprint 3.
Sistema de gestión de inventario, ventas, clientes y proveedores con PySide6.
"""

import re
import sys
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QDate, QRegularExpression, Qt, QTimer
from PySide6.QtGui import QFont, QRegularExpressionValidator
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from clients import ClientManager
from products import ProductManager
from reports import (
    build_sales_report_rows,
    export_sales_report_csv,
    export_sales_report_excel,
    export_sales_report_pdf,
    summarize_sales_rows,
)
from restock import RestockOrderManager, generate_restock_order_text
from sales import IVA_RATE, SaleManager, generate_receipt_text
from suppliers import SupplierManager


def is_valid_email(email: str) -> bool:
    """Valida un correo con una expresión regular simple."""
    return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email.strip()))


class ClientFormDialog(QDialog):
    """Formulario para registrar clientes."""

    def __init__(self, client_manager, parent=None, document: str = ""):
        super().__init__(parent)
        self.client_manager = client_manager

        self.setWindowTitle("Registrar Cliente")
        self.setModal(True)
        self.resize(420, 260)

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.name_edit = QLineEdit()
        self.document_edit = QLineEdit()
        self.document_edit.setText(document)
        self.email_edit = QLineEdit()
        self.phone_edit = QLineEdit()

        self.document_edit.setPlaceholderText("Ingrese número de cédula")
        self.email_edit.setPlaceholderText("cliente@correo.com")
        self.phone_edit.setPlaceholderText("Ingrese teléfono")

        form_layout.addRow("Nombre:", self.name_edit)
        form_layout.addRow("Documento:", self.document_edit)
        form_layout.addRow("Correo:", self.email_edit)
        form_layout.addRow("Teléfono:", self.phone_edit)
        layout.addLayout(form_layout)

        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.button(QDialogButtonBox.Save).setText("Guardar")
        button_box.button(QDialogButtonBox.Cancel).setText("Cancelar")
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_form_data(self):
        """Retorna los datos del cliente."""
        return {
            "name": self.name_edit.text().strip(),
            "document": self.document_edit.text().strip(),
            "email": self.email_edit.text().strip(),
            "phone": self.phone_edit.text().strip(),
        }

    def accept(self):
        """Valida y registra el cliente."""
        data = self.get_form_data()

        if not all(data.values()):
            QMessageBox.warning(self, "Error", "Todos los campos del cliente son obligatorios.")
            return

        if not is_valid_email(data["email"]):
            QMessageBox.warning(self, "Error", "El correo del cliente no tiene un formato válido.")
            return

        if self.client_manager.get_client_by_document(data["document"]):
            QMessageBox.warning(self, "Error", "Ya existe un cliente con esa cédula.")
            return

        try:
            self.client_manager.add_client(**data)
        except Exception as error:
            QMessageBox.critical(self, "Error", f"No se pudo registrar el cliente: {error}")
            return

        QMessageBox.information(self, "Éxito", "Cliente registrado correctamente.")
        super().accept()


class SupplierFormDialog(QDialog):
    """Formulario para crear o editar proveedores."""

    def __init__(self, supplier_manager, parent=None, supplier=None):
        super().__init__(parent)
        self.supplier_manager = supplier_manager
        self.supplier = supplier

        self.setWindowTitle("Editar Proveedor" if supplier else "Registrar Proveedor")
        self.setModal(True)
        self.resize(420, 280)

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.name_edit = QLineEdit()
        self.phone_edit = QLineEdit()
        self.email_edit = QLineEdit()
        self.address_edit = QLineEdit()

        self.name_edit.setPlaceholderText("Ejemplo: Distribuidora Central")
        self.phone_edit.setPlaceholderText("Ejemplo: 3001234567")
        self.phone_edit.setValidator(QRegularExpressionValidator(QRegularExpression(r"\d+"), self))
        self.email_edit.setPlaceholderText("Ejemplo: contacto@proveedor.com")
        self.address_edit.setPlaceholderText("Ejemplo: Calle 10 # 25-30, Bogotá")

        form_layout.addRow("Nombre del proveedor:", self.name_edit)
        form_layout.addRow("Teléfono:", self.phone_edit)
        form_layout.addRow("Correo:", self.email_edit)
        form_layout.addRow("Dirección:", self.address_edit)
        layout.addLayout(form_layout)

        if supplier:
            self.name_edit.setText(supplier.name)
            self.phone_edit.setText(supplier.phone)
            self.email_edit.setText(supplier.email)
            self.address_edit.setText(supplier.address)

        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.button(QDialogButtonBox.Save).setText("Guardar")
        button_box.button(QDialogButtonBox.Cancel).setText("Cancelar")
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_form_data(self):
        """Retorna la información del proveedor."""
        return {
            "name": self.name_edit.text().strip(),
            "phone": self.phone_edit.text().strip(),
            "email": self.email_edit.text().strip(),
            "address": self.address_edit.text().strip(),
        }

    def accept(self):
        """Valida los datos del proveedor."""
        data = self.get_form_data()

        if not data["name"] or not data["phone"] or not data["email"]:
            QMessageBox.warning(self, "Error", "Nombre, teléfono y correo son obligatorios.")
            return

        if not data["phone"].isdigit():
            QMessageBox.warning(self, "Error", "El teléfono del proveedor debe contener solo números.")
            return

        if not is_valid_email(data["email"]):
            QMessageBox.warning(self, "Error", "El correo del proveedor no es válido.")
            return

        super().accept()


class SupplierManagementDialog(QDialog):
    """Pantalla CRUD para proveedores."""

    def __init__(self, supplier_manager, parent=None):
        super().__init__(parent)
        self.supplier_manager = supplier_manager

        self.setWindowTitle("Gestión de Proveedores")
        self.setModal(True)
        self.resize(760, 500)

        self.setup_ui()
        self.load_suppliers()

    def setup_ui(self):
        """Construye la interfaz de proveedores."""
        layout = QVBoxLayout(self)

        button_layout = QHBoxLayout()
        self.add_btn = QPushButton("Nuevo Proveedor")
        self.edit_btn = QPushButton("Editar")
        self.delete_btn = QPushButton("Eliminar")
        self.edit_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)

        self.add_btn.clicked.connect(self.add_supplier)
        self.edit_btn.clicked.connect(self.edit_supplier)
        self.delete_btn.clicked.connect(self.delete_supplier)

        button_layout.addWidget(self.add_btn)
        button_layout.addWidget(self.edit_btn)
        button_layout.addWidget(self.delete_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        self.suppliers_table = QTableWidget()
        self.suppliers_table.setColumnCount(5)
        self.suppliers_table.setHorizontalHeaderLabels(["ID", "Nombre", "Teléfono", "Correo", "Dirección"])
        self.suppliers_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.suppliers_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.suppliers_table.setAlternatingRowColors(True)
        self.suppliers_table.setColumnHidden(0, True)

        header = self.suppliers_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        self.suppliers_table.selectionModel().selectionChanged.connect(self.on_selection_changed)
        layout.addWidget(self.suppliers_table)

    def load_suppliers(self):
        """Carga los proveedores en la tabla."""
        suppliers = self.supplier_manager.get_all_suppliers()
        self.suppliers_table.setRowCount(len(suppliers))

        for row, supplier in enumerate(suppliers):
            self.suppliers_table.setItem(row, 0, QTableWidgetItem(supplier.id))
            self.suppliers_table.setItem(row, 1, QTableWidgetItem(supplier.name))
            self.suppliers_table.setItem(row, 2, QTableWidgetItem(supplier.phone))
            self.suppliers_table.setItem(row, 3, QTableWidgetItem(supplier.email))
            self.suppliers_table.setItem(row, 4, QTableWidgetItem(supplier.address))

    def on_selection_changed(self):
        has_selection = bool(self.suppliers_table.selectionModel().selectedRows())
        self.edit_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)

    def get_selected_supplier(self):
        selected_rows = self.suppliers_table.selectionModel().selectedRows()
        if not selected_rows:
            return None
        supplier_id = self.suppliers_table.item(selected_rows[0].row(), 0).text()
        return self.supplier_manager.get_supplier_by_id(supplier_id)

    def add_supplier(self):
        dialog = SupplierFormDialog(self.supplier_manager, self)
        if dialog.exec() == QDialog.Accepted:
            try:
                self.supplier_manager.add_supplier(**dialog.get_form_data())
                self.load_suppliers()
                QMessageBox.information(self, "Éxito", "Proveedor registrado correctamente.")
            except Exception as error:
                QMessageBox.critical(self, "Error", f"No se pudo registrar el proveedor: {error}")

    def edit_supplier(self):
        supplier = self.get_selected_supplier()
        if not supplier:
            return

        dialog = SupplierFormDialog(self.supplier_manager, self, supplier=supplier)
        if dialog.exec() == QDialog.Accepted:
            try:
                self.supplier_manager.update_supplier(supplier.id, **dialog.get_form_data())
                self.load_suppliers()
                QMessageBox.information(self, "Éxito", "Proveedor actualizado correctamente.")
            except Exception as error:
                QMessageBox.critical(self, "Error", f"No se pudo actualizar el proveedor: {error}")

    def delete_supplier(self):
        supplier = self.get_selected_supplier()
        if not supplier:
            return

        reply = QMessageBox.question(
            self,
            "Confirmar eliminación",
            f"¿Desea eliminar el proveedor '{supplier.name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.supplier_manager.delete_supplier(supplier.id)
            self.load_suppliers()
            QMessageBox.information(self, "Éxito", "Proveedor eliminado correctamente.")


class ProductFormDialog(QDialog):
    """Diálogo para añadir o editar productos."""

    def __init__(self, parent=None, product=None, categories=None, supplier_names=None):
        super().__init__(parent)
        self.product = product
        self.categories = categories or []
        self.supplier_names = supplier_names or []

        title = "Editar Producto" if product else "Nuevo Producto"
        self.setWindowTitle(title)
        self.setModal(True)
        self.resize(400, 360)

        self.setup_ui()
        if product:
            self.populate_fields()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Ingrese el nombre del producto")

        self.category_combo = QComboBox()
        self.category_combo.setEditable(True)
        self.category_combo.addItem("")
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
        self.isbn_edit.setValidator(QRegularExpressionValidator(isbn_regex))

        self.supplier_combo = QComboBox()
        self.supplier_combo.setEditable(True)
        self.supplier_combo.addItem("")
        self.supplier_combo.addItems(self.supplier_names)

        form_layout.addRow("Nombre del producto:", self.name_edit)
        form_layout.addRow("Categoría:", self.category_combo)
        form_layout.addRow("Precio (Mínimo $5,000):", self.price_spinbox)
        form_layout.addRow("Cantidad disponible:", self.quantity_spinbox)
        form_layout.addRow("Código ISBN:", self.isbn_edit)
        form_layout.addRow("Proveedor:", self.supplier_combo)
        layout.addLayout(form_layout)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def populate_fields(self):
        if self.product:
            self.name_edit.setText(self.product.name)
            self.category_combo.setCurrentText(self.product.category)
            self.price_spinbox.setValue(self.product.price)
            self.quantity_spinbox.setValue(self.product.quantity)
            self.isbn_edit.setText(self.product.isbn)
            self.supplier_combo.setCurrentText(self.product.supplier)

    def get_form_data(self):
        return {
            "name": self.name_edit.text().strip(),
            "category": self.category_combo.currentText().strip(),
            "price": self.price_spinbox.value(),
            "quantity": self.quantity_spinbox.value(),
            "isbn": self.isbn_edit.text().strip(),
            "supplier": self.supplier_combo.currentText().strip(),
        }

    def process_price_input(self):
        if int(self.price_spinbox.value()) < 5000:
            self.price_spinbox.setValue(5000)

    def accept(self):
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
    """Diálogo para registrar una nueva venta vinculada a un cliente."""

    def __init__(self, products, client_manager, parent=None):
        super().__init__(parent)
        self.products = [product for product in products if product.quantity > 0]
        self.client_manager = client_manager
        self.selected_items = {}
        self.selected_client = None

        self.setWindowTitle("Registrar Venta")
        self.setModal(True)
        self.resize(820, 620)

        self.setup_ui()
        self.load_available_products()
        self.on_payment_method_changed(self.payment_combo.currentText())
        self.update_total()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        title_label = QLabel("Registro de ventas")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        client_group = QGroupBox("Cliente")
        client_layout = QVBoxLayout(client_group)
        client_search_layout = QHBoxLayout()

        client_search_layout.addWidget(QLabel("Cédula:"))
        self.client_document_edit = QLineEdit()
        self.client_document_edit.setPlaceholderText("Ingrese número de cédula del cliente")
        client_search_layout.addWidget(self.client_document_edit)

        self.search_client_btn = QPushButton("Buscar Cliente")
        self.search_client_btn.clicked.connect(self.search_client)
        client_search_layout.addWidget(self.search_client_btn)

        self.new_client_btn = QPushButton("Registrar Cliente")
        self.new_client_btn.clicked.connect(self.register_client)
        client_search_layout.addWidget(self.new_client_btn)

        client_layout.addLayout(client_search_layout)
        self.client_status_label = QLabel("Cliente no seleccionado.")
        client_layout.addWidget(self.client_status_label)
        layout.addWidget(client_group)

        selector_group = QGroupBox("Selección de productos")
        selector_vlayout = QVBoxLayout(selector_group)

        search_row = QHBoxLayout()
        search_row.addWidget(QLabel("Buscar por nombre:"))
        self.product_search_edit = QLineEdit()
        self.product_search_edit.setPlaceholderText("Escriba el nombre del producto para filtrar...")
        self.product_search_edit.textChanged.connect(self.filter_products)
        search_row.addWidget(self.product_search_edit, 1)
        self.clear_search_btn = QPushButton("Limpiar")
        self.clear_search_btn.clicked.connect(lambda: self.product_search_edit.clear())
        search_row.addWidget(self.clear_search_btn)
        selector_vlayout.addLayout(search_row)

        selector_layout = QHBoxLayout()
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
        selector_vlayout.addLayout(selector_layout)
        layout.addWidget(selector_group)

        self.items_table = QTableWidget()
        self.items_table.setColumnCount(5)
        self.items_table.setHorizontalHeaderLabels(["ID", "Producto", "Cantidad", "Precio unitario", "Subtotal"])
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
        self.payment_combo.currentTextChanged.connect(self.on_payment_method_changed)
        summary_layout.addRow("Método de pago:", self.payment_combo)

        self.received_label = QLabel("Monto recibido:")
        self.received_spinbox = QDoubleSpinBox()
        self.received_spinbox.setRange(0, 999999999)
        self.received_spinbox.setDecimals(0)
        self.received_spinbox.setSuffix(" COP")
        self.received_spinbox.setSingleStep(1000)
        summary_layout.addRow(self.received_label, self.received_spinbox)

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

    def search_client(self):
        document = self.client_document_edit.text().strip()
        if not document:
            QMessageBox.warning(self, "Error", "Ingrese la cédula del cliente.")
            return

        client = self.client_manager.get_client_by_document(document)
        if client:
            self.selected_client = client
            self.client_status_label.setText(f"Cliente seleccionado: {client.name} | Correo: {client.email}")
        else:
            self.selected_client = None
            self.client_status_label.setText("Cliente no encontrado. Regístrelo para continuar.")
            QMessageBox.information(self, "Cliente no encontrado", "No existe un cliente con esa cédula. Regístrelo para continuar.")

    def register_client(self):
        dialog = ClientFormDialog(self.client_manager, self, document=self.client_document_edit.text().strip())
        if dialog.exec() == QDialog.Accepted:
            document = dialog.get_form_data()["document"]
            client = self.client_manager.get_client_by_document(document)
            if client:
                self.selected_client = client
                self.client_document_edit.setText(client.document)
                self.client_status_label.setText(f"Cliente seleccionado: {client.name} | Correo: {client.email}")

    def load_available_products(self):
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

    def filter_products(self, text: str):
        self.product_combo.clear()
        filtered = (
            [p for p in self.products if text.strip().lower() in p.name.lower()]
            if text.strip()
            else self.products
        )
        for product in filtered:
            label = f"{product.name} | Stock: {product.quantity} | ${product.price:,.0f} COP"
            self.product_combo.addItem(label, product.id)
        has_products = self.product_combo.count() > 0
        self.add_item_btn.setEnabled(has_products)
        self.product_combo.setEnabled(has_products)
        self.quantity_spinbox.setEnabled(has_products)
        if not has_products:
            self.product_combo.addItem("Sin resultados", "")

    def get_product_by_id(self, product_id):
        for product in self.products:
            if product.id == product_id:
                return product
        return None

    def add_sale_item(self):
        product_id = self.product_combo.currentData()
        product = self.get_product_by_id(product_id)
        quantity = self.quantity_spinbox.value()
        if not product:
            QMessageBox.warning(self, "Error", "Seleccione un producto válido.")
            return

        current_quantity = self.selected_items.get(product_id, {}).get("quantity", 0)
        new_quantity = current_quantity + quantity
        if new_quantity > product.quantity:
            QMessageBox.warning(self, "Stock insuficiente", f"No puede vender más de {product.quantity} unidades de '{product.name}'.")
            return

        self.selected_items[product_id] = {"product": product, "quantity": new_quantity}
        self.refresh_items_table()

    def remove_selected_item(self):
        selected_rows = self.items_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Error", "Seleccione un producto de la venta.")
            return
        row = selected_rows[0].row()
        product_id = self.items_table.item(row, 0).text()
        self.selected_items.pop(product_id, None)
        self.refresh_items_table()

    def refresh_items_table(self):
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
        return sum(item["product"].price * item["quantity"] for item in self.selected_items.values())

    def _get_total_with_iva(self) -> float:
        net = self._get_net_total()
        iva = round(net * IVA_RATE)
        return net + iva

    def update_total(self):
        net = self._get_net_total()
        iva = round(net * IVA_RATE)
        total_with_iva = net + iva
        self.total_label.setText(f"${total_with_iva:,.0f} COP  (IVA 19%: ${iva:,.0f} COP)")

    def on_payment_method_changed(self, method: str):
        is_cash = method == "Efectivo"
        self.received_label.setVisible(is_cash)
        self.received_spinbox.setVisible(is_cash)
        if not is_cash:
            self.received_spinbox.setValue(0)

    def get_sale_data(self):
        items = []
        for product_id, item in self.selected_items.items():
            items.append({"product_id": product_id, "quantity": item["quantity"]})
        return {
            "items": items,
            "payment_method": self.payment_combo.currentText(),
            "received_amount": self.received_spinbox.value(),
            "client_document": self.selected_client.document if self.selected_client else "",
            "client_name": self.selected_client.name if self.selected_client else "",
        }

    def accept(self):
        if not self.selected_client:
            QMessageBox.warning(self, "Error", "Debe buscar o registrar un cliente antes de vender.")
            return
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
                    f"El monto recibido (${received:,.0f} COP) es menor al total a pagar con IVA (${total_with_iva:,.0f} COP).",
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
        self.resize(520, 620)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        title_label = QLabel("Comprobante de venta")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        info_label = QLabel(
            f"Venta: {self.sale.id}\n"
            f"Cliente: {self.sale.client_name or 'No especificado'}\n"
            f"Documento: {self.sale.client_document or 'No especificado'}\n"
            f"Fecha: {self.sale.created_at}\n"
            f"Método de pago: {self.sale.payment_method}"
        )
        layout.addWidget(info_label)

        receipt_text = QTextEdit()
        receipt_text.setReadOnly(True)
        receipt_text.setFont(QFont("Courier New", 10))
        receipt_text.setPlainText(generate_receipt_text(self.sale))
        layout.addWidget(receipt_text)

        actions_layout = QHBoxLayout()
        actions_layout.addStretch()
        print_button = QPushButton("Imprimir")
        print_button.clicked.connect(self.download_receipt)
        actions_layout.addWidget(print_button)
        close_button = QPushButton("Cerrar")
        close_button.clicked.connect(self.accept)
        actions_layout.addWidget(close_button)
        layout.addLayout(actions_layout)

    def download_receipt(self):
        """Permite guardar el recibo .txt en la ubicación elegida por el usuario."""
        default_name = f"{self.sale.id}_PRINT.txt"
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar recibo para impresión",
            default_name,
            "Text Files (*.txt)",
        )
        if not save_path:
            return

        source_path = Path(self.sale.receipt_file) if self.sale.receipt_file else None
        target_path = Path(save_path)

        if source_path and source_path.exists():
            target_path.write_text(source_path.read_text(encoding="utf-8"), encoding="utf-8")
        else:
            target_path.write_text(generate_receipt_text(self.sale), encoding="utf-8")

        QMessageBox.information(
            self,
            "Recibo descargado",
            f"El recibo quedó guardado en:\n{target_path.resolve()}",
        )


class PurchaseHistoryDialog(QDialog):
    """Consulta historial de compras por cédula."""

    def __init__(self, client_manager, sale_manager, parent=None):
        super().__init__(parent)
        self.client_manager = client_manager
        self.sale_manager = sale_manager

        self.setWindowTitle("Historial de Compras")
        self.setModal(True)
        self.resize(980, 560)

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Cédula:"))
        self.document_edit = QLineEdit()
        self.document_edit.setPlaceholderText("Ingrese cédula del cliente")
        search_layout.addWidget(self.document_edit)
        self.search_btn = QPushButton("Buscar")
        self.search_btn.clicked.connect(self.search_history)
        search_layout.addWidget(self.search_btn)
        layout.addLayout(search_layout)

        self.client_info_label = QLabel("Ingrese una cédula para consultar compras.")
        layout.addWidget(self.client_info_label)

        self.history_table = QTableWidget()
        self.history_table.setColumnCount(6)
        self.history_table.setHorizontalHeaderLabels(["ID Venta", "Fecha", "Productos", "Detalles", "Factura", "Total con IVA"])
        self.history_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.history_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.history_table.setAlternatingRowColors(True)
        self.history_table.doubleClicked.connect(self.view_receipt)

        header = self.history_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        layout.addWidget(self.history_table)

        action_layout = QHBoxLayout()
        hint_label = QLabel("Doble clic en una fila para ver la factura")
        hint_label.setStyleSheet("color: gray; font-style: italic;")
        action_layout.addWidget(hint_label)
        action_layout.addStretch()
        self.view_receipt_btn = QPushButton("Ver Factura")
        self.view_receipt_btn.setEnabled(False)
        self.view_receipt_btn.clicked.connect(self.view_receipt)
        action_layout.addWidget(self.view_receipt_btn)
        layout.addLayout(action_layout)

        self.history_table.selectionModel().selectionChanged.connect(self.on_selection_changed)

    def search_history(self):
        document = self.document_edit.text().strip()
        if not document:
            QMessageBox.warning(self, "Error", "Ingrese la cédula del cliente.")
            return

        client = self.client_manager.get_client_by_document(document)
        if not client:
            self.client_info_label.setText("Cliente no encontrado")
            self.history_table.setRowCount(0)
            self.view_receipt_btn.setEnabled(False)
            QMessageBox.information(self, "Cliente no encontrado", "Cliente no encontrado")
            return

        sales = self.sale_manager.get_sales_by_client_document(document)
        self.client_info_label.setText(f"Historial de {client.name} | Compras registradas: {len(sales)}")
        self.history_table.setRowCount(len(sales))

        for row, sale in enumerate(sales):
            products_text = ", ".join(item.product_name for item in sale.items)
            details_text = " | ".join(
                f"{item.product_name} x{item.quantity} (${item.subtotal:,.0f})"
                for item in sale.items
            )
            total_with_iva = sale.total + round(sale.total * IVA_RATE)
            receipt_name = Path(sale.receipt_file).name if sale.receipt_file else "Sin archivo"
            self.history_table.setItem(row, 0, QTableWidgetItem(sale.id))
            self.history_table.setItem(row, 1, QTableWidgetItem(sale.created_at.split("T")[0]))
            self.history_table.setItem(row, 2, QTableWidgetItem(products_text))
            self.history_table.setItem(row, 3, QTableWidgetItem(details_text))
            self.history_table.setItem(row, 4, QTableWidgetItem(receipt_name))
            self.history_table.setItem(row, 5, QTableWidgetItem(f"${total_with_iva:,.0f} COP"))

    def on_selection_changed(self):
        self.view_receipt_btn.setEnabled(bool(self.history_table.selectionModel().selectedRows()))

    def view_receipt(self):
        selected_rows = self.history_table.selectionModel().selectedRows()
        if not selected_rows:
            return
        sale_id = self.history_table.item(selected_rows[0].row(), 0).text()
        sale = next((item for item in self.sale_manager.get_all_sales() if item.id == sale_id), None)
        if sale:
            ReceiptDialog(sale, self).exec()


class RestockOrderDialog(QDialog):
    """Módulo de reabastecimiento para crear y descargar órdenes."""

    def __init__(self, product_manager, supplier_manager, restock_manager, parent=None):
        super().__init__(parent)
        self.product_manager = product_manager
        self.supplier_manager = supplier_manager
        self.restock_manager = restock_manager
        self.selected_items = {}

        self.setWindowTitle("Órdenes de Reabastecimiento")
        self.setModal(True)
        self.resize(980, 680)

        self.setup_ui()
        self.load_suppliers()
        self.load_products()
        self.load_orders()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        title_label = QLabel("Generación de órdenes de reabastecimiento")
        title_font = QFont()
        title_font.setPointSize(13)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        supplier_group = QGroupBox("Proveedor y productos")
        supplier_layout = QVBoxLayout(supplier_group)

        supplier_row = QHBoxLayout()
        supplier_row.addWidget(QLabel("Proveedor:"))
        self.supplier_combo = QComboBox()
        self.supplier_combo.currentIndexChanged.connect(self.on_supplier_changed)
        supplier_row.addWidget(self.supplier_combo, 1)
        supplier_layout.addLayout(supplier_row)

        product_row = QHBoxLayout()
        product_row.addWidget(QLabel("Producto:"))
        self.product_combo = QComboBox()
        product_row.addWidget(self.product_combo, 1)
        product_row.addWidget(QLabel("Cantidad:"))
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setRange(1, 99999)
        product_row.addWidget(self.quantity_spin)
        self.add_item_btn = QPushButton("Agregar producto")
        self.add_item_btn.clicked.connect(self.add_item)
        product_row.addWidget(self.add_item_btn)
        supplier_layout.addLayout(product_row)

        self.items_table = QTableWidget()
        self.items_table.setColumnCount(5)
        self.items_table.setHorizontalHeaderLabels(["ID", "Producto", "Cantidad", "Precio", "Subtotal"])
        self.items_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.items_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.items_table.setAlternatingRowColors(True)
        self.items_table.setColumnHidden(0, True)
        header = self.items_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        supplier_layout.addWidget(self.items_table)

        notes_row = QHBoxLayout()
        notes_row.addWidget(QLabel("Notas:"))
        self.notes_edit = QLineEdit()
        self.notes_edit.setPlaceholderText("Observaciones para el proveedor (opcional)")
        notes_row.addWidget(self.notes_edit)
        self.remove_item_btn = QPushButton("Quitar seleccionado")
        self.remove_item_btn.clicked.connect(self.remove_item)
        notes_row.addWidget(self.remove_item_btn)
        supplier_layout.addLayout(notes_row)

        action_row = QHBoxLayout()
        action_row.addStretch()
        self.create_order_btn = QPushButton("Crear orden")
        self.create_order_btn.clicked.connect(self.create_order)
        action_row.addWidget(self.create_order_btn)
        supplier_layout.addLayout(action_row)
        layout.addWidget(supplier_group)

        orders_group = QGroupBox("Órdenes guardadas")
        orders_layout = QVBoxLayout(orders_group)

        self.orders_table = QTableWidget()
        self.orders_table.setColumnCount(5)
        self.orders_table.setHorizontalHeaderLabels(["ID", "Fecha", "Proveedor", "Total", "Archivo"])
        self.orders_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.orders_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.orders_table.setAlternatingRowColors(True)
        orders_header = self.orders_table.horizontalHeader()
        orders_header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        orders_header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        orders_header.setSectionResizeMode(2, QHeaderView.Stretch)
        orders_header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        orders_header.setSectionResizeMode(4, QHeaderView.Stretch)
        orders_layout.addWidget(self.orders_table)

        order_actions = QHBoxLayout()
        self.preview_btn = QPushButton("Visualizar orden")
        self.preview_btn.clicked.connect(self.preview_order)
        self.download_btn = QPushButton("Descargar orden")
        self.download_btn.clicked.connect(self.download_order)
        self.delete_order_btn = QPushButton("Eliminar orden")
        self.delete_order_btn.clicked.connect(self.delete_order)
        order_actions.addStretch()
        order_actions.addWidget(self.preview_btn)
        order_actions.addWidget(self.download_btn)
        order_actions.addWidget(self.delete_order_btn)
        orders_layout.addLayout(order_actions)

        layout.addWidget(orders_group)

    def load_suppliers(self):
        self.supplier_combo.clear()
        suppliers = self.supplier_manager.get_all_suppliers()
        for supplier in suppliers:
            self.supplier_combo.addItem(supplier.name, supplier.id)

    def load_products(self):
        self.product_combo.clear()
        supplier_id = self.supplier_combo.currentData()
        supplier = self.supplier_manager.get_supplier_by_id(supplier_id) if supplier_id else None
        supplier_name = supplier.name.strip() if supplier else ""
        products = self.product_manager.get_all_products()
        for product in products:
            if supplier_name and product.supplier.strip().lower() != supplier_name.lower():
                continue
            label = f"{product.name} | Stock actual: {product.quantity} | ${product.price:,.0f}"
            self.product_combo.addItem(label, product.id)

        has_products = self.product_combo.count() > 0
        self.add_item_btn.setEnabled(has_products)
        self.product_combo.setEnabled(has_products)
        self.quantity_spin.setEnabled(has_products)
        if not has_products:
            self.product_combo.addItem("No hay productos asociados a este proveedor", "")

    def on_supplier_changed(self):
        self.selected_items = {}
        self.refresh_selected_items_table()
        self.load_products()

    def add_item(self):
        product_id = self.product_combo.currentData()
        product = self.product_manager.get_product_by_id(product_id)
        if not product:
            QMessageBox.warning(self, "Error", "Seleccione un producto válido.")
            return

        quantity = self.quantity_spin.value()
        current_quantity = self.selected_items.get(product_id, {}).get("quantity", 0)
        self.selected_items[product_id] = {
            "product": product,
            "quantity": current_quantity + quantity,
        }
        self.refresh_selected_items_table()

    def remove_item(self):
        selected_rows = self.items_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Error", "Seleccione una fila para quitar.")
            return

        row = selected_rows[0].row()
        product_id = self.items_table.item(row, 0).text()
        self.selected_items.pop(product_id, None)
        self.refresh_selected_items_table()

    def refresh_selected_items_table(self):
        items = list(self.selected_items.values())
        self.items_table.setRowCount(len(items))
        for row, item in enumerate(items):
            product = item["product"]
            quantity = item["quantity"]
            subtotal = product.price * quantity
            self.items_table.setItem(row, 0, QTableWidgetItem(product.id))
            self.items_table.setItem(row, 1, QTableWidgetItem(product.name))
            self.items_table.setItem(row, 2, QTableWidgetItem(str(quantity)))
            self.items_table.setItem(row, 3, QTableWidgetItem(f"${product.price:,.0f}"))
            self.items_table.setItem(row, 4, QTableWidgetItem(f"${subtotal:,.0f}"))

    def create_order(self):
        supplier_id = self.supplier_combo.currentData()
        if not supplier_id:
            QMessageBox.warning(self, "Error", "Debe seleccionar un proveedor.")
            return

        if not self.selected_items:
            QMessageBox.warning(self, "Error", "Debe agregar al menos un producto a la orden.")
            return

        items_data = [
            {"product_id": product_id, "quantity": item["quantity"]}
            for product_id, item in self.selected_items.items()
        ]

        try:
            order = self.restock_manager.create_order(
                supplier_id=supplier_id,
                items_data=items_data,
                notes=self.notes_edit.text().strip(),
            )
        except Exception as error:
            QMessageBox.critical(self, "Error", f"No se pudo crear la orden: {error}")
            return

        QMessageBox.information(
            self,
            "Orden creada",
            f"Orden {order.id} creada y guardada correctamente.",
        )
        self.selected_items = {}
        self.notes_edit.clear()
        self.refresh_selected_items_table()
        self.load_orders()

    def load_orders(self):
        orders = self.restock_manager.get_all_orders()
        self.orders_table.setRowCount(len(orders))
        for row, order in enumerate(orders):
            date_text = order.created_at.split("T")[0] if "T" in order.created_at else order.created_at
            self.orders_table.setItem(row, 0, QTableWidgetItem(order.id))
            self.orders_table.setItem(row, 1, QTableWidgetItem(date_text))
            self.orders_table.setItem(row, 2, QTableWidgetItem(order.supplier_name))
            self.orders_table.setItem(row, 3, QTableWidgetItem(f"${order.total:,.0f}"))
            self.orders_table.setItem(row, 4, QTableWidgetItem(Path(order.file_path).name if order.file_path else "Sin archivo"))

    def get_selected_order(self):
        selected_rows = self.orders_table.selectionModel().selectedRows()
        if not selected_rows:
            return None
        order_id = self.orders_table.item(selected_rows[0].row(), 0).text()
        return self.restock_manager.get_order_by_id(order_id)

    def preview_order(self):
        order = self.get_selected_order()
        if not order:
            QMessageBox.warning(self, "Error", "Seleccione una orden para visualizar.")
            return

        preview = QDialog(self)
        preview.setWindowTitle(f"Vista previa - {order.id}")
        preview.setModal(True)
        preview.resize(640, 520)
        preview_layout = QVBoxLayout(preview)

        text = QPlainTextEdit()
        text.setReadOnly(True)
        text.setPlainText(generate_restock_order_text(order))
        preview_layout.addWidget(text)

        close_btn = QPushButton("Cerrar")
        close_btn.clicked.connect(preview.accept)
        preview_layout.addWidget(close_btn, alignment=Qt.AlignRight)
        preview.exec()

    def download_order(self):
        order = self.get_selected_order()
        if not order:
            QMessageBox.warning(self, "Error", "Seleccione una orden para descargar.")
            return

        if not order.file_path or not Path(order.file_path).exists():
            QMessageBox.warning(self, "Error", "El archivo de la orden no está disponible.")
            return

        default_name = Path(order.file_path).name
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar orden de reabastecimiento",
            default_name,
            "PDF Files (*.pdf)",
        )
        if not save_path:
            return

        Path(save_path).write_bytes(Path(order.file_path).read_bytes())
        QMessageBox.information(self, "Descarga completa", "La orden fue descargada correctamente.")

    def delete_order(self):
        order = self.get_selected_order()
        if not order:
            QMessageBox.warning(self, "Error", "Seleccione una orden para eliminar.")
            return

        reply = QMessageBox.question(
            self,
            "Confirmar eliminación",
            f"¿Desea eliminar la orden {order.id}? Esta acción no se puede deshacer.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        if not self.restock_manager.delete_order(order.id):
            QMessageBox.warning(self, "Error", "No se pudo eliminar la orden seleccionada.")
            return

        self.load_orders()
        QMessageBox.information(self, "Orden eliminada", "La orden fue eliminada correctamente.")


class SalesReportDialog(QDialog):
    """Módulo de reportes de ventas por rango de fechas y exportación."""

    def __init__(self, sale_manager, parent=None):
        super().__init__(parent)
        self.sale_manager = sale_manager
        self.current_rows = []

        self.setWindowTitle("Reportes de Ventas")
        self.setModal(True)
        self.resize(1100, 680)

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        title_label = QLabel("Reporte de ventas por rango de fechas")
        title_font = QFont()
        title_font.setPointSize(13)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        filters_layout = QHBoxLayout()
        filters_layout.addWidget(QLabel("Desde:"))
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate.currentDate().addDays(-30))
        filters_layout.addWidget(self.start_date_edit)

        filters_layout.addWidget(QLabel("Hasta:"))
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate.currentDate())
        filters_layout.addWidget(self.end_date_edit)

        self.generate_btn = QPushButton("Generar reporte")
        self.generate_btn.clicked.connect(self.generate_report)
        filters_layout.addWidget(self.generate_btn)
        filters_layout.addStretch()
        layout.addLayout(filters_layout)

        self.report_table = QTableWidget()
        self.report_table.setColumnCount(11)
        self.report_table.setHorizontalHeaderLabels(
            [
                "ID Venta",
                "Fecha",
                "Cliente",
                "Documento",
                "Producto",
                "Cantidad",
                "Precio unitario",
                "Subtotal",
                "IVA",
                "Total con IVA",
                "Pago",
            ]
        )
        self.report_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.report_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.report_table.setAlternatingRowColors(True)
        header = self.report_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(8, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(9, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(10, QHeaderView.ResizeToContents)
        layout.addWidget(self.report_table)

        self.summary_label = QLabel("Genere el reporte para visualizar resultados.")
        layout.addWidget(self.summary_label)

        export_layout = QHBoxLayout()
        export_layout.addStretch()
        self.export_csv_btn = QPushButton("Exportar CSV")
        self.export_excel_btn = QPushButton("Exportar Excel")
        self.export_pdf_btn = QPushButton("Exportar PDF")
        self.export_csv_btn.setEnabled(False)
        self.export_excel_btn.setEnabled(False)
        self.export_pdf_btn.setEnabled(False)
        self.export_csv_btn.clicked.connect(self.export_csv)
        self.export_excel_btn.clicked.connect(self.export_excel)
        self.export_pdf_btn.clicked.connect(self.export_pdf)
        export_layout.addWidget(self.export_csv_btn)
        export_layout.addWidget(self.export_excel_btn)
        export_layout.addWidget(self.export_pdf_btn)
        layout.addLayout(export_layout)

    def generate_report(self):
        start_date = self.start_date_edit.date().toPython()
        end_date = self.end_date_edit.date().toPython()
        if start_date > end_date:
            QMessageBox.warning(self, "Error", "La fecha inicial no puede ser mayor que la final.")
            return

        all_sales = self.sale_manager.get_all_sales()
        self.current_rows = build_sales_report_rows(all_sales, start_date, end_date)
        self.report_table.setRowCount(len(self.current_rows))

        for row_index, row in enumerate(self.current_rows):
            self.report_table.setItem(row_index, 0, QTableWidgetItem(row["sale_id"]))
            self.report_table.setItem(row_index, 1, QTableWidgetItem(row["date"]))
            self.report_table.setItem(row_index, 2, QTableWidgetItem(row["client"]))
            self.report_table.setItem(row_index, 3, QTableWidgetItem(row["document"]))
            self.report_table.setItem(row_index, 4, QTableWidgetItem(row["product"]))
            self.report_table.setItem(row_index, 5, QTableWidgetItem(str(row["quantity"])))
            self.report_table.setItem(row_index, 6, QTableWidgetItem(f"${row['unit_price']:,.0f}"))
            self.report_table.setItem(row_index, 7, QTableWidgetItem(f"${row['subtotal']:,.0f}"))
            self.report_table.setItem(row_index, 8, QTableWidgetItem(f"${row['iva']:,.0f}"))
            self.report_table.setItem(row_index, 9, QTableWidgetItem(f"${row['total_with_iva']:,.0f}"))
            self.report_table.setItem(row_index, 10, QTableWidgetItem(row["payment_method"]))

        if not self.current_rows:
            self.summary_label.setText("No se encontraron ventas en el rango seleccionado.")
            self.set_export_enabled(False)
            return

        summary = summarize_sales_rows(self.current_rows)
        self.summary_label.setText(
            " | ".join(
                [
                    f"Ventas: {summary['sales']}",
                    f"Líneas: {summary['lines']}",
                    f"Subtotal: ${summary['net_total']:,.0f}",
                    f"IVA: ${summary['iva_total']:,.0f}",
                    f"Total con IVA: ${summary['gross_total']:,.0f}",
                ]
            )
        )
        self.set_export_enabled(True)

    def set_export_enabled(self, enabled: bool):
        self.export_csv_btn.setEnabled(enabled)
        self.export_excel_btn.setEnabled(enabled)
        self.export_pdf_btn.setEnabled(enabled)

    def _get_period_label(self) -> str:
        return f"{self.start_date_edit.date().toString('yyyy-MM-dd')} a {self.end_date_edit.date().toString('yyyy-MM-dd')}"

    def export_csv(self):
        if not self.current_rows:
            return
        default_name = f"reporte_ventas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        file_path, _ = QFileDialog.getSaveFileName(self, "Exportar reporte CSV", default_name, "CSV (*.csv)")
        if not file_path:
            return
        export_sales_report_csv(self.current_rows, file_path)
        QMessageBox.information(self, "Exportación completa", "El reporte CSV fue generado correctamente.")

    def export_excel(self):
        if not self.current_rows:
            return
        default_name = f"reporte_ventas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        file_path, _ = QFileDialog.getSaveFileName(self, "Exportar reporte Excel", default_name, "Excel (*.xlsx)")
        if not file_path:
            return
        try:
            export_sales_report_excel(self.current_rows, file_path)
            QMessageBox.information(self, "Exportación completa", "El reporte Excel fue generado correctamente.")
        except Exception as error:
            QMessageBox.critical(self, "Error", f"No se pudo exportar a Excel: {error}")

    def export_pdf(self):
        if not self.current_rows:
            return
        default_name = f"reporte_ventas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        file_path, _ = QFileDialog.getSaveFileName(self, "Exportar reporte PDF", default_name, "PDF (*.pdf)")
        if not file_path:
            return
        try:
            export_sales_report_pdf(
                self.current_rows,
                file_path,
                title="LibroExpress - Reporte de Ventas",
                period_label=self._get_period_label(),
            )
            QMessageBox.information(self, "Exportación completa", "El reporte PDF fue generado correctamente.")
        except Exception as error:
            QMessageBox.critical(self, "Error", f"No se pudo exportar a PDF: {error}")


class MainWindow(QMainWindow):
    """Ventana principal del sistema LibroExpress."""

    def __init__(self):
        super().__init__()
        self.product_manager = ProductManager()
        self.client_manager = ClientManager()
        self.supplier_manager = SupplierManager()
        self.sale_manager = SaleManager(self.product_manager)
        self.restock_manager = RestockOrderManager(self.product_manager, self.supplier_manager)
        self.setup_ui()
        self.load_products()

        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.refresh_products)

    def setup_ui(self):
        self.setWindowTitle("LibroExpress - Sistema de Inventario, Ventas y Clientes")
        self.setMinimumSize(1120, 720)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        title_label = QLabel("Sistema de Gestión de Inventario, Ventas y Clientes - LibroExpress")
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
        self.history_btn = QPushButton("Historial Compras")
        self.history_btn.clicked.connect(self.show_purchase_history)
        self.supplier_btn = QPushButton("Proveedores")
        self.supplier_btn.clicked.connect(self.manage_suppliers)
        self.restock_btn = QPushButton("Reabastecimiento")
        self.restock_btn.clicked.connect(self.manage_restock)
        self.sales_report_btn = QPushButton("Reportes Ventas")
        self.sales_report_btn.clicked.connect(self.show_sales_reports)
        self.refresh_btn = QPushButton("Actualizar")
        self.refresh_btn.clicked.connect(self.refresh_products)

        button_layout.addWidget(self.add_btn)
        button_layout.addWidget(self.edit_btn)
        button_layout.addWidget(self.delete_btn)
        button_layout.addWidget(self.sale_btn)
        button_layout.addWidget(self.history_btn)
        button_layout.addWidget(self.supplier_btn)
        button_layout.addWidget(self.restock_btn)
        button_layout.addWidget(self.sales_report_btn)
        button_layout.addWidget(self.refresh_btn)
        button_layout.addStretch()
        main_layout.addLayout(button_layout)

        self.products_table = QTableWidget()
        self.setup_table()
        main_layout.addWidget(self.products_table)
        self.statusBar().showMessage("Sistema iniciado correctamente")

    def setup_table(self):
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
        has_selection = bool(self.products_table.selectionModel().selectedRows())
        self.edit_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)

    def get_selected_product(self):
        selected_rows = self.products_table.selectionModel().selectedRows()
        if selected_rows:
            row = selected_rows[0].row()
            product_id = self.products_table.item(row, 0).text()
            return self.product_manager.get_product_by_id(product_id)
        return None

    def add_product(self):
        categories = self.product_manager.get_categories()
        supplier_names = self.supplier_manager.get_supplier_names()
        dialog = ProductFormDialog(self, categories=categories, supplier_names=supplier_names)
        if dialog.exec() == QDialog.Accepted:
            try:
                self.product_manager.add_product(**dialog.get_form_data())
                self.refresh_products()
                QMessageBox.information(self, "Éxito", "Producto añadido correctamente.")
            except Exception as error:
                QMessageBox.critical(self, "Error", f"Error al añadir producto: {error}")

    def edit_product(self):
        product = self.get_selected_product()
        if not product:
            return
        categories = self.product_manager.get_categories()
        supplier_names = self.supplier_manager.get_supplier_names()
        dialog = ProductFormDialog(self, product=product, categories=categories, supplier_names=supplier_names)
        if dialog.exec() == QDialog.Accepted:
            try:
                self.product_manager.update_product(product.id, **dialog.get_form_data())
                self.refresh_products()
                QMessageBox.information(self, "Éxito", "Producto actualizado correctamente.")
            except Exception as error:
                QMessageBox.critical(self, "Error", f"Error al actualizar producto: {error}")

    def delete_product(self):
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
        self.product_manager.load_products()
        available_products = self.product_manager.get_all_products()
        if not any(product.quantity > 0 for product in available_products):
            QMessageBox.warning(self, "Sin stock", "No hay productos disponibles para registrar una venta.")
            return

        dialog = SalesDialog(available_products, self.client_manager, self)
        if dialog.exec() != QDialog.Accepted:
            return
        sale_data = dialog.get_sale_data()

        try:
            sale = self.sale_manager.create_sale(
                sale_data["items"],
                sale_data["payment_method"],
                sale_data.get("received_amount", 0.0),
                sale_data.get("client_document", ""),
                sale_data.get("client_name", ""),
            )
            self.refresh_products()
            total_with_iva = sale.total + round(sale.total * IVA_RATE)
            self.statusBar().showMessage(f"Venta registrada correctamente - Total: ${total_with_iva:,.0f} COP")
            ReceiptDialog(sale, self).exec()
        except Exception as error:
            QMessageBox.critical(self, "Error", f"No se pudo registrar la venta: {error}")

    def show_purchase_history(self):
        PurchaseHistoryDialog(self.client_manager, self.sale_manager, self).exec()

    def manage_suppliers(self):
        SupplierManagementDialog(self.supplier_manager, self).exec()

    def manage_restock(self):
        RestockOrderDialog(
            self.product_manager,
            self.supplier_manager,
            self.restock_manager,
            self,
        ).exec()

    def show_sales_reports(self):
        SalesReportDialog(self.sale_manager, self).exec()

    def refresh_products(self):
        self.product_manager.load_products()
        if self.search_edit.text():
            self.search_products()
        else:
            self.load_products()

    def search_products(self):
        query = self.search_edit.text().strip()
        if not query:
            self.load_products()
            return
        search_type_map = {"Nombre": "name", "Categoría": "category", "Todos": "all"}
        search_type = search_type_map.get(self.search_type_combo.currentText(), "all")
        results = self.product_manager.search_products(query, search_type)
        self.load_products(results)

    def clear_search(self):
        self.search_edit.clear()
        self.search_type_combo.setCurrentText("Todos")
        self.load_products()


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
