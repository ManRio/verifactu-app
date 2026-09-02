# VeriFactu App

Aplicación web de facturación ligera orientada a autónomos, pequeños comercios y pequeñas empresas en España, diseñada con una arquitectura preparada para incorporar los requisitos de **VERI\*FACTU**.

> **Estado del proyecto:** en desarrollo.  
> La aplicación todavía **no debe considerarse un sistema VERI\*FACTU conforme**. La integración y validación completa con las especificaciones técnicas vigentes de la AEAT forma parte de fases posteriores del proyecto.

---

## 🎯 Objetivo

El objetivo de VeriFactu App es construir una solución de facturación sencilla para negocios que necesitan gestionar usuarios, productos, clientes y facturas sin recurrir a un ERP o CRM complejo.

El proyecto busca combinar:

- Una interfaz sencilla y moderna.
- Una API REST estructurada.
- Persistencia en PostgreSQL.
- Gestión de usuarios y autenticación segura.
- Gestión segura de facturas y numeración.
- Registros de facturación inmutables.
- Encadenamiento criptográfico.
- Generación de QR.
- Preparación para la comunicación con los servicios de la AEAT.
- Trazabilidad de envíos, errores y correcciones.

El proyecto se desarrolla también como proyecto de portfolio, prestando especial atención a arquitectura, separación de responsabilidades, calidad de código, testing y buenas prácticas.

---

## 🚧 Estado actual

Actualmente se encuentra implementada la infraestructura base del backend y los dominios **Business** y **User**.

La aplicación permite gestionar empresas y usuarios asociados a ellas. Las contraseñas se almacenan mediante hash Argon2 y nunca se persisten ni se devuelven en texto plano.

La autenticación mediante login y tokens todavía no está implementada.

### Implementado

- FastAPI configurado.
- PostgreSQL 17 mediante Docker.
- SQLAlchemy 2.
- Psycopg.
- Pydantic y Pydantic Settings.
- Variables de entorno.
- Alembic configurado.
- Sistema de migraciones operativo.
- Registro centralizado de modelos SQLAlchemy.
- Patrón Repository.
- Capa Service.
- Control transaccional desde la capa Service.
- Endpoint de health check.
- Endpoint de health check de PostgreSQL.
- Fixtures transaccionales de testing.
- Tests de Repository.
- Tests de Service.
- Tests de integración de API.
- Swagger/OpenAPI mediante FastAPI.

### Dominio Business

- Modelo `Business`.
- Relación `Business → User`.
- Creación, consulta, listado y actualización.
- Identificador fiscal único.
- Detección previa de identificadores fiscales duplicados.
- Ciclo de vida activo/inactivo.
- Activación y desactivación sin eliminación física.
- API REST del dominio Business.

### Dominio User

- Modelo `User`.
- Asociación obligatoria con `Business`.
- Email globalmente único.
- Validación de direcciones de email.
- Creación y consulta de usuarios.
- Actualización parcial de email y nombre.
- Listado de usuarios por empresa a nivel de Repository/Service.
- Ciclo de vida activo/inactivo.
- Activación y desactivación sin eliminación física.
- Validación de empresa existente antes de crear un usuario.
- Rechazo de creación de usuarios para empresas inactivas.
- Detección previa de emails duplicados.
- Hash seguro de contraseñas mediante Argon2.
- Verificación de contraseñas preparada para la futura autenticación.
- API REST del dominio User.
- Exclusión de `password` y `password_hash` de las respuestas HTTP.

### API implementada

```text
GET   /health
GET   /health/db

POST  /businesses
GET   /businesses
GET   /businesses/{business_id}
PATCH /businesses/{business_id}
PATCH /businesses/{business_id}/deactivate
PATCH /businesses/{business_id}/activate

POST  /users
GET   /users/{user_id}
PATCH /users/{user_id}
PATCH /users/{user_id}/deactivate
PATCH /users/{user_id}/activate
```

Actualmente no existe un endpoint global `GET /users`. Los usuarios pertenecen a una empresa y el listado por empresa se expondrá cuando se defina el contrato HTTP adecuado y las reglas de autorización.

---

## 🧱 Stack tecnológico

### Backend

- Python 3.13
- FastAPI
- Uvicorn
- Pydantic
- Pydantic Settings
- Email Validator
- SQLAlchemy 2
- Alembic
- Psycopg
- PostgreSQL 17
- pwdlib
- Argon2
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

El backend evita concentrar la lógica de negocio y persistencia en los endpoints de FastAPI.

La arquitectura separa responsabilidades entre distintas capas:

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
- validar los datos de entrada mediante Pydantic;
- devolver códigos HTTP;
- transformar errores de negocio en respuestas HTTP;
- serializar las respuestas públicas de la API.

### Service

Responsable de:

