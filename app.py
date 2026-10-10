"""App Flask: solo crea la app y registra rutas (sin logica de negocio)."""
from flask import Flask, jsonify

from core.config import Config
from database.mongo import get_mongo_client
from database.redis_client import get_redis_client
from routes.vehiculos import bp as vehiculos_bp


def create_app():
    app = Flask(__name__)
    app.register_blueprint(vehiculos_bp)

    @app.route("/", methods=["GET"])
    def index():
        return jsonify({
            "mensaje": "API Vehiculos - Flask + MongoDB + Redis",
            "endpoints": {
                "POST": "/api/vehiculos",
                "GET todos": "/api/vehiculos",
                "GET uno": "/api/vehiculos/<nombre>",
                "PUT": "/api/vehiculos/<nombre>",
                "DELETE": "/api/vehiculos/<nombre>",
                "Salud": "/api/health",
            },
            "reglas_cache": {
                "descripcion > 20 caracteres": "NO se almacena (prioridad)",
                "vehiculo <= 5 caracteres": "15 seg",
                "vehiculo 6-10 caracteres": "20 seg",
                "vehiculo > 10 caracteres": "40 seg",
            },
        })

    @app.route("/api/health", methods=["GET"])
    def health():
        estado = {"flask": "ok"}
        try:
            get_mongo_client().admin.command("ping")
            estado["mongodb"] = "ok"
        except Exception as e:
            estado["mongodb"] = f"error: {e}"
        try:
            get_redis_client().ping()
            estado["redis"] = "ok"
        except Exception as e:
            estado["redis"] = f"error: {e}"
        code = 200 if estado.get("mongodb") == "ok" and estado.get("redis") == "ok" else 503
        return jsonify(estado), code

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=Config.FLASK_PORT, debug=True)
