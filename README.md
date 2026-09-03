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

Actualmente se encuentra implementada la infraestructura base del backend, los dominios **Business** y **User** y una primera capa funcional de **autenticación mediante JWT**.

La aplicación permite:

- gestionar empresas;
- gestionar usuarios asociados a empresas;
- almacenar contraseñas mediante Argon2;
- autenticar mediante email y contraseña;
- generar access tokens JWT;
- validar tokens Bearer;
- identificar al usuario autenticado;
- comprobar en cada petición autenticada que el usuario sigue activo;
- comprobar que su empresa sigue activa;
- consultar la identidad del usuario mediante `/auth/me`.

La protección de los endpoints de negocio y las reglas de autorización entre empresas todavía no están implementadas.

### Implementado

- FastAPI configurado.
- PostgreSQL 17 mediante Docker.
- SQLAlchemy 2.
- Psycopg.
- Pydantic.
- Pydantic Settings.
- Variables de entorno.
- Alembic configurado.
- Sistema de migraciones operativo.
- Registro centralizado de modelos SQLAlchemy.
- Patrón Repository.
- Capa Service.
- Control transaccional desde Service.
- Health check de API.
- Health check de PostgreSQL.
- Hash de contraseñas mediante Argon2.
- Verificación de contraseñas.
- Autenticación mediante email y contraseña.
- Generación de JWT mediante PyJWT.
- Validación de JWT.
- Expiración de access tokens.
- Autenticación Bearer mediante `HTTPBearer`.
- Identificación del usuario autenticado.
- Validación del usuario contra PostgreSQL.
- Validación de empresa activa durante autenticación.
- Revocación funcional de acceso mediante estado activo/inactivo.
- Endpoint `/auth/login`.
- Endpoint `/auth/me`.
- Fixtures transaccionales de testing.
- Tests de Repository.
- Tests de Service.
- Tests de seguridad.
- Tests de dependencias de autenticación.
- Tests de integración de API.
- Swagger/OpenAPI mediante FastAPI.

---

## 🏢 Dominio Business

Actualmente se encuentra implementado:

- Modelo `Business`.
- Relación `Business → User`.
- Creación.
- Consulta.
- Listado.
- Actualización parcial.
- Identificador fiscal único.
- Detección previa de identificadores fiscales duplicados.
- Ciclo de vida activo/inactivo.
- Activación.
- Desactivación sin eliminación física.
- API REST del dominio Business.

---

## 👤 Dominio User

Actualmente se encuentra implementado:

- Modelo `User`.
- Asociación obligatoria con `Business`.
- Email globalmente único.
- Validación de direcciones de email.
- Creación.
- Consulta.
- Actualización parcial.
- Listado por empresa a nivel Repository/Service.
- Ciclo de vida activo/inactivo.
- Activación.
- Desactivación.
- Validación de empresa existente.
- Rechazo de creación para empresas inactivas.
- Detección previa de emails duplicados.
- Hash seguro de contraseñas mediante Argon2.
- Verificación de contraseñas.
- Autenticación de usuario.
- Rechazo de usuarios inactivos durante autenticación.
- Rechazo cuando la empresa está inactiva.
- API REST del dominio User.
- Exclusión de `password` y `password_hash` de las respuestas HTTP.

---

## 🔐 Autenticación

Actualmente se encuentra implementado:

- `LoginRequest`.
- `TokenResponse`.
- `AuthService`.
- `POST /auth/login`.
- JWT firmado mediante PyJWT.
- Claims `sub`, `iat` y `exp`.
- Expiración configurable.
- `HTTPBearer`.
- `get_current_user`.
- `GET /auth/me`.
- Validación de usuario y empresa en cada petición autenticada.
- Respuestas `401 Unauthorized` controladas.

---

## 🌐 API implementada

```text
GET   /health
GET   /health/db

POST  /auth/login
GET   /auth/me

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

Actualmente no existe un endpoint global:

```text
GET /users
```

Los usuarios pertenecen a una empresa y el listado HTTP por empresa se expondrá cuando se definan las reglas de autorización correspondientes.

Los endpoints de `Business` y `User` todavía no están protegidos mediante JWT.

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
- PyJWT
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

El backend evita concentrar lógica de negocio y persistencia en los endpoints de FastAPI.

La arquitectura separa responsabilidades:

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
- validar datos de entrada;
- devolver códigos HTTP;
- transformar errores de negocio en respuestas HTTP;
- serializar respuestas públicas.

### Service

Responsable de:

- reglas de negocio;
- coordinación de operaciones;
- control de límites transaccionales;
- coordinación entre repositorios;
- ejecución de `commit`.

Ejemplo de creación de usuario:

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

Ejemplo de autenticación:

```text
LoginRequest
     │
     ▼