- reglas de negocio;
- coordinación de operaciones;
- control de los límites transaccionales;
- coordinación entre varios repositorios;
- ejecución de `commit` cuando una operación de negocio finaliza correctamente.

Por ejemplo, la creación de un usuario coordina actualmente:

```text
UserService
   │
   ├── BusinessRepository
   │      └── comprobar empresa
   │
   ├── UserRepository
   │      └── comprobar email
   │
   ├── hash_password()
   │      └── Argon2
   │
   └── commit
```

### Repository

Responsable exclusivamente del acceso a datos:

- consultas;
- inserciones;
- modificaciones;
- acceso mediante SQLAlchemy.

Los repositories utilizan operaciones como `flush()` y `refresh()`, pero no deciden cuándo realizar el `commit` de una operación de negocio.

Esta separación será especialmente importante cuando se implemente el proceso de facturación y VERI\*FACTU, donde varias operaciones deberán ejecutarse dentro de una única transacción.

---

## 📁 Estructura actual

```text
verifactu-app/
│
├── backend/
│   ├── alembic/
│   │   ├── versions/
│   │   │   ├── f59baa15a544_initial_migration.py
│   │   │   ├── 4edaea57d404_create_businesses_table.py
│   │   │   ├── e4eb415b0211_add_is_active_to_businesses.py
│   │   │   └── a23de07e7fb2_create_users_table.py
│   │   ├── env.py
│   │   └── script.py.mako
│   │
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/
│   │   │       ├── business.py
│   │   │       └── user.py
│   │   │
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   └── security.py
│   │   │
│   │   ├── db/
│   │   │   ├── base.py
│   │   │   ├── models.py
│   │   │   └── session.py
│   │   │
│   │   ├── domain/
│   │   │   ├── business/
│   │   │   │   ├── model.py
│   │   │   │   ├── repository.py
│   │   │   │   ├── schemas.py
│   │   │   │   └── service.py
│   │   │   │
│   │   │   └── user/
│   │   │       ├── model.py
│   │   │       ├── repository.py
│   │   │       ├── schemas.py
│   │   │       └── service.py
│   │   │
│   │   └── main.py
│   │
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_business_api.py
│   │   ├── test_business_repository.py
│   │   ├── test_business_service.py
│   │   ├── test_user_api.py
│   │   ├── test_user_repository.py
│   │   ├── test_user_service.py
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
- estado activo/inactivo;
- fecha de creación;
- fecha de actualización.

Una empresa puede tener múltiples usuarios asociados.

El identificador fiscal (`tax_id`) tiene una restricción de unicidad en PostgreSQL.

Además, la capa Service detecta previamente los duplicados para poder transformar este caso de negocio en una respuesta controlada:

```text
HTTP 409 Conflict
```

La restricción de PostgreSQL permanece como última garantía de integridad.

### Ciclo de vida

El ciclo de vida de una empresa se gestiona mediante:

```text
is_active
```

Las empresas se crean activas por defecto y pueden desactivarse y reactivarse posteriormente.

La desactivación no elimina físicamente el registro. De esta forma se preserva su identidad y se prepara el dominio para mantener referencias e histórico cuando se incorporen facturas y registros fiscales.

El estado no forma parte de la actualización genérica de `Business`. La activación y desactivación se modelan como operaciones explícitas:

```text
deactivate_business()
activate_business()
```

Esta estrategia evita utilizar una eliminación física como operación habitual y permitirá conservar en el futuro las relaciones históricas y fiscales asociadas a una empresa.

---

## 👤 Dominio User

`User` representa a un usuario de la aplicación asociado a una empresa.

La relación actual es:

```text
Business 1 ─────────── N User
```

Cada usuario pertenece obligatoriamente a una única empresa mediante:

```text
business_id
```

Actualmente almacena:

- identificador;
- empresa asociada;
- email;
- hash de contraseña;
- nombre completo;
- estado activo/inactivo;
- fecha de creación;
- fecha de actualización.

### Email

El email es globalmente único en el MVP.

Esto permitirá posteriormente realizar el login utilizando:

```text
email + password
```

sin necesidad de solicitar también un identificador de empresa.

Las direcciones se validan mediante Pydantic `EmailStr`.

La unicidad está protegida tanto por PostgreSQL como mediante una comprobación previa en la capa Service.

### Contraseñas

Las contraseñas en texto plano únicamente forman parte del schema de entrada:

```text
UserCreate.password
```

Antes de persistir un usuario:

```text
password
   │
   ▼
Argon2
   │
   ▼
