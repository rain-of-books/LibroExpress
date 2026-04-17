"""
Módulo para la gestión de proveedores del sistema LibroExpress.
Maneja registro, edición, eliminación y persistencia en JSON.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional


class Supplier:
	"""Representa un proveedor registrado."""

	def __init__(
		self,
		name: str,
		phone: str,
		email: str,
		address: str = "",
		supplier_id: str = None,
	):
		self.id = supplier_id or self._generate_id()
		self.name = name
		self.phone = phone
		self.email = email
		self.address = address
		self.created_at = datetime.now().isoformat()
		self.updated_at = datetime.now().isoformat()

	def _generate_id(self) -> str:
		"""Genera un identificador único para el proveedor."""
		return f"SUP_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"

	def to_dict(self) -> Dict:
		"""Convierte el proveedor a diccionario."""
		return {
			"id": self.id,
			"name": self.name,
			"phone": self.phone,
			"email": self.email,
			"address": self.address,
			"created_at": self.created_at,
			"updated_at": self.updated_at,
		}

	@classmethod
	def from_dict(cls, data: Dict):
		"""Reconstruye un proveedor desde JSON."""
		supplier = cls(
			name=data["name"],
			phone=data["phone"],
			email=data["email"],
			address=data.get("address", ""),
			supplier_id=data["id"],
		)
		supplier.created_at = data.get("created_at", datetime.now().isoformat())
		supplier.updated_at = data.get("updated_at", datetime.now().isoformat())
		return supplier

	def update(self, **kwargs):
		"""Actualiza los campos del proveedor."""
		for key, value in kwargs.items():
			if hasattr(self, key):
				setattr(self, key, value)
		self.updated_at = datetime.now().isoformat()


class SupplierManager:
	"""Gestiona el CRUD de proveedores."""

	def __init__(self, json_file: str = "suppliers.json"):
		self.json_file = json_file
		self.suppliers: List[Supplier] = []
		self.load_suppliers()

	def load_suppliers(self) -> None:
		"""Carga proveedores desde JSON."""
		if os.path.exists(self.json_file):
			try:
				with open(self.json_file, "r", encoding="utf-8") as file:
					data = json.load(file)
					self.suppliers = [Supplier.from_dict(item) for item in data]
			except (json.JSONDecodeError, KeyError) as error:
				print(f"Error al cargar proveedores: {error}")
				self.suppliers = []
		else:
			self.save_suppliers()

	def save_suppliers(self) -> None:
		"""Guarda proveedores en JSON."""
		with open(self.json_file, "w", encoding="utf-8") as file:
			json.dump(
				[supplier.to_dict() for supplier in self.suppliers],
				file,
				indent=2,
				ensure_ascii=False,
			)

	def get_all_suppliers(self) -> List[Supplier]:
		"""Retorna la lista de proveedores."""
		return self.suppliers.copy()

	def get_supplier_by_id(self, supplier_id: str) -> Optional[Supplier]:
		"""Busca un proveedor por ID."""
		for supplier in self.suppliers:
			if supplier.id == supplier_id:
				return supplier
		return None

	def get_supplier_by_name(self, name: str) -> Optional[Supplier]:
		"""Busca un proveedor por nombre (insensible a mayúsculas/minúsculas)."""
		normalized_name = name.strip().lower()
		for supplier in self.suppliers:
			if supplier.name.strip().lower() == normalized_name:
				return supplier
		return None

	def get_supplier_names(self) -> List[str]:
		"""Retorna solo los nombres de proveedores para combos."""
		return sorted({supplier.name for supplier in self.suppliers if supplier.name})

	def add_supplier(
		self,
		name: str,
		phone: str = "",
		email: str = "",
		address: str = "",
	) -> Supplier:
		"""Registra un nuevo proveedor."""
		supplier = Supplier(name=name, phone=phone, email=email, address=address)
		self.suppliers.append(supplier)
		self.save_suppliers()
		return supplier

	def update_supplier(self, supplier_id: str, **kwargs) -> Optional[Supplier]:
		"""Actualiza un proveedor existente."""
		supplier = self.get_supplier_by_id(supplier_id)
		if supplier:
			supplier.update(**kwargs)
			self.save_suppliers()
			return supplier
		return None

	def delete_supplier(self, supplier_id: str) -> bool:
		"""Elimina un proveedor."""
		for index, supplier in enumerate(self.suppliers):
			if supplier.id == supplier_id:
				self.suppliers.pop(index)
				self.save_suppliers()
				return True
		return False