AuthService
     │
     ▼
UserService.authenticate_user()
     │
     ├── comprobar usuario
     ├── verificar contraseña
     ├── comprobar usuario activo
     └── comprobar empresa activa
     │
     ▼
create_access_token()
     │
     ▼
TokenResponse
```

### Repository

Responsable exclusivamente del acceso a datos:

- consultas;
- inserciones;
- modificaciones;
- acceso mediante SQLAlchemy.

Los repositories utilizan operaciones como:

```text
flush()
refresh()
```

pero no deciden cuándo realizar el `commit`.

Esto será especialmente importante cuando se implemente el proceso de facturación y VERI\*FACTU, donde varias operaciones deberán formar parte de una única transacción.

---

## 🔐 Arquitectura de autenticación

El flujo de login actual es:

```text
email + password
      │
      ▼
POST /auth/login
      │
      ▼
AuthService
      │
      ▼
UserService.authenticate_user()
      │
      ├── usuario existe
      ├── contraseña correcta
      ├── usuario activo
      └── empresa activa
      │
      ▼
create_access_token()
      │
      ▼
JWT
      │
      ├── sub
      ├── iat
      └── exp
```

El flujo de una petición autenticada es:

```text
Authorization: Bearer <JWT>
            │
            ▼
HTTPBearer
            │
            ▼
get_current_user()
            │
            ▼
decode_access_token()
            │
            ▼
payload["sub"]
            │
            ▼
user_id
            │
            ▼
UserRepository
            │
            ├── usuario existe
            └── usuario activo
            │
            ▼
BusinessRepository
            │
            ├── empresa existe
            └── empresa activa
            │
            ▼
User autenticado
```

---

## 🔑 JWT

Los access tokens se generan mediante:

```text
PyJWT
```

La configuración se obtiene de variables de entorno.

Actualmente los tokens contienen:

```text
sub
iat
exp
```

### `sub`

El claim:

```text
sub
```

contiene el identificador del usuario convertido a `str`.

Se utiliza el identificador interno y no el email porque el ID es estable mientras que el email puede modificarse.

### `iat`

Representa el instante de emisión del token.

### `exp`

Representa el instante de expiración.

Actualmente la duración por defecto es:

```text
30 minutos
```

y puede modificarse mediante configuración.

---

## 🛡️ Validación de access tokens

La validación se realiza mediante:

```text
decode_access_token()
```

El sistema rechaza:

- tokens con firma inválida;
- tokens manipulados;
- tokens expirados;
- valores `sub` inválidos;
- usuarios inexistentes;
- usuarios inactivos;
- empresas inexistentes;
- empresas inactivas.

---

## 🔒 Revocación funcional de acceso

Los JWT son stateless y no se almacenan actualmente en la base de datos.

Sin embargo, un token criptográficamente válido no implica automáticamente que siga concediendo acceso.

En cada petición autenticada:

```text
JWT válido
   │
   ▼
buscar User en PostgreSQL
   │
   ▼
comprobar User.is_active
   │
   ▼
buscar Business
   │
   ▼
