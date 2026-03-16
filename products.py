"""
Módulo para la gestión de productos del sistema LibroExpress
Maneja las operaciones CRUD para productos almacenados en JSON
"""

import json
import os
from typing import List, Dict, Optional
from datetime import datetime


class Product:
    """Clase que representa un producto en el inventario"""
    
    def __init__(self, name: str, category: str, price: float, quantity: int, 
                 isbn: str = "", supplier: str = "", product_id: str = None):
        self.id = product_id or self._generate_id()
        self.name = name
        self.category = category
        self.price = price
        self.quantity = quantity
        self.isbn = isbn
        self.supplier = supplier
        self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
    
    def _generate_id(self) -> str:
        """Genera un ID único para el producto"""
        return f"PROD_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    def to_dict(self) -> Dict:
        """Convierte el producto a diccionario para JSON"""
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'price': self.price,
            'quantity': self.quantity,
            'isbn': self.isbn,
            'supplier': self.supplier,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict):
        """Crea un producto desde un diccionario"""
        product = cls(
            name=data['name'],
            category=data['category'],
            price=data['price'],
            quantity=data['quantity'],
            isbn=data.get('isbn', ''),
            supplier=data.get('supplier', ''),
            product_id=data['id']
        )
        product.created_at = data.get('created_at', datetime.now().isoformat())
        product.updated_at = data.get('updated_at', datetime.now().isoformat())
        return product
    
    def update(self, **kwargs):
        """Actualiza los campos del producto"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.now().isoformat()


class ProductManager:
    """Clase para gestionar las operaciones de productos"""
    
    def __init__(self, json_file: str = "products.json"):
        self.json_file = json_file
        self.products: List[Product] = []
        self.load_products()
    
    def load_products(self) -> None:
        """Carga los productos desde el archivo JSON"""
        if os.path.exists(self.json_file):
            try:
                with open(self.json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.products = [Product.from_dict(product_data) 
                                   for product_data in data]
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Error al cargar productos: {e}")
                self.products = []
        else:
            # Crear archivo vacío si no existe
            self.save_products()
    
    def save_products(self) -> None:
        """Guarda los productos en el archivo JSON"""
        try:
            with open(self.json_file, 'w', encoding='utf-8') as f:
                json.dump([product.to_dict() for product in self.products], 
                         f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error al guardar productos: {e}")
            raise
    
    def add_product(self, name: str, category: str, price: float, quantity: int,
                   isbn: str = "", supplier: str = "") -> Product:
        """Añade un nuevo producto al inventario"""
        product = Product(name, category, price, quantity, isbn, supplier)
        self.products.append(product)
        self.save_products()
        return product
    
    def get_all_products(self) -> List[Product]:
        """Obtiene todos los productos"""
        return self.products.copy()
    
    def search_products(self, query: str, search_by: str = "name") -> List[Product]:
        """Busca productos por nombre o categoría"""
        query = query.lower()
        results = []
        
        for product in self.products:
            if search_by == "name" and query in product.name.lower():
                results.append(product)
            elif search_by == "category" and query in product.category.lower():
                results.append(product)
            elif search_by == "all" and (query in product.name.lower() or 
                                       query in product.category.lower()):
                results.append(product)
        
        return results
    
    def update_product(self, product_id: str, **kwargs) -> Optional[Product]:
        """Actualiza un producto existente"""
        for product in self.products:
            if product.id == product_id:
                product.update(**kwargs)
                self.save_products()
                return product
        return None
    
    def delete_product(self, product_id: str) -> bool:
        """Elimina un producto del inventario"""
        for i, product in enumerate(self.products):
            if product.id == product_id:
                self.products.pop(i)
                self.save_products()
                return True
        return False
    
    def get_product_by_id(self, product_id: str) -> Optional[Product]:
        """Obtiene un producto por su ID"""
        for product in self.products:
            if product.id == product_id:
                return product
        return None
    
    def get_categories(self) -> List[str]:
        """Obtiene todas las categorías únicas"""
        categories = set()
        for product in self.products:
            if product.category:
                categories.add(product.category)
        return sorted(list(categories))