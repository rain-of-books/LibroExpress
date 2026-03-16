import json

ARCHIVO = "product.json"


def cargar_productos():
    try:
        with open(ARCHIVO, "r") as file:
            return json.load(file)
    except:
        return []


def guardar_productos(productos):
    with open(ARCHIVO, "w") as file:
        json.dump(productos, file, indent=4)