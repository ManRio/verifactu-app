# VeriFactu App

Aplicación web de facturación ligera orientada a autónomos, pequeños comercios y pequeñas empresas en España, diseñada con una arquitectura preparada para incorporar los requisitos de **VERI\*FACTU**.

> **Estado del proyecto:** en desarrollo.
> La aplicación todavía **no debe considerarse un sistema VERI\*FACTU conforme**. La integración y validación completa con las especificaciones técnicas de la AEAT forma parte de fases posteriores del proyecto.

---

## 🎯 Objetivo

El objetivo de VeriFactu App es construir una solución de facturación sencilla para negocios que necesitan gestionar productos, clientes y facturas sin recurrir a un ERP o CRM complejo.

El proyecto busca combinar:

- Una interfaz sencilla y moderna.
- Una API REST estructurada.
- Persistencia en PostgreSQL.
- Gestión segura de facturas y numeración.
- Registros de facturación inmutables.
- Encadenamiento criptográfico.
- Generación de QR.
- Preparación para comunicación con los servicios de la AEAT.
- Trazabilidad de envíos, errores y correcciones.

El proyecto se desarrolla también como proyecto de portfolio, prestando especial atención a arquitectura, calidad de código, testing y buenas prácticas.

---

## 🚧 Estado actual

Actualmente se encuentra implementada la infraestructura inicial del backend y el primer dominio de la aplicación: **Business**.

### Implementado

- FastAPI configurado.
- PostgreSQL 17 mediante Docker.
- SQLAlchemy 2.
- Psycopg.
- Pydantic Settings.
- Variables de entorno.
- Alembic configurado.
- Sistema de migraciones operativo.
- Modelo `Business`.
- Migración de la tabla `businesses`.
- Esquemas Pydantic para creación, actualización y lectura.
- Patrón Repository.
- Capa Service.
- Control de duplicados por identificador fiscal.
- API REST inicial de empresas.
- Endpoint de health check.
- Endpoint de health check de PostgreSQL.
- Tests de repositorio.
- Tests de servicio.
- Fixtures transaccionales para evitar que los tests ensucien la base de datos.
- Swagger/OpenAPI mediante FastAPI.

### API implementada

Actualmente están disponibles:

```text
GET  /health
GET  /health/db

POST /businesses
GET  /businesses/{business_id}
```

Comportamiento probado:

```text
POST /businesses válido          → 201 Created
GET /businesses/{id} existente   → 200 OK
POST con tax_id duplicado        → 409 Conflict
GET de Business inexistente      → 404 Not Found
```

---

## 🧱 Stack tecnológico

### Backend

- Python 3.13
- FastAPI
- Uvicorn
- Pydantic
- Pydantic Settings
- SQLAlchemy 2
- Alembic
- Psycopg
- PostgreSQL 17
- Pytest
- Ruff

### Infraestructura

- Docker
- Docker Compose
- Git
- GitHub

### Frontend previsto

El frontend todavía no se ha iniciado.

Stack previsto:

- React
- TypeScript
- Vite
- Tailwind CSS

Podrán incorporarse posteriormente herramientas como:

- TanStack Query
- React Hook Form
- Zod

---

## 🏗️ Arquitectura

El backend evita concentrar toda la lógica en los endpoints de FastAPI.

La arquitectura se está construyendo separando responsabilidades entre distintas capas.

```text
HTTP Request
     │
     ▼
FastAPI Router
     │
     ▼
Service
     │
     ▼
Repository
     │
     ▼
SQLAlchemy
     │
     ▼
PostgreSQL
```

### Router

Responsable del contrato HTTP:

- recibir requests;
- validar parámetros;
- devolver códigos HTTP;
- convertir errores de negocio en respuestas HTTP.

### Service

Responsable de:

- reglas de negocio;
- coordinación de operaciones;
- control transaccional;
- coordinación entre varios repositorios.

### Repository

Responsable exclusivamente del acceso a datos:

- consultas;
- inserciones;
- modificaciones;
- acceso mediante SQLAlchemy.

El repositorio no decide cuándo realizar el `commit` de una operación.

Esta separación será especialmente importante cuando se implemente el proceso de facturación y VERI\*FACTU, donde varias operaciones deberán ejecutarse dentro de una única transacción.

---

## 📁 Estructura actual

```text
verifactu-app/
│
├── backend/
│   ├── alembic/
│   │   ├── versions/
│   │   ├── env.py
│   │   └── script.py.mako
│   │
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/
│   │   │       └── business.py
│   │   │
│   │   ├── core/
│   │   │   └── config.py
│   │   │
│   │   ├── db/
│   │   │   ├── base.py
│   │   │   ├── models.py
│   │   │   └── session.py
│   │   │
│   │   ├── domain/
│   │   │   └── business/
│   │   │       ├── model.py
│   │   │       ├── repository.py
│   │   │       ├── schemas.py
│   │   │       └── service.py
│   │   │
│   │   └── main.py
│   │
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_business_repository.py
│   │   ├── test_business_service.py
│   │   └── test_health.py
│   │
│   ├── alembic.ini
│   └── pyproject.toml
│
├── frontend/
├── docs/
├── .env.example
├── .gitignore
├── docker-compose.yml
└── README.md
```