comprobar Business.is_active
```

Por tanto:

```text
JWT válido ≠ acceso garantizado
```

Si un usuario es desactivado después de haber obtenido un token, su siguiente petición autenticada devuelve:

```text
401 Unauthorized
```

Lo mismo sucede si se desactiva su empresa.

Esto permite revocar funcionalmente el acceso antes de que expire el JWT.

---

## 🔐 Errores de autenticación

La API evita revelar información innecesaria sobre las cuentas.

Durante el login, casos como:

- usuario inexistente;
- contraseña incorrecta;
- usuario inactivo;
- empresa inactiva;

se transforman externamente en:

```text
401 Unauthorized
```

con:

```json
{
  "detail": "Incorrect email or password"
}
```

y:

```text
WWW-Authenticate: Bearer
```

Durante la validación de un Bearer token se utiliza:

```json
{
  "detail": "Could not validate credentials"
}
```

también con:

```text
WWW-Authenticate: Bearer
```

---

## 👤 Usuario autenticado

La dependencia:

```text
get_current_user()
```

es responsable de identificar al usuario asociado al JWT.

Actualmente valida:

1. existencia de credenciales Bearer;
2. validez del JWT;
3. existencia de `sub`;
4. conversión de `sub` a ID de usuario;
5. existencia del usuario;
6. estado activo del usuario;
7. existencia de su empresa;
8. estado activo de la empresa.

Si todas las comprobaciones son correctas devuelve el objeto:

```text
User
```

que puede ser inyectado posteriormente en endpoints protegidos mediante `Depends`.

---

## 🙋 Endpoint `/auth/me`

El endpoint:

```http
GET /auth/me
```

requiere:

```text
Authorization: Bearer <access_token>
```

Si la autenticación es correcta devuelve `UserRead`.

Ejemplo conceptual:

```json
{
  "id": 1,
  "business_id": 1,
  "email": "admin@example.com",
  "full_name": "Usuario Demo",
  "is_active": true,
  "created_at": "...",
  "updated_at": "..."
}
```

Nunca devuelve:

```text
password
password_hash
```

Si el token es inexistente o inválido:

```text
401 Unauthorized
```

---

## ⚠️ Autenticación no equivale a autorización

Actualmente la aplicación puede identificar correctamente al usuario autenticado.

Sin embargo, todavía no se han implementado las reglas que determinen:

```text
qué recursos puede utilizar ese usuario
```

Por ejemplo, antes de proteger los endpoints existentes será necesario impedir que un usuario perteneciente a:

```text
Business A
```

pueda consultar o modificar datos pertenecientes a:

```text
Business B
```

Por tanto, el siguiente bloque deberá diseñar explícitamente:

- autorización;
- aislamiento entre empresas;
- acceso a recursos propios;
- reglas de administración;
- estrategia de registro/bootstrap inicial.

No se protegerán indiscriminadamente los endpoints sin definir primero estas reglas.

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
│   │   │   ├── dependencies/
│   │   │   │   ├── __init__.py
│   │   │   │   └── auth.py
│   │   │   │
│   │   │   └── routes/
│   │   │       ├── auth.py
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
│   │   │   ├── auth/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── schemas.py
│   │   │   │   └── service.py
│   │   │   │
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
│   │   ├── test_auth_api.py
│   │   ├── test_auth_dependencies.py
│   │   ├── test_auth_service.py
│   │   ├── test_business_api.py
│   │   ├── test_business_repository.py
│   │   ├── test_business_service.py
│   │   ├── test_health.py
│   │   ├── test_security.py
│   │   ├── test_user_api.py
│   │   ├── test_user_repository.py
│   │   └── test_user_service.py
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

La relación es:

```text
Business 1 ─────────── N User
```

El identificador fiscal:

```text
tax_id
```

tiene una restricción de unicidad en PostgreSQL.

La capa Service también detecta duplicados previamente para transformar el caso en:

```text
409 Conflict
```

La restricción de PostgreSQL permanece como garantía final de integridad.

### Ciclo de vida

El ciclo de vida se gestiona mediante:

```text
is_active
```

Las empresas se crean activas y pueden desactivarse y reactivarse.

La desactivación no elimina el registro.

Las operaciones son explícitas:

```text
deactivate_business()
activate_business()
```

Esto permitirá mantener posteriormente las referencias históricas y fiscales.

---

## 👤 Dominio User

`User` representa un usuario asociado a una empresa.

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

Esto permite utilizar:

```text
email + password
```

como credenciales de autenticación.

Las direcciones se validan mediante:

```text
EmailStr
```

La unicidad está protegida mediante PostgreSQL y mediante comprobación previa en Service.

### Contraseñas

Las contraseñas en texto plano únicamente se utilizan como datos de entrada.

Antes de persistir:

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

Ni `password` ni `password_hash` forman parte de:

```text
UserRead
```

### Reglas de creación

Antes de crear un usuario, `UserService` comprueba:

1. que la empresa exista;
2. que esté activa;
3. que el email no esté registrado.

Después genera el hash y persiste el usuario.

### Ciclo de vida

Los usuarios utilizan:

```text
is_active
```

Las operaciones son:

```text
deactivate_user()
activate_user()
```

La contraseña no se modifica mediante `UserUpdate`.

El cambio de contraseña se implementará posteriormente como una operación específica.

---

## 🔐 Variables de entorno

Las credenciales reales y claves criptográficas no deben almacenarse en Git.

El proyecto utiliza:

```text
.env
```

en la raíz del proyecto y excluido mediante `.gitignore`.

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

JWT_SECRET_KEY=change_me
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
```

