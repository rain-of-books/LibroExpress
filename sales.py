"""
Módulo para la gestión de ventas del sistema LibroExpress.
Registra ventas, actualiza el stock y persiste la información en JSON.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List

IVA_RATE = 0.19
RECEIPTS_FOLDER = "recibos"

STORE_INFO = {
	"name": "LIBROEXPRESS",
	"subtitle": "Librería & Papelería",
	"nit": "123456789-0",
	"address": "Tumaco, Nariño",
	"phone": "300 000 0000",
}


class SaleItem:
	"""Representa un producto incluido en una venta."""

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
		"""Convierte el item a diccionario para JSON."""
		return {
			"product_id": self.product_id,
			"product_name": self.product_name,
			"unit_price": self.unit_price,
			"quantity": self.quantity,
			"subtotal": self.subtotal,
		}

	@classmethod
	def from_dict(cls, data: Dict):
		"""Reconstruye un item desde JSON."""
		return cls(
			product_id=data["product_id"],
			product_name=data["product_name"],
			unit_price=data["unit_price"],
			quantity=data["quantity"],
		)


class Sale:
	"""Representa una venta completa."""

	def __init__(
		self,
		items: List[SaleItem],
		payment_method: str,
		client_document: str = "",
		client_name: str = "",
		sale_id: str = None,
		created_at: str = None,
		invoice_number: int = 0,
		received_amount: float = 0.0,
		receipt_file: str = "",
	):
		self.id = sale_id or self._generate_id()
		self.items = items
		self.payment_method = payment_method
		self.client_document = client_document
		self.client_name = client_name
		self.total = sum(item.subtotal for item in items)
		self.invoice_number = invoice_number
		self.received_amount = received_amount
		self.receipt_file = receipt_file
		self.created_at = created_at or datetime.now().isoformat()

	def _generate_id(self) -> str:
		"""Genera un identificador único para la venta."""
		return f"SALE_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"

	def to_dict(self) -> Dict:
		"""Convierte la venta a diccionario para JSON."""
		return {
			"id": self.id,
			"invoice_number": self.invoice_number,
			"client_document": self.client_document,
			"client_name": self.client_name,
			"items": [item.to_dict() for item in self.items],
			"payment_method": self.payment_method,
			"received_amount": self.received_amount,
			"total": self.total,
			"created_at": self.created_at,
			"receipt_file": self.receipt_file,
		}

	@classmethod
	def from_dict(cls, data: Dict):
		"""Reconstruye una venta desde JSON."""
		items = [SaleItem.from_dict(item_data) for item_data in data.get("items", [])]
		return cls(
			items=items,
			payment_method=data["payment_method"],
			client_document=data.get("client_document", ""),
			client_name=data.get("client_name", ""),
			sale_id=data["id"],
			created_at=data.get("created_at"),
			invoice_number=data.get("invoice_number", 0),
			received_amount=data.get("received_amount", 0.0),
			receipt_file=data.get("receipt_file", ""),
		)


def generate_receipt_text(sale) -> str:
	"""Genera el texto del recibo en formato de factura para una venta."""
	W = 40
	SEP = "=" * W
	DASH = "-" * W

	dt = datetime.fromisoformat(sale.created_at)
	date_str = dt.strftime("%d/%m/%Y")
	time_str = dt.strftime("%H:%M")
	invoice_str = str(sale.invoice_number).zfill(6)

	def cop(amount: float) -> str:
		return f"{amount:,.0f}".replace(",", ".")

	lines = [
		SEP,
		STORE_INFO["name"].center(W),
		STORE_INFO["subtitle"].center(W),
		SEP,
		f"NIT: {STORE_INFO['nit']}",
		f"Dirección: {STORE_INFO['address']}",
		f"Tel: {STORE_INFO['phone']}",
		"",
		f"Fecha: {date_str}",
		f"Hora: {time_str}",
		f"Factura No: {invoice_str}",
		f"Cliente: {sale.client_name or 'No especificado'}",
		f"Documento: {sale.client_document or 'No especificado'}",
		"",
		DASH,
		f"{'Producto':<16}{'Cant':>4}{'Precio':>10}{'Subtotal':>10}",
		DASH,
	]

	for item in sale.items:
		name = item.product_name[:15].ljust(16)
		qty = str(item.quantity).rjust(4)
		price = cop(item.unit_price).rjust(10)
		subtotal_str = cop(item.subtotal).rjust(10)
		lines.append(f"{name}{qty}{price}{subtotal_str}")

	iva_amount = round(sale.total * IVA_RATE)
	total_with_iva = sale.total + iva_amount

	lines.extend([
		DASH,
		"",
		f"{'Subtotal:':<30}{cop(sale.total):>10}",
		f"{'IVA (19%):':<30}{cop(iva_amount):>10}",
		DASH,
		f"{'TOTAL:':<30}{cop(total_with_iva):>10}",
		DASH,
		"",
		f"Método de pago: {sale.payment_method.upper()}",
	])

	if sale.received_amount > 0:
		change = max(0.0, sale.received_amount - total_with_iva)
		lines.extend([
			"",
			f"{'Recibido:':<30}{cop(sale.received_amount):>10}",
			f"{'Cambio:':<30}{cop(change):>10}",
		])

	lines.extend([
		"",
		SEP,
		"¡Gracias por su compra!".center(W),
		SEP,
	])

	return "\n".join(lines)


class SaleManager:
	"""Gestiona el registro de ventas y la actualización de stock."""

	VALID_PAYMENT_METHODS = {"Efectivo", "Tarjeta"}

	def __init__(self, product_manager, json_file: str = "sales.json"):
		self.product_manager = product_manager
		self.json_file = json_file
		self.sales: List[Sale] = []
		self.load_sales()

	def load_sales(self) -> None:
		"""Carga las ventas desde el archivo JSON."""
		if os.path.exists(self.json_file):
			try:
				with open(self.json_file, "r", encoding="utf-8") as file:
					data = json.load(file)
					self.sales = [Sale.from_dict(sale_data) for sale_data in data]
			except (json.JSONDecodeError, KeyError) as error:
				print(f"Error al cargar ventas: {error}")
				self.sales = []
		else:
			self.save_sales()

	def save_sales(self) -> None:
		"""Guarda las ventas en el archivo JSON."""
		with open(self.json_file, "w", encoding="utf-8") as file:
			json.dump(
				[sale.to_dict() for sale in self.sales],
				file,
				indent=2,
				ensure_ascii=False,
			)

	def get_all_sales(self) -> List[Sale]:
		"""Retorna una copia de las ventas registradas."""
		return self.sales.copy()

	def get_sales_by_client_document(self, document: str) -> List[Sale]:
		"""Retorna las ventas asociadas a una cédula específica."""
		normalized_document = document.strip()
		return [sale for sale in self.sales if sale.client_document == normalized_document]

	def get_next_invoice_number(self) -> int:
		"""Retorna el próximo número de factura secuencial."""
		return len(self.sales) + 1

	def save_receipt(self, sale) -> None:
		"""Guarda el recibo de la venta en un archivo de texto."""
		folder = Path(RECEIPTS_FOLDER)
		folder.mkdir(exist_ok=True)
		receipt_path = folder / f"{sale.id}.txt"
		receipt_path.write_text(generate_receipt_text(sale), encoding="utf-8")

	def create_sale(
		self,
		items_data: List[Dict],
		payment_method: str,
		received_amount: float = 0.0,
		client_document: str = "",
		client_name: str = "",
	) -> Sale:
		"""Crea una venta, valida stock y actualiza el inventario."""
		if payment_method not in self.VALID_PAYMENT_METHODS:
			raise ValueError("El método de pago seleccionado no es válido.")

		if not items_data:
			raise ValueError("Debe agregar al menos un producto a la venta.")

		sale_items: List[SaleItem] = []
		stock_snapshot: Dict[str, int] = {}

		for item_data in items_data:
			product_id = item_data.get("product_id", "")
			quantity = int(item_data.get("quantity", 0))

			if quantity <= 0:
				raise ValueError("La cantidad de cada producto debe ser mayor a cero.")

			product = self.product_manager.get_product_by_id(product_id)
			if not product:
				raise ValueError("Uno de los productos seleccionados ya no existe.")

			if product.quantity < quantity:
				raise ValueError(
					f"Stock insuficiente para '{product.name}'. Disponible: {product.quantity}."
				)

			stock_snapshot[product.id] = product.quantity
			sale_items.append(
				SaleItem(
					product_id=product.id,
					product_name=product.name,
					unit_price=product.price,
					quantity=quantity,
				)
			)

		invoice_number = self.get_next_invoice_number()
		sale = Sale(
			items=sale_items,
			payment_method=payment_method,
			client_document=client_document,
			client_name=client_name,
			invoice_number=invoice_number,
			received_amount=received_amount,
		)
		sale.receipt_file = str(Path(RECEIPTS_FOLDER) / f"{sale.id}.txt")

		# --- Transacción atómica: stock + persistencia de la venta ---
		try:
			for sale_item in sale_items:
				product = self.product_manager.get_product_by_id(sale_item.product_id)
				product.update(quantity=product.quantity - sale_item.quantity)

			self.product_manager.save_products()
			self.sales.append(sale)
			self.save_sales()
		except Exception:
			# Revertir stock en memoria y en disco
			for pid, qty in stock_snapshot.items():
				product = self.product_manager.get_product_by_id(pid)
				if product:
					product.update(quantity=qty)
			self.product_manager.save_products()
			# Retirar la venta si ya se agregó a la lista antes del fallo
			if sale in self.sales:
				self.sales.remove(sale)
			raise

		# --- Guardado del recibo (no crítico: fallo aquí no revierte la venta) ---
		try:
			self.save_receipt(sale)
		except Exception as receipt_error:
			print(f"Advertencia: no se pudo guardar el archivo de recibo: {receipt_error}")
			sale.receipt_file = ""
			# Reflejar en sales.json que no hay archivo de recibo
			self.save_sales()

		return sale
