"""Cache en Redis con las reglas de expiracion del taller.

- descripcion > 20 caracteres -> NO se guarda (prioridad).
- vehiculo <= 5  -> 15 s | 6-10 -> 20 s | > 10 -> 40 s
"""
import json


def _ttl(vehiculo, descripcion):
    if descripcion is not None and len(descripcion) > 20:
        return None
    n = len((vehiculo or "").strip())
    if n <= 5:
        return 15
    if n <= 10:
        return 20
    return 40


class CacheService:
    def __init__(self, redis_client):
        self.r = redis_client

    @staticmethod
    def key(nombre):
        return f"vehiculo:{nombre.strip().lower()}"

    def get(self, nombre):
        """Retorna (dato, ttl_restante) o (None, None) si no esta en cache."""
        try:
            raw = self.r.get(self.key(nombre))
        except Exception:
            return None, None
        if not raw:
            return None, None
        try:
            ttl = self.r.ttl(self.key(nombre))
        except Exception:
            ttl = None
        return json.loads(raw), ttl

    def save_if_cacheable(self, dato):
        """Guarda en Redis si cumple las reglas. Retorna el TTL o None."""
        ttl = _ttl(dato.get("vehiculo", ""), dato.get("descripcion", ""))
        if ttl is None:
            return None
        try:
            self.r.setex(self.key(dato["vehiculo"]), ttl, json.dumps(dato, ensure_ascii=False))
        except Exception:
            pass
        return ttl

    def invalidate(self, nombre, nuevo_nombre=None):
        try:
            self.r.delete(self.key(nombre))
            if nuevo_nombre and nuevo_nombre.strip().lower() != nombre.strip().lower():
                self.r.delete(self.key(nuevo_nombre))
        except Exception:
            pass