`JWT_SECRET_KEY` debe sustituirse por una clave aleatoria segura.

Puede generarse mediante:

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

Nunca deben almacenarse secretos reales en el repositorio.

---

## 🗄️ Base de datos

La aplicación utiliza PostgreSQL 17 mediante Docker Compose.

Configuración actual:

```text
Database: verifactu
User:     verifactu
Host:     localhost
Port:     55732
```

El puerto interno del contenedor es:

```text
5432
```

Las tablas implementadas actualmente son:

```text
businesses
users
```

La relación se establece mediante:

```text
users.business_id → businesses.id
```

---

## ⚙️ Instalación del backend

### 1. Clonar

```bash
git clone <repository-url>
cd verifactu-app/backend
```

### 2. Crear entorno virtual

```powershell
python -m venv .venv
```

### 3. Activar

```powershell
.\.venv\Scripts\Activate.ps1
```

### 4. Instalar dependencias

```powershell
pip install -e ".[dev]"
```

### 5. Configurar entorno

Crear:

```text
.env
```

en la raíz tomando como referencia:

```text
.env.example
```

### 6. Iniciar PostgreSQL

Desde la raíz:

```powershell
docker compose up -d
```

Comprobar:

```powershell
docker ps
```

### 7. Migraciones

Desde `backend`:

```powershell
alembic upgrade head
```

### 8. Iniciar FastAPI

```powershell
uvicorn app.main:app --reload
```

API:

```text
http://127.0.0.1:8000
```

Swagger:

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

## 🔐 API Auth

### Login

```http
POST /auth/login
```

Body:

```json
{
  "email": "admin@example.com",
  "password": "password123"
}
```

Respuesta correcta:

```text
200 OK
```

```json
{
  "access_token": "<jwt>",
  "token_type": "bearer"
}
```

Credenciales inválidas:

```text
401 Unauthorized
```

```json
{
  "detail": "Incorrect email or password"
}
```

### Usuario actual

```http
GET /auth/me
```

Header:

```text
Authorization: Bearer <access_token>
```

Respuesta:

```text
200 OK
```

El contenido utiliza el schema:

```text
UserRead
```

Si el token no puede validarse:

```text
401 Unauthorized
```

---

## 🏢 API Business

### Crear

```http
POST /businesses
```

### Listar

```http
GET /businesses
```

### Consultar

```http
GET /businesses/{business_id}
```

### Actualizar

```http
PATCH /businesses/{business_id}
```

### Desactivar

```http
PATCH /businesses/{business_id}/deactivate
```

### Reactivar

```http
PATCH /businesses/{business_id}/activate
```

> Estos endpoints todavía no están protegidos mediante autenticación y autorización.

---

## 👤 API User

### Crear

```http
POST /users
```

### Consultar

```http
GET /users/{user_id}
```

### Actualizar

```http
PATCH /users/{user_id}
```

### Desactivar

```http
PATCH /users/{user_id}/deactivate
```

### Reactivar

```http
PATCH /users/{user_id}/activate
```

La API nunca devuelve:

```text
password
password_hash
```

> Estos endpoints todavía no están protegidos mediante reglas de autorización por empresa.

---

## 🧪 Testing

La suite utiliza Pytest.

Ejecutar:

```powershell
pytest -q
```

Estado actual:

```text
77 passed
```

Existe actualmente un warning conocido relacionado con `Starlette TestClient` y `httpx`.

No bloquea la suite y se abordará de forma independiente.

### Infraestructura

Los tests cubren:

- health check;
- conexión PostgreSQL;
- aislamiento transaccional;
- overrides de `get_db`.

### Business

Se prueba:

- Repository;
- Service;
- API;
- creación;
- consulta;
- listado;
- actualización;
- duplicados;
- activación;
- desactivación;
- IDs inexistentes.

### User

Se prueba:

- Repository;
- Service;
- API;
- creación;
- asociación con Business;
- emails duplicados;
- empresas inexistentes;
- empresas inactivas;
- hashing;
- verificación de password;
- actualización;
- activación;
- desactivación;
- no exposición de credenciales.

### JWT

Se prueba:

- creación de token;
- `sub`;
- `iat`;
- `exp`;
- decodificación;
- manipulación de token;
- expiración.

### AuthService

Se prueba:

- autenticación;
- generación de access token;
- asociación del token al usuario.

### Login API

Se prueba:

- login correcto;
- credenciales incorrectas;
- respuesta `401`;
- `WWW-Authenticate`.