---

## 🏢 Dominio Business

`Business` representa la empresa o negocio emisor que utilizará la aplicación.

Actualmente almacena:

- razón social;
- identificador fiscal;
- nombre comercial;
- dirección;
- código postal;
- ciudad;
- provincia;
- código de país;
- fecha de creación;
- fecha de actualización.

El identificador fiscal (`tax_id`) tiene una restricción de unicidad en PostgreSQL.

Además, la capa de servicio detecta previamente los duplicados y los transforma posteriormente en un:

```text
HTTP 409 Conflict
```

---

## 🗄️ Base de datos

La aplicación utiliza PostgreSQL.

Durante el desarrollo PostgreSQL se ejecuta mediante Docker Compose.

Configuración actual del contenedor:

```text
Database: verifactu
User:     verifactu
Host:     localhost
Port:     55732
```

El puerto `55732` se utiliza en el host para evitar conflictos con instalaciones locales de PostgreSQL.

El puerto interno del contenedor sigue siendo:

```text
5432
```

---

## 🔐 Variables de entorno

Las credenciales reales no deben almacenarse en Git.

El proyecto utiliza un archivo:

```text
.env
```

que debe permanecer excluido mediante `.gitignore`.

Para configurar un entorno nuevo se utilizará:

```text
.env.example
```

Ejemplo:

```env
POSTGRES_DB=verifactu
POSTGRES_USER=verifactu
POSTGRES_PASSWORD=change_me
POSTGRES_HOST=localhost
POSTGRES_PORT=55732
```

Nunca deben almacenarse contraseñas reales, tokens, claves privadas o secretos dentro del repositorio.

---

## ⚙️ Instalación del backend

### 1. Clonar el repositorio

```bash
git clone <repository-url>
cd verifactu-app/backend
```

### 2. Crear entorno virtual

En Windows:

```powershell
python -m venv .venv
```

### 3. Activar entorno virtual

```powershell
.\.venv\Scripts\Activate.ps1
```

### 4. Instalar dependencias

```powershell
pip install -e ".[dev]"
```

### 5. Configurar variables de entorno

Crear `.env` en la raíz del proyecto tomando como referencia:

```text
.env.example
```

### 6. Iniciar PostgreSQL

Desde la raíz del proyecto:

```powershell
docker compose up -d
```

Comprobar:

```powershell
docker ps
```

### 7. Ejecutar migraciones

Desde `backend`:

```powershell
alembic upgrade head
```

### 8. Iniciar FastAPI

```powershell
uvicorn app.main:app --reload
```

La API estará disponible en:

```text
http://127.0.0.1:8000
```

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

OpenAPI:

```text
http://127.0.0.1:8000/openapi.json
```

---

## 🩺 Health checks

### API

```http
GET /health
```

Respuesta:

```json
{
  "status": "ok"
}
```

### PostgreSQL

```http
GET /health/db
```

Respuesta esperada:

```json
{
  "status": "ok",
  "database": 1
}
```

---

## 🏢 API Business

### Crear empresa

```http
POST /businesses
```

Ejemplo:

```json
{
  "legal_name": "Mi Tienda Demo SL",
  "tax_id": "B87654321",
  "trade_name": "Mi Tienda",
  "address": "Calle Principal 10",
  "postal_code": "41001",
  "city": "Sevilla",
  "province": "Sevilla",
  "country_code": "ES"
}
```

Respuesta:

```text
201 Created
```

Si ya existe el identificador fiscal:

```text
409 Conflict
```

### Consultar empresa

```http
GET /businesses/{business_id}
```

Si existe:

```text
200 OK
```

Si no existe:

```text
404 Not Found
```

---

## 🧪 Testing

La suite utiliza Pytest.

Ejecutar todos los tests:

```powershell
pytest -v
```

Estado actual:

```text
12 passed
```

Los tests cubren actualmente:

- health check de FastAPI;
- conexión con PostgreSQL;
- creación de empresas mediante Repository;
- búsqueda por ID;
- búsqueda por identificador fiscal;
- creación mediante Service;
- consulta mediante Service;
- rechazo de identificadores fiscales duplicados.
- creación de empresas mediante la API (`201 Created`);
- consulta de empresas mediante la API (`200 OK`);
- rechazo de identificadores fiscales duplicados mediante la API (`409 Conflict`);
- respuesta para empresas inexistentes mediante la API (`404 Not Found`).

