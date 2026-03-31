"""
Módulo para la gestión de clientes del sistema LibroExpress.
Maneja registro, búsqueda y persistencia en JSON.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional


class Client:
	"""Representa un cliente registrado en el sistema."""

	def __init__(
		self,
		name: str,
		document: str,
		email: str,
		phone: str,
		client_id: str = None,
	):
		self.id = client_id or self._generate_id()
		self.name = name
		self.document = document
		self.email = email
		self.phone = phone
		self.created_at = datetime.now().isoformat()
		self.updated_at = datetime.now().isoformat()

	def _generate_id(self) -> str:
		"""Genera un identificador único para el cliente."""
		return f"CLI_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"

	def to_dict(self) -> Dict:
		"""Convierte el cliente a diccionario para JSON."""
		return {
			"id": self.id,
			"name": self.name,
			"document": self.document,
			"email": self.email,
			"phone": self.phone,
			"created_at": self.created_at,
			"updated_at": self.updated_at,
		}

	@classmethod
	def from_dict(cls, data: Dict):
		"""Reconstruye un cliente desde JSON."""
		client = cls(
			name=data["name"],
			document=data["document"],
			email=data["email"],
			phone=data["phone"],
			client_id=data["id"],
		)
		client.created_at = data.get("created_at", datetime.now().isoformat())
		client.updated_at = data.get("updated_at", datetime.now().isoformat())
		return client

	def update(self, **kwargs):
		"""Actualiza los campos del cliente."""
		for key, value in kwargs.items():
			if hasattr(self, key):
				setattr(self, key, value)
		self.updated_at = datetime.now().isoformat()


class ClientManager:
	"""Gestiona registro y consulta de clientes."""

	def __init__(self, json_file: str = "clients.json"):
		self.json_file = json_file
		self.clients: List[Client] = []
		self.load_clients()

	def load_clients(self) -> None:
		"""Carga los clientes desde el archivo JSON."""
		if os.path.exists(self.json_file):
			try:
				with open(self.json_file, "r", encoding="utf-8") as file:
					data = json.load(file)
					self.clients = [Client.from_dict(client_data) for client_data in data]
			except (json.JSONDecodeError, KeyError) as error:
				print(f"Error al cargar clientes: {error}")
				self.clients = []
		else:
			self.save_clients()

	def save_clients(self) -> None:
		"""Guarda los clientes en el archivo JSON."""
		with open(self.json_file, "w", encoding="utf-8") as file:
			json.dump(
				[client.to_dict() for client in self.clients],
				file,
				indent=2,
				ensure_ascii=False,
			)

	def get_all_clients(self) -> List[Client]:
		"""Retorna todos los clientes registrados."""
		return self.clients.copy()

	def get_client_by_document(self, document: str) -> Optional[Client]:
		"""Busca un cliente por documento."""
		normalized_document = document.strip()
		for client in self.clients:
			if client.document == normalized_document:
				return client
		return None

	def add_client(self, name: str, document: str, email: str, phone: str) -> Client:
		"""Registra un nuevo cliente validando documento único."""
		if self.get_client_by_document(document):
			raise ValueError("Ya existe un cliente registrado con ese documento.")

		client = Client(name=name, document=document, email=email, phone=phone)
		self.clients.append(client)
		self.save_clients()
		return client

	def update_client(self, client_id: str, **kwargs) -> Optional[Client]:
		"""Actualiza un cliente existente."""
		for client in self.clients:
			if client.id == client_id:
				new_document = kwargs.get("document")
				if new_document and new_document != client.document:
					existing_client = self.get_client_by_document(new_document)
					if existing_client and existing_client.id != client.id:
						raise ValueError("Ya existe un cliente registrado con ese documento.")
				client.update(**kwargs)
				self.save_clients()
				return client
		return None

	def delete_client(self, client_id: str) -> bool:
		"""Elimina un cliente del sistema."""
		for index, client in enumerate(self.clients):
			if client.id == client_id:
				self.clients.pop(index)
				self.save_clients()
				return True
		return False
