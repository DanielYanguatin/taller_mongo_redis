"""Configuracion centralizada leida desde variables de entorno."""
import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
    MONGO_DB = os.getenv("MONGO_DB", "automoviles")
    MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", "vehiculos")
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB = int(os.getenv("REDIS_DB", "0"))
    FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))
