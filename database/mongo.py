"""Conexion a MongoDB (unico lugar que conecta con Mongo)."""
from pymongo import MongoClient

from core.config import Config

_mongo_client = None


def get_mongo_client():
    global _mongo_client
    if _mongo_client is None:
        _mongo_client = MongoClient(Config.MONGO_URI)
    return _mongo_client


def get_mongo_collection():
    """Retorna la coleccion vehiculos (crea indice unico una vez)."""
    collection = get_mongo_client()[Config.MONGO_DB][Config.MONGO_COLLECTION]
    collection.create_index("vehiculo", unique=True)
    return collection