### Dependencias de autenticación

Se prueba `get_current_user` para:

- token válido;
- ausencia de credenciales;
- token inválido;
- `sub` inválido;
- usuario inexistente;
- usuario inactivo;
- empresa inactiva.

### `/auth/me`

Se prueba:

- acceso con Bearer válido;
- respuesta pública del usuario;
- ausencia de password;
- ausencia de password hash;
- ausencia de token;
- token inválido;
- desactivación del usuario después de emitir el token;
- desactivación de la empresa después de emitir el token.

Los tests de persistencia utilizan transacciones aisladas que se revierten tras cada prueba.

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

Head actual:

```text
a23de07e7fb2
```

Consultar:

```powershell
alembic current
```

Crear migración:

```powershell
alembic revision --autogenerate -m "description"
```

Aplicar:

```powershell
alembic upgrade head
```

Las migraciones autogeneradas deben revisarse manualmente antes de aplicarse.

---

## 🧾 VERI\*FACTU

La arquitectura está siendo diseñada para soportar posteriormente los requisitos asociados a VERI\*FACTU.

Elementos previstos:

- registros de facturación de alta;
- registros de anulación;
- subsanaciones;
- encadenamiento;
- huella/hash;
- inmutabilidad;
- QR;
- generación de formatos requeridos;
- comunicación con servicios AEAT;
- almacenamiento de respuestas;
- trazabilidad;
- incidencias;
- verificación de cadena.

Los registros separarán conceptualmente:

```text
previous_record_id
```

para encadenamiento, de:

```text
corrects_record_id
```

para correcciones o subsanaciones.

La implementación definitiva deberá seguir las **especificaciones técnicas vigentes publicadas por la AEAT** en el momento de su desarrollo.

> Una arquitectura preparada para VERI\*FACTU no implica por sí misma conformidad normativa.

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
- [x] POST
- [x] GET
- [x] PATCH
- [x] Listado
- [x] Activación
- [x] Desactivación
- [x] Tests Repository
- [x] Tests Service
- [x] Tests API
- [x] Ciclo de vida

### Fase 3 — Usuarios y autenticación

#### Usuarios

- [x] Modelo User
- [x] Migración
- [x] Relación Business/User
- [x] Schemas
- [x] Repository
- [x] Service
- [x] Creación
- [x] Consulta
- [x] Actualización
- [x] Activación/desactivación
- [x] Validación email
- [x] Email único
- [x] Asociación empresa
- [x] Validación empresa activa
- [x] API
- [x] Tests Repository
- [x] Tests Service
- [x] Tests API

#### Seguridad y autenticación

- [x] Argon2
- [x] Verificación de contraseñas
- [x] Configuración JWT
- [x] Generación JWT
- [x] Validación JWT
- [x] Expiración
- [x] Rechazo de tokens manipulados
- [x] Rechazo de tokens expirados
- [x] Autenticación de credenciales
- [x] AuthService
- [x] Login
- [x] HTTPBearer
- [x] `get_current_user`
- [x] `/auth/me`
- [x] Validación de usuario activo
- [x] Validación de empresa activa
- [x] Revocación funcional
- [x] Tests JWT
- [x] Tests AuthService
- [x] Tests API Auth
- [x] Tests dependencia de autenticación
- [ ] Protección de endpoints Business
- [ ] Protección de endpoints User
- [ ] Autorización por empresa
- [ ] Aislamiento multiempresa
- [ ] Estrategia de bootstrap/registro inicial
- [ ] Normalización robusta de email
- [ ] Hardening frente a enumeración temporal
- [ ] Cambio de contraseña
- [ ] Roles/permisos si el dominio los necesita

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
- [ ] Activación/desactivación
- [ ] Tests

### Fase 6 — Facturación

- [ ] Series
- [ ] Numeración
- [ ] Factura completa
- [ ] Factura simplificada
- [ ] Líneas
- [ ] Bases
- [ ] Impuestos
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
- [ ] Mensajes AEAT
- [ ] Integración AEAT
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
- conciliación bancaria;
- CRM avanzado;
- gestión de múltiples almacenes;
- plataforma de comercio electrónico.

El objetivo es mantener un producto pequeño, comprensible y mantenible.

---

## 📄 Licencia

Licencia pendiente de definir.

---

## 👨‍💻 Autor

Desarrollado por **Manuel Ríos Reina**.

Proyecto desarrollado como aplicación práctica y proyecto de portfolio.