password_hash
```

La base de datos almacena exclusivamente:

```text
password_hash
```

El hashing se realiza mediante `pwdlib` utilizando la configuración recomendada basada en Argon2.

Ni `password` ni `password_hash` forman parte de `UserRead`, por lo que no se incluyen en las respuestas HTTP de la API.

### Reglas de creación

Antes de crear un usuario, `UserService` comprueba:

1. que la empresa exista;
2. que la empresa esté activa;
3. que el email no esté registrado.

Solo después se genera el hash de la contraseña y se persiste el usuario.

### Ciclo de vida

Al igual que `Business`, `User` utiliza:

```text
is_active
```

Los usuarios se crean activos y pueden desactivarse y reactivarse sin eliminar físicamente el registro.

Estas operaciones son explícitas:

```text
deactivate_user()
activate_user()
```

`is_active` no forma parte de `UserUpdate`.

La contraseña tampoco se modifica mediante la actualización genérica. Los cambios de contraseña se implementarán posteriormente como una operación específica ligada al sistema de autenticación.

---

## 🔐 Seguridad y autenticación

La infraestructura inicial de seguridad de contraseñas ya está implementada.

Actualmente existe:

```text
app/core/security.py
```

con operaciones para:

```text
hash_password()
verify_password()
```

El algoritmo utilizado es Argon2 mediante `pwdlib`.

### Implementado

- Hash de contraseñas.
- Verificación de contraseñas.
- No persistencia de contraseñas en texto plano.
- No exposición de hashes mediante la API.
- Validación de email.
- Usuarios activos/inactivos.

### Pendiente

Todavía no están implementados:

- endpoint de login;
- autenticación mediante JWT;
- access tokens;
- identificación del usuario autenticado;
- protección de endpoints;
- autorización;
- roles o permisos;
- cambio seguro de contraseña.

Por tanto, la existencia del dominio `User` **no implica todavía que los endpoints estén protegidos mediante autenticación**.

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

Las tablas principales implementadas actualmente son:

```text
businesses
users
```

La relación entre ambas se establece mediante la foreign key:

```text
users.business_id → businesses.id
```

---

## 🔐 Variables de entorno

Las credenciales reales no deben almacenarse en Git.

El proyecto utiliza:

```text
.env
```

en la raíz del proyecto, excluido mediante `.gitignore`.

Para configurar un entorno nuevo se utiliza:

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

Nunca deben almacenarse contraseñas reales, tokens, claves privadas u otros secretos dentro del repositorio.

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

### Listar empresas

```http
GET /businesses
```

Respuesta:

```text
200 OK
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

### Actualizar empresa

```http
PATCH /businesses/{business_id}
```

Permite actualizaciones parciales.

El estado `is_active` no se modifica mediante este endpoint.

Posibles respuestas:

```text
200 OK
404 Not Found
409 Conflict
```

### Desactivar empresa

```http
PATCH /businesses/{business_id}/deactivate
```

La empresa permanece almacenada con:

```json
{
  "is_active": false
}
```

### Reactivar empresa

```http
PATCH /businesses/{business_id}/activate
```

La empresa vuelve a:

```json
{
  "is_active": true
}
```

---

## 👤 API User

### Crear usuario

```http
POST /users
```

Ejemplo:

```json
{
  "business_id": 1,
  "email": "admin@example.com",
  "password": "password123",
  "full_name": "Usuario Demo"
}
```

Si la creación es correcta:

```text
201 Created
```

La respuesta contiene los datos públicos del usuario, pero nunca:

```text
password
password_hash
```

Si el email ya está registrado:

```text
409 Conflict
```

Si la empresa no existe:

```text
404 Not Found
```

Si la empresa está inactiva:

```text
409 Conflict
```

### Consultar usuario

```http
GET /users/{user_id}
```

Posibles respuestas:

```text
200 OK
404 Not Found
```

### Actualizar usuario

```http
PATCH /users/{user_id}
```

Actualmente permite modificar parcialmente:

- email;
- nombre completo.

No permite modificar mediante este endpoint:

- `business_id`;
- `password`;
- `password_hash`;
- `is_active`.

Si el nuevo email pertenece a otro usuario:

```text
409 Conflict
```

### Desactivar usuario

```http
PATCH /users/{user_id}/deactivate
```

El usuario permanece almacenado con:

```json
{
  "is_active": false
}
```

### Reactivar usuario

```http
PATCH /users/{user_id}/activate
```

El usuario vuelve a:

```json
{
  "is_active": true
}
```

---

## 🧪 Testing

La suite utiliza Pytest.

Ejecutar todos los tests:

```powershell
pytest -q
```

Estado actual:

```text
54 passed
```

Los tests cubren actualmente:

### Infraestructura

- health check de FastAPI;
- conexión con PostgreSQL;
- aislamiento transaccional de pruebas.

### Business

