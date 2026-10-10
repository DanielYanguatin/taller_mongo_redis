"""Acceso a MongoDB. Solo consultas a la coleccion vehiculos."""
from pymongo.errors import DuplicateKeyError


class VehiculoRepository:
    def __init__(self, collection):
        self.col = collection

    def list_all(self):
        return list(self.col.find().sort("vehiculo", 1))

    def find_by_nombre(self, nombre):
        return self.col.find_one(
            {"vehiculo": {"$regex": f"^{nombre.strip()}$", "$options": "i"}}
        )

    def find_by_id(self, object_id):
        return self.col.find_one({"_id": object_id})

    def insert(self, vehiculo, categoria, peso_toneladas, descripcion):
        """Inserta y retorna el documento creado. Lanza DuplicateKeyError si existe."""
        result = self.col.insert_one({
            "vehiculo": vehiculo,
            "categoria": categoria,
            "peso_toneladas": float(peso_toneladas),
            "descripcion": descripcion,
        })
        return self.find_by_id(result.inserted_id)

    def update(self, doc_id, cambios):
        """Aplica los cambios (dict ya filtrado). Lanza DuplicateKeyError si colisiona."""
        if "peso_toneladas" in cambios:
            cambios["peso_toneladas"] = float(cambios["peso_toneladas"])
        self.col.update_one({"_id": doc_id}, {"$set": cambios})
        return self.find_by_id(doc_id)

    def delete(self, doc_id):
        self.col.delete_one({"_id": doc_id})