Los tests de persistencia utilizan transacciones aisladas que se revierten al terminar cada prueba para evitar contaminar la base de desarrollo.

Los tests de integración de la API utilizan `FastAPI TestClient` y sobrescriben temporalmente la dependencia `get_db` para utilizar la misma sesión aislada de pruebas.

Existe actualmente un warning conocido relacionado con la integración entre `Starlette TestClient` y `httpx`. No bloquea la ejecución de la suite y se abordará en una fase posterior.

---

## 🗃️ Migraciones

Alembic gestiona el esquema de PostgreSQL.

Migraciones actuales:

```text
f59baa15a544  initial migration
4edaea57d404  create businesses table
```

Consultar migración actual:

```powershell
alembic current
```

Crear una nueva migración:

```powershell
alembic revision --autogenerate -m "description"
```

Aplicar:

```powershell
alembic upgrade head
```

Las migraciones autogeneradas deben revisarse antes de aplicarse.

---

## 🧾 VERI\*FACTU

La arquitectura está siendo diseñada desde el inicio para soportar posteriormente los requisitos asociados a VERI\*FACTU.

Entre los elementos previstos se encuentran:

- registros de facturación de alta;
- registros de anulación;
- subsanaciones;
- encadenamiento de registros;
- huella/hash SHA-256;
- inmutabilidad de registros;
- generación de QR;
- generación de los formatos requeridos;
- comunicación con los servicios de la AEAT;
- almacenamiento de respuestas;
- trazabilidad de envíos;
- detección de incidencias;
- verificación de la cadena de registros.

Los registros de facturación se diseñarán separando:

```text
previous_record_id
```

para el encadenamiento criptográfico, de:

```text
corrects_record_id
```

para representar relaciones de corrección o subsanación.

La implementación definitiva deberá seguir las especificaciones técnicas vigentes publicadas por la AEAT.

---

## 🗺️ Roadmap

### Fase 1 — Infraestructura

- [x] FastAPI
- [x] PostgreSQL
- [x] Docker Compose
- [x] SQLAlchemy
- [x] Alembic
- [x] Pydantic Settings
- [x] Pytest
- [x] Health checks

### Fase 2 — Empresa

- [x] Modelo Business
- [x] Migración
- [x] Schemas
- [x] Repository
- [x] Service
- [x] POST Business
- [x] GET Business
- [x] Tests de API
- [ ] Actualización de Business
- [ ] Listado
- [ ] Gestión completa del dominio

### Fase 3 — Usuarios y autenticación

- [ ] Usuarios
- [ ] Autenticación
- [ ] Hash de contraseñas
- [ ] Autorización
- [ ] Asociación usuario/empresa

### Fase 4 — Productos

- [ ] Modelo Product
- [ ] Impuestos
- [ ] Precios
- [ ] CRUD
- [ ] Tests

### Fase 5 — Clientes

- [ ] Modelo Customer
- [ ] CRUD
- [ ] Validaciones fiscales
- [ ] Tests

### Fase 6 — Facturación

- [ ] Series
- [ ] Numeración
- [ ] Factura completa
- [ ] Factura simplificada
- [ ] Líneas de factura
- [ ] Cálculo de bases e impuestos
- [ ] Totales
- [ ] PDF

### Fase 7 — VERI\*FACTU

- [ ] BillingRecord
- [ ] ALTA
- [ ] ANULACIÓN
- [ ] SUBSANACIÓN
- [ ] Encadenamiento
- [ ] SHA-256
- [ ] Inmutabilidad
- [ ] QR
- [ ] Generación de mensajes AEAT
- [ ] Integración con servicios AEAT
- [ ] Historial de envíos
- [ ] Gestión de respuestas
- [ ] Tests de integridad
- [ ] Tests de concurrencia

### Fase 8 — Frontend

- [ ] React
- [ ] TypeScript
- [ ] Vite
- [ ] Tailwind CSS
- [ ] Login
- [ ] Dashboard
- [ ] Empresas
- [ ] Productos
- [ ] Clientes
- [ ] Facturas
- [ ] Estado VERI\*FACTU

---

## ⚠️ Alcance

VeriFactu App pretende ser una aplicación de facturación ligera.

No se plantea inicialmente como:

- ERP completo;
- sistema de contabilidad integral;
- software de nóminas;
- sistema de conciliación bancaria;
- CRM avanzado;
- sistema de gestión de almacenes múltiples;
- plataforma de comercio electrónico.

El objetivo es mantener un producto pequeño, comprensible y mantenible.

---

## 📄 Licencia

Licencia pendiente de definir.

---

## 👨‍💻 Autor

Desarrollado por **Manuel Ríos Reina**.

Proyecto desarrollado como aplicación práctica y proyecto de portfolio.
