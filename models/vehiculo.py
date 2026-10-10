"""Validacion y serializacion del documento vehiculo.

Documento Mongo:
{
    "vehiculo": str (unico, identifica al vehiculo),
    "categoria": str,
    "peso_toneladas": float,
    "descripcion": str,
}
"""

CAMPOS = ("vehiculo", "categoria", "peso_toneladas", "descripcion")


def to_json(doc):
    """Convierte un documento Mongo a dict serializable (ObjectId -> str)."""
    if not doc:
        return None
    out = dict(doc)
    if "_id" in out:
        out["_id"] = str(out["_id"])
    return out


def validate(data, require_all=True):
    """Valida el payload de POST/PUT. Retorna mensaje de error o None."""
    if not isinstance(data, dict):
        return "El cuerpo debe ser un objeto JSON."
    if require_all:
        faltantes = [c for c in CAMPOS if c not in data]
        if faltantes:
            return f"Faltan campos obligatorios: {', '.join(faltantes)}."
    if "peso_toneladas" in data:
        try:
            float(data["peso_toneladas"])
        except (TypeError, ValueError):
            return "peso_toneladas debe ser numerico."
    return None
