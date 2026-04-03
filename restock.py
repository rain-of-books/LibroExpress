"""
Módulo para gestionar órdenes de reabastecimiento.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


RESTOCK_ORDERS_FOLDER = "ordenes_reabastecimiento"


class RestockItem:
    """Representa un ítem dentro de una orden de reabastecimiento."""

    def __init__(
        self,
        product_id: str,
        product_name: str,
        unit_price: float,
        quantity: int,
    ):
        self.product_id = product_id
        self.product_name = product_name
        self.unit_price = unit_price
        self.quantity = quantity
        self.subtotal = unit_price * quantity

    def to_dict(self) -> Dict:
        return {
            "product_id": self.product_id,
            "product_name": self.product_name,
            "unit_price": self.unit_price,
            "quantity": self.quantity,
            "subtotal": self.subtotal,
        }

    @classmethod
    def from_dict(cls, data: Dict):
        return cls(
            product_id=data["product_id"],
            product_name=data["product_name"],
            unit_price=data["unit_price"],
            quantity=data["quantity"],
        )


class RestockOrder:
    """Representa una orden de compra a proveedor para reabastecimiento."""

    def __init__(
        self,
        supplier_id: str,
        supplier_name: str,
        items: List[RestockItem],
        notes: str = "",
        order_id: str = None,
        created_at: str = None,
        file_path: str = "",
    ):
        self.id = order_id or self._generate_id()
        self.supplier_id = supplier_id
        self.supplier_name = supplier_name
        self.items = items
        self.notes = notes
        self.created_at = created_at or datetime.now().isoformat()
        self.file_path = file_path
        self.total = sum(item.subtotal for item in items)

    def _generate_id(self) -> str:
        return f"ORD_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "supplier_id": self.supplier_id,
            "supplier_name": self.supplier_name,
            "items": [item.to_dict() for item in self.items],
            "notes": self.notes,
            "created_at": self.created_at,
            "file_path": self.file_path,
            "total": self.total,
        }

    @classmethod
    def from_dict(cls, data: Dict):
        items = [RestockItem.from_dict(item_data) for item_data in data.get("items", [])]
        order = cls(
            supplier_id=data["supplier_id"],
            supplier_name=data["supplier_name"],
            items=items,
            notes=data.get("notes", ""),
            order_id=data["id"],
            created_at=data.get("created_at"),
            file_path=data.get("file_path", ""),
        )
        return order


def generate_restock_order_text(order: RestockOrder) -> str:
    """Genera el archivo de texto de la orden para envío manual al proveedor."""
    lines = [
        "=" * 52,
        "LIBROEXPRESS - ORDEN DE REABASTECIMIENTO",
        "=" * 52,
        f"Orden ID: {order.id}",
        f"Fecha: {order.created_at}",
        f"Proveedor: {order.supplier_name}",
        "",
        "Detalle de productos:",
        "-" * 52,
        f"{'Producto':<24}{'Cant':>8}{'Precio':>10}{'Subtotal':>10}",
        "-" * 52,
    ]


    for item in order.items:
        name = item.product_name[:24]
        lines.append(
            f"{name:<24}{item.quantity:>8}{item.unit_price:>10.0f}{item.subtotal:>10.0f}"
        )

    lines.extend([
        "-" * 52,
        f"{'TOTAL':<42}{order.total:>10.0f}",
        "",
        f"Notas: {order.notes or 'Sin notas'}",
        "",
        "Esta orden fue generada por LibroExpress para envío manual al proveedor.",
    ])

    return "\n".join(lines)


def generate_restock_order_pdf(order: RestockOrder, file_path: Path) -> None:
    """Genera una orden de reabastecimiento en PDF con formato empresarial."""
    doc = SimpleDocTemplate(
        str(file_path),
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )
    styles = getSampleStyleSheet()
    story = []

    title_style = styles["Title"]
    normal_style = styles["Normal"]
    heading_style = styles["Heading4"]

    story.append(Paragraph("LibroExpress - Orden de Reabastecimiento", title_style))
    story.append(Spacer(1, 8))
    story.append(Paragraph(f"<b>Orden ID:</b> {order.id}", normal_style))
    story.append(Paragraph(f"<b>Fecha:</b> {order.created_at.replace('T', ' ')}", normal_style))
    story.append(Paragraph(f"<b>Proveedor:</b> {order.supplier_name}", normal_style))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Detalle de productos", heading_style))
    story.append(Spacer(1, 6))

    table_data = [["Producto", "Cantidad", "Precio Unitario", "Subtotal"]]
    for item in order.items:
        table_data.append([
            item.product_name,
            str(item.quantity),
            f"${item.unit_price:,.0f}",
            f"${item.subtotal:,.0f}",
        ])

    table_data.append(["", "", "TOTAL", f"${order.total:,.0f}"])

    table = Table(table_data, colWidths=[80 * mm, 22 * mm, 35 * mm, 35 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E78")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("GRID", (0, 0), (-1, -2), 0.5, colors.HexColor("#B0B7C3")),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#E9EEF5")),
        ("FONTNAME", (2, -1), (3, -1), "Helvetica-Bold"),
        ("BOX", (0, -1), (-1, -1), 0.8, colors.HexColor("#7C8798")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(table)
    story.append(Spacer(1, 12))

    notes_text = order.notes.strip() if order.notes.strip() else "Sin notas"
    story.append(Paragraph(f"<b>Notas:</b> {notes_text}", normal_style))
    story.append(Spacer(1, 8))
    story.append(Paragraph("Este documento ha sido generado automáticamente por el sistema LibroExpress como soporte del proceso de reabastecimiento.", normal_style))

    doc.build(story)


class RestockOrderManager:
    """Gestiona creación, persistencia y descarga de órdenes de reabastecimiento."""

    def __init__(
        self,
        product_manager,
        supplier_manager,
        json_file: str = "restock_orders.json",
    ):
        self.product_manager = product_manager
        self.supplier_manager = supplier_manager
        self.json_file = json_file
        self.orders: List[RestockOrder] = []
        self.load_orders()

    def load_orders(self) -> None:
        if os.path.exists(self.json_file):
            try:
                with open(self.json_file, "r", encoding="utf-8") as file:
                    data = json.load(file)
                    self.orders = [RestockOrder.from_dict(order_data) for order_data in data]
            except (json.JSONDecodeError, KeyError) as error:
                print(f"Error al cargar órdenes de reabastecimiento: {error}")
                self.orders = []
        else:
            self.save_orders()

    def save_orders(self) -> None:
        with open(self.json_file, "w", encoding="utf-8") as file:
            json.dump(
                [order.to_dict() for order in self.orders],
                file,
                indent=2,
                ensure_ascii=False,
            )

    def get_all_orders(self) -> List[RestockOrder]:
        return self.orders.copy()

    def get_order_by_id(self, order_id: str) -> Optional[RestockOrder]:
        for order in self.orders:
            if order.id == order_id:
                return order
        return None

    def delete_order(self, order_id: str) -> bool:
        """Elimina una orden y su archivo asociado si existe."""
        for index, order in enumerate(self.orders):
            if order.id == order_id:
                if order.file_path:
                    file_path = Path(order.file_path)
                    if file_path.exists():
                        file_path.unlink()
                self.orders.pop(index)
                self.save_orders()
                return True
        return False

    def save_order_file(self, order: RestockOrder) -> None:
        folder = Path(RESTOCK_ORDERS_FOLDER)
        folder.mkdir(exist_ok=True)
        file_path = folder / f"{order.id}.pdf"
        generate_restock_order_pdf(order, file_path)
        order.file_path = str(file_path)

    def create_order(self, supplier_id: str, items_data: List[Dict], notes: str = "") -> RestockOrder:
        supplier = self.supplier_manager.get_supplier_by_id(supplier_id)
        if not supplier:
            raise ValueError("Debe seleccionar un proveedor válido.")
        supplier_name_normalized = supplier.name.strip().lower()

        if not items_data:
            raise ValueError("Debe agregar al menos un producto a la orden.")

        order_items: List[RestockItem] = []
        for item_data in items_data:
            product_id = item_data.get("product_id", "")
            quantity = int(item_data.get("quantity", 0))

            if quantity <= 0:
                raise ValueError("La cantidad solicitada debe ser mayor a cero.")

            product = self.product_manager.get_product_by_id(product_id)
            if not product:
                raise ValueError("Uno de los productos seleccionados ya no existe.")

            product_supplier = product.supplier.strip()
            if not product_supplier:
                raise ValueError(
                    f"El producto '{product.name}' no tiene proveedor asignado. Actualice el producto antes de crear la orden."
                )
            if product_supplier.lower() != supplier_name_normalized:
                raise ValueError(
                    f"El producto '{product.name}' está asignado al proveedor '{product_supplier}'."
                )

            order_items.append(
                RestockItem(
                    product_id=product.id,
                    product_name=product.name,
                    unit_price=product.price,
                    quantity=quantity,
                )
            )

        order = RestockOrder(
            supplier_id=supplier.id,
            supplier_name=supplier.name,
            items=order_items,
            notes=notes.strip(),
        )

        self.save_order_file(order)
        self.orders.append(order)
        self.save_orders()
        return order
