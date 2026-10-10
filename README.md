# Taller Flask + MongoDB + Redis — API de Vehículos

API REST con Flask y MongoDB (CRUD de vehículos) + caché en Redis con expiración condicional.

## Reglas de caché (según taller)

Al consultar `GET /api/vehiculos/<nombre>` se devuelve `fuente: MongoDB | Redis`.

| Condición | TTL |
|---|---|
| `vehiculo` ≤ 5 caracteres | 15 s |
| `vehiculo` 6–10 caracteres | 20 s |
| `vehiculo` > 10 caracteres | 40 s |
| `descripcion` > 20 caracteres | **No se guarda en caché (prioridad)** |

> Nota: los 10 vehículos de la tabla original tienen descripciones largas (>20), por eso **no se cachean** por diseño del taller. Para demostrar Redis en el video, cree vehículos de prueba con descripción corta (ver Demo de caché).

## Requisitos

- Python 3.10+
- MongoDB en ejecución (`mongodb://localhost:27017/`)
- Redis en ejecución (`localhost:6379`)

## Instalación y ejecución

```bash
# 1. Entorno Python
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
# source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env   # Windows: copy .env.example .env

# 2. Cargar datos iniciales (DB automoviles, 10 vehículos)
python scripts/seed.py

# 3. Ejecutar API
python app.py
# API en http://localhost:5000
```

Verificar salud: `GET http://localhost:5000/api/health`

## Estructura del proyecto

```
├── app.py                        # Crea la app Flask y registra rutas (sin lógica de negocio)
├── core/config.py                # Configuración centralizada desde .env
├── database/
│   ├── mongo.py                  # Conexión a MongoDB (único lugar que conecta)
│   └── redis_client.py           # Conexión a Redis (único lugar que conecta)
├── models/vehiculo.py            # Validación y serialización (reusado por POST/PUT)
├── repositories/vehiculo_repository.py  # Consultas MongoDB (sin Flask ni Redis)
├── services/cache_service.py     # Reglas TTL + lectura/escritura/invalidación Redis
├── routes/vehiculos.py           # Endpoints CRUD (orquestan repositorio + caché)
└── scripts/seed.py               # Carga inicial de los 10 vehículos
```

## Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/api/vehiculos` | Registrar vehículo |
| GET | `/api/vehiculos` | Listar todos |
| GET | `/api/vehiculos/<nombre>` | Consultar uno (con caché Redis + `fuente`) |
| PUT | `/api/vehiculos/<nombre>` | Actualizar (invalida caché) |
| DELETE | `/api/vehiculos/<nombre>` | Eliminar (invalida caché) |

Estructura del documento:

```json
{
  "vehiculo": "Barco",
  "categoria": "Acuático",
  "peso_toneladas": 500,
  "descripcion": "Embarcación grande usada para transporte marítimo."
}
```

## Ejemplos cURL

```bash
# Crear
curl -X POST http://localhost:5000/api/vehiculos -H "Content-Type: application/json" -d "{\"vehiculo\":\"Taxi\",\"categoria\":\"Terrestre (motorizado)\",\"peso_toneladas\":1.2,\"descripcion\":\"Auto amarillo\"}"

# Listar
curl http://localhost:5000/api/vehiculos

# Consultar uno (1ra vez -> MongoDB, 2da -> Redis)
curl http://localhost:5000/api/vehiculos/Taxi

# Ver TTL en Redis
redis-cli TTL "vehiculo:taxi"
redis-cli GET "vehiculo:taxi"

# Actualizar (invalida caché)
curl -X PUT http://localhost:5000/api/vehiculos/Taxi -H "Content-Type: application/json" -d "{\"peso_toneladas\":1.4}"

# Eliminar (invalida caché)
curl -X DELETE http://localhost:5000/api/vehiculos/Taxi
```

## Demo de caché para el video (tiempos de expiración)

Los datos semilla no se cachean (descripción > 20). Use estos 3 vehículos de prueba:

```bash
# TTL 15 s (nombre ≤ 5): "Bus" (3) + descripción corta
curl -X POST http://localhost:5000/api/vehiculos -H "Content-Type: application/json" -d "{\"vehiculo\":\"Bus\",\"categoria\":\"Terrestre (motorizado)\",\"peso_toneladas\":8,\"descripcion\":\"Bus urbano\"}"

# TTL 20 s (nombre 6-10): "Lancha" (6) + descripción corta
curl -X POST http://localhost:5000/api/vehiculos -H "Content-Type: application/json" -d "{\"vehiculo\":\"YateX\",\"categoria\":\"Acuático\",\"peso_toneladas\":5,\"descripcion\":\"Yate veloz\"}"

# TTL 40 s (nombre > 10): "Motocicleta" ya existe pero tiene descripción larga -> crear "Aerodeslizador" (15) corto
curl -X POST http://localhost:5000/api/vehiculos -H "Content-Type: application/json" -d "{\"vehiculo\":\"Aerodeslizador\",\"categoria\":\"Acuático\",\"peso_toneladas\":1,\"descripcion\":\"Nave rápida\"}"

# Caso NO cacheable (descripción > 20): cualquier vehículo semilla, ej. Barco
curl http://localhost:5000/api/vehiculos/Barco
# -> {"fuente":"MongoDB","cache":"No almacenado..."} y en Redis no existe la clave
```

Guion sugerido para el video (Redis):
1. `GET /api/vehiculos/Bus` → 1ra vez `fuente: MongoDB, ttl_asignado: 15`. 2da vez inmediata → `fuente: Redis, ttl_restante < 15`.
2. Mostrar en terminal `redis-cli KEYS *`, `TTL`, esperar 15 s y mostrar que expira (`TTL` = -2) y vuelve a `MongoDB`.
3. Repetir con `YateX` (20 s) y `Aerodeslizador` (40 s).
4. Mostrar `Barco` nunca se cachea.
5. Mostrar `PUT`/`DELETE` invalidan: consultar, luego actualizar/eliminar, luego `GET` en Redis = nil.

## Colección Postman

Importe `postman_collection.json` en Postman con todas las peticiones listas.