- creación mediante Repository;
- búsqueda por ID;
- búsqueda por identificador fiscal;
- actualización parcial;
- listado;
- creación mediante Service;
- consulta mediante Service;
- actualización mediante Service;
- listado mediante Service;
- rechazo de identificadores fiscales duplicados;
- activación y desactivación;
- comportamiento ante IDs inexistentes;
- creación mediante API (`201 Created`);
- consulta y listado mediante API (`200 OK`);
- actualización mediante API (`200 OK`);
- rechazo de duplicados mediante API (`409 Conflict`);
- activación y desactivación mediante API;
- respuestas `404 Not Found`.

### User

- creación mediante Repository;
- búsqueda por ID;
- búsqueda por email;
- listado por empresa;
- actualización mediante Repository;
- creación mediante Service;
- asociación con una empresa;
- rechazo de empresas inexistentes;
- rechazo de empresas inactivas;
- rechazo de emails duplicados;
- hashing de contraseña;
- verificación del hash;
- actualización mediante Service;
- rechazo de emails duplicados durante actualización;
- activación y desactivación;
- comportamiento ante IDs inexistentes;
- creación mediante API (`201 Created`);
- consulta mediante API (`200 OK`);
- actualización mediante API (`200 OK`);
- rechazo de emails duplicados mediante API (`409 Conflict`);
- rechazo de empresa inexistente mediante API (`404 Not Found`);
- activación y desactivación mediante API;
- no exposición de `password`;
- no exposición de `password_hash`.

Los tests de persistencia utilizan transacciones aisladas que se revierten al terminar cada prueba para evitar contaminar la base de desarrollo.

Los tests de integración utilizan `FastAPI TestClient` y sobrescriben temporalmente `get_db` para utilizar la misma sesión aislada.

Existe actualmente un warning conocido relacionado con la integración entre `Starlette TestClient` y `httpx`. No bloquea la ejecución de la suite y se abordará de forma independiente.

---

## 🗃️ Migraciones

Alembic gestiona el esquema de PostgreSQL.

Migraciones actuales:

```text
f59baa15a544  initial migration
4edaea57d404  create businesses table
e4eb415b0211  add is_active to businesses
a23de07e7fb2  create users table
```

La revisión actual de la base de datos es:

```text
a23de07e7fb2 (head)
```

Consultar migración actual:

```powershell
alembic current
```

Crear una nueva migración:

```powershell
alembic revision --autogenerate -m "description"
```

Aplicar migraciones:

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
- huella/hash;
- inmutabilidad de registros;
- generación de QR;
- generación de los formatos requeridos;
- comunicación con los servicios de la AEAT;
- almacenamiento de respuestas;
- trazabilidad de envíos;
- detección de incidencias;
- verificación de la cadena de registros.

Los registros de facturación se diseñarán separando conceptualmente:

```text
previous_record_id
```

para el encadenamiento de registros, de:

```text
corrects_record_id
```

para representar relaciones de corrección o subsanación.

La implementación definitiva de formatos, campos, algoritmos, reglas de encadenamiento, QR y comunicación deberá seguir las **especificaciones técnicas vigentes publicadas por la AEAT** en el momento de su implementación.

> La arquitectura preparada para VERI\*FACTU no equivale por sí misma a conformidad normativa.

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
- [x] Migraciones
- [x] Schemas
- [x] Repository
- [x] Service
- [x] POST Business
- [x] GET Business
- [x] PATCH Business
- [x] Listado
- [x] Activación y desactivación
- [x] Tests de Repository
- [x] Tests de Service
- [x] Tests de API
- [x] Gestión del ciclo de vida

### Fase 3 — Usuarios y autenticación

#### Usuarios

- [x] Modelo User
- [x] Migración de usuarios
- [x] Relación Business/User
- [x] Schemas
- [x] Repository
- [x] Service
- [x] Creación de usuarios
- [x] Consulta de usuarios
- [x] Actualización de usuarios
- [x] Activación y desactivación
- [x] Validación de email
- [x] Email único
- [x] Asociación usuario/empresa
- [x] Validación de empresa activa
- [x] API User
- [x] Tests de Repository
- [x] Tests de Service
- [x] Tests de API

#### Seguridad y autenticación

- [x] Hash de contraseñas con Argon2
- [x] Verificación de contraseñas
- [ ] Login
- [ ] JWT
- [ ] Usuario autenticado
- [ ] Protección de endpoints
- [ ] Autorización
- [ ] Cambio de contraseña
- [ ] Roles/permisos si los requisitos del dominio los necesitan

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
- [ ] Activación y desactivación
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
- [ ] Huella/hash según especificación vigente
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

El objetivo es mantener un producto pequeño, comprensible y mantenible, evitando incorporar complejidad que no sea necesaria para el dominio de facturación.

---

## 📄 Licencia

Licencia pendiente de definir.

---

## 👨‍💻 Autor

Desarrollado por **Manuel Ríos Reina**.

Proyecto desarrollado como aplicación práctica y proyecto de portfolio.
