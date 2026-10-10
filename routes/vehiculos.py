"""Endpoints CRUD de vehiculos (usan repositorio Mongo + servicio Redis)."""
from flask import Blueprint, jsonify, request
from pymongo.errors import DuplicateKeyError

from database.mongo import get_mongo_collection
from database.redis_client import get_redis_client
from models.vehiculo import to_json, validate
from repositories.vehiculo_repository import VehiculoRepository
from services.cache_service import CacheService

bp = Blueprint("vehiculos", __name__, url_prefix="/api/vehiculos")


def _deps():
    return (
        VehiculoRepository(get_mongo_collection()),
        CacheService(get_redis_client()),
    )


@bp.route("", methods=["POST"])
def crear():
    data = request.get_json(force=True, silent=True)
    error = validate(data, require_all=True)
    if error:
        return jsonify({"error": error}), 400
    nombre = str(data["vehiculo"]).strip()
    if not nombre:
        return jsonify({"error": "vehiculo no puede estar vacio."}), 400
    repo, _ = _deps()
    try:
        doc = repo.insert(nombre, data["categoria"], data["peso_toneladas"], data["descripcion"])
    except DuplicateKeyError:
        return jsonify({"error": f"Ya existe un vehiculo '{nombre}'."}), 409
    return jsonify(to_json(doc)), 201


@bp.route("", methods=["GET"])
def listar():
    repo, _ = _deps()
    docs = [to_json(d) for d in repo.list_all()]
    return jsonify({"total": len(docs), "fuente": "MongoDB", "datos": docs}), 200


@bp.route("/<nombre>", methods=["GET"])
def obtener(nombre):
    nombre = nombre.strip()
    repo, cache = _deps()

    dato, ttl_restante = cache.get(nombre)
    if dato:
        dato["fuente"] = "Redis"
        if ttl_restante is not None:
            dato["ttl_restante"] = ttl_restante
        return jsonify(dato), 200

    doc = repo.find_by_nombre(nombre)
    if not doc:
        return jsonify({"error": f"Vehiculo '{nombre}' no encontrado."}), 404
    dato = to_json(doc)

    ttl = cache.save_if_cacheable(dato)
    if ttl is None:
        dato["fuente"] = "MongoDB"
        dato["cache"] = "No almacenado (descripcion superior a 20 caracteres)"
    else:
        dato["fuente"] = "MongoDB"
        dato["ttl_asignado"] = ttl
    return jsonify(dato), 200


@bp.route("/<nombre>", methods=["PUT"])
def actualizar(nombre):
    nombre = nombre.strip()
    data = request.get_json(force=True, silent=True)
    if not isinstance(data, dict) or not data:
        return jsonify({"error": "Cuerpo JSON vacio."}), 400
    error = validate(data, require_all=False)
    if error:
        return jsonify({"error": error}), 400

    repo, cache = _deps()
    doc = repo.find_by_nombre(nombre)
    if not doc:
        return jsonify({"error": f"Vehiculo '{nombre}' no encontrado."}), 404

    cambios = {c: data[c] for c in ("vehiculo", "categoria", "peso_toneladas", "descripcion") if c in data}
    if "vehiculo" in cambios:
        cambios["vehiculo"] = str(cambios["vehiculo"]).strip()
        if not cambios["vehiculo"]:
            return jsonify({"error": "vehiculo no puede estar vacio."}), 400
    try:
        nuevo = repo.update(doc["_id"], cambios)
    except DuplicateKeyError:
        return jsonify({"error": f"Ya existe un vehiculo '{cambios.get('vehiculo')}'."}), 409

    cache.invalidate(nombre, cambios.get("vehiculo"))
    out = to_json(nuevo)
    out["fuente"] = "MongoDB"
    out["cache"] = "Invalidada por actualizacion"
    return jsonify(out), 200


@bp.route("/<nombre>", methods=["DELETE"])
def eliminar(nombre):
    nombre = nombre.strip()
    repo, cache = _deps()
    doc = repo.find_by_nombre(nombre)
    if not doc:
        return jsonify({"error": f"Vehiculo '{nombre}' no encontrado."}), 404
    repo.delete(doc["_id"])
    cache.invalidate(nombre)
    return jsonify({
        "mensaje": f"Vehiculo '{doc['vehiculo']}' eliminado.",
        "cache": "Invalidada por eliminacion",
    }), 200
