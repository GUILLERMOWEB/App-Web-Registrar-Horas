import sys
sys.path.append('.')  # Agrega el directorio actual al path para evitar el conflicto de importación

from app import db, Cliente

# Definición de los clientes a cargar
clientes = [
    {"nombre": "Barraca Deambrosi SA", "direccion": "Sin dirección", "telefono": ""},
    {"nombre": "Cooperativa Agraria de (CALCAR)", "direccion": "Sin dirección", "telefono": ""},
    {"nombre": "Gibur S.A.", "direccion": "Sin dirección", "telefono": ""},
    {"nombre": "Nolir S.A.", "direccion": "Sin dirección", "telefono": ""},
    {"nombre": "Recalco SA (ex Suadil)", "direccion": "Sin dirección", "telefono": ""},
    {"nombre": "CONAPROLE Planta CIM", "direccion": "Sin dirección", "telefono": ""},
    {"nombre": "CONAPROLE Planta VIII", "direccion": "Sin dirección", "telefono": ""},
    {"nombre": "Cerealin San Jose", "direccion": "Sin dirección", "telefono": ""},
    {"nombre": "Jugos del Uruguay SA", "direccion": "Sin dirección", "telefono": ""},
    {"nombre": "OTRO CLIENTE CLUSTER", "direccion": "Sin dirección", "telefono": ""},
    {"nombre": "Tetrapak San Fernando", "direccion": "Sin dirección", "telefono": ""}
]

# Cargar los clientes a la base de datos
for datos in clientes:
    cliente = Cliente(**datos)
    db.session.add(cliente)

# Confirmar los cambios en la base de datos
db.session.commit()

print("Clientes cargados.")
