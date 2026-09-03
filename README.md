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

Actualmente se encuentra implementada la infraestructura base del backend, los dominios **Business** y **User** y la primera fase del sistema de **autenticación mediante JWT**.

La aplicación permite gestionar empresas y usuarios asociados a ellas. Las contraseñas se almacenan mediante hash Argon2 y nunca se persisten ni se devuelven en texto plano.

También se encuentra implementado el login mediante email y contraseña. Cuando las credenciales son válidas y tanto el usuario como su empresa están activos, la API genera un access token JWT firmado.

La identificación del usuario autenticado a partir del Bearer token, la protección de endpoints y las reglas de autorización todavía están pendientes.

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
- Hash de contraseñas mediante Argon2.
- Verificación de contraseñas.
- Autenticación mediante email y contraseña.
- Generación y validación de JWT mediante PyJWT.
- Expiración de access tokens.
- Rechazo de tokens manipulados o expirados.
- Endpoint de login.
- Fixtures transaccionales de testing.
- Tests de Repository.
- Tests de Service.
- Tests de seguridad.
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
- Verificación de contraseñas.
- Autenticación mediante email y contraseña.
- Rechazo de autenticación de usuarios inactivos.
- Rechazo de autenticación cuando la empresa está inactiva.
- API REST del dominio User.
- Exclusión de `password` y `password_hash` de las respuestas HTTP.

### Autenticación

- Schemas específicos de autenticación.
- `AuthService`.
- Login mediante email y contraseña.
- Access tokens JWT.
- Firma mediante clave secreta configurable.
- Algoritmo JWT configurable.
- Expiración configurable.
- Claim `sub` asociado al identificador del usuario.
- Claims `iat` y `exp`.
- Validación criptográfica de tokens.
- Rechazo de tokens manipulados.
- Rechazo de tokens expirados.
- Respuesta genérica ante errores de autenticación.
- Cabecera `WWW-Authenticate: Bearer` en respuestas `401`.

### API implementada

```text
GET   /health
GET   /health/db

POST  /auth/login

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

Los endpoints de Business y User todavía no están protegidos mediante JWT. La autenticación ya permite emitir tokens, pero la identificación del usuario actual y la autorización de acceso a recursos se implementarán en los siguientes pasos.

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

La autenticación se mantiene separada del CRUD de usuarios mediante `AuthService`:

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

Esto permite realizar el login utilizando:

```text
email + password
```

sin necesidad de solicitar también un identificador de empresa.

Las direcciones se validan mediante Pydantic `EmailStr`.

La unicidad está protegida tanto por PostgreSQL como mediante una comprobación previa en la capa Service.

### Contraseñas

Las contraseñas en texto plano únicamente forman parte de los datos de entrada durante la creación de usuarios y el proceso de login.

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

### Autenticación de credenciales

`UserService` incorpora la validación de credenciales mediante:

```text
authenticate_user()
```

Durante la autenticación se comprueba:

1. que el usuario exista;
2. que la contraseña sea válida;
3. que el usuario esté activo;
4. que la empresa asociada exista;
5. que la empresa esté activa.

Un email inexistente y una contraseña incorrecta se tratan como credenciales inválidas, evitando exponer innecesariamente la existencia de cuentas mediante la respuesta HTTP.

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

La primera fase del sistema de autenticación está implementada.

La seguridad de contraseñas y JWT se concentra principalmente en:

```text
app/core/security.py
```

Actualmente proporciona:

```text
hash_password()
verify_password()
create_access_token()
decode_access_token()
```

### Contraseñas

Las contraseñas se protegen mediante Argon2 utilizando `pwdlib`.

Se garantiza que:

- la contraseña en texto plano no se persiste;
- el hash no se devuelve mediante la API;
- la contraseña se verifica contra el hash almacenado durante el login.

### JWT

Los access tokens se generan mediante `PyJWT`.

Actualmente incluyen:

```text
sub
iat
exp
```

El claim:

```text
sub
```

contiene el identificador del usuario convertido a `str`.

Se utiliza el identificador interno y no el email porque el identificador es estable mientras que el email puede modificarse.

La duración del token y los parámetros criptográficos se obtienen de la configuración de la aplicación.

El sistema valida la firma y la expiración al decodificar un token.

Los tokens manipulados o expirados son rechazados.

### Login

El endpoint:

```http
POST /auth/login
```

recibe JSON:

```json
{
  "email": "admin@example.com",
  "password": "password123"
}
```

Si las credenciales son válidas y tanto el usuario como su empresa están activos:

```json
{
  "access_token": "<jwt>",
  "token_type": "bearer"
}
```

El access token utiliza el identificador del usuario como `sub`.

Ante un fallo de autenticación se devuelve una respuesta genérica:

```text
401 Unauthorized
```

con:

```json
{
  "detail": "Incorrect email or password"
}
```

y la cabecera:

```text
WWW-Authenticate: Bearer
```

La respuesta HTTP no distingue entre:

- usuario inexistente;
- contraseña incorrecta;
- usuario inactivo;
- empresa inexistente;
- empresa inactiva.

### Implementado

- Hash de contraseñas mediante Argon2.
- Verificación de contraseñas.
- No persistencia de contraseñas en texto plano.
- No exposición de hashes mediante la API.
- Validación de email.
- Usuarios activos/inactivos.
- Autenticación de credenciales.
- Validación de empresa activa durante el login.
- Generación de JWT.
- Firma de JWT.
- Expiración de access tokens.
- Claims `sub`, `iat` y `exp`.
- Validación de JWT.
- Rechazo de tokens manipulados.
- Rechazo de tokens expirados.
- Endpoint de login.
- Respuestas de autenticación que evitan revelar información innecesaria sobre las cuentas.

### Pendiente

Todavía no están implementados:

- identificación del usuario autenticado mediante Bearer token;
- `get_current_user`;
- protección de endpoints;
- autorización por empresa;
- aislamiento de recursos entre empresas;
- roles o permisos;
- cambio seguro de contraseña;
- refresh tokens, si posteriormente resultan necesarios.

Por tanto, disponer de login y emisión de JWT **todavía no implica que los endpoints de Business y User estén protegidos**.

---

## 🔑 Flujo de autenticación actual

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
JWT firmado
      │
      ├── sub = user.id
      ├── iat
      └── exp
      │
      ▼
TokenResponse
```

El siguiente paso del sistema de autenticación será implementar el flujo inverso para las peticiones protegidas:

```text
Authorization: Bearer <token>
            │
            ▼
validar y decodificar JWT
            │
            ▼
obtener user_id desde sub
            │
            ▼
consultar usuario
            │
            ▼
validar usuario y empresa
            │
            ▼
usuario autenticado
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

Las credenciales reales y claves criptográficas no deben almacenarse en Git.

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

JWT_SECRET_KEY=change_me
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
```

`JWT_SECRET_KEY` debe sustituirse en el entorno real por una clave aleatoria segura.

La clave real utilizada para firmar tokens nunca debe almacenarse en el repositorio.

Nunca deben almacenarse contraseñas reales, tokens, claves privadas u otros secretos dentro de Git.

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

Es necesario configurar tanto PostgreSQL como una clave JWT segura.

Puede generarse una clave aleatoria para desarrollo mediante Python:

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

El valor generado debe almacenarse únicamente en `.env`:

```env
JWT_SECRET_KEY=<clave-generada>
```

No debe copiarse al repositorio ni compartirse públicamente.

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

Si la autenticación es correcta:

```text
200 OK
```

Respuesta:

```json
{
  "access_token": "<jwt>",
  "token_type": "bearer"
}
```

El JWT contiene el identificador del usuario en el claim:

```text
sub
```

Si las credenciales no son válidas o el usuario o su empresa no pueden autenticarse:

```text
401 Unauthorized
```

Respuesta:

```json
{
  "detail": "Incorrect email or password"
}
```

La respuesta incluye:

```text
WWW-Authenticate: Bearer
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

> Los endpoints de Business todavía no requieren autenticación. La protección y las reglas de autorización por empresa forman parte de la siguiente fase del sistema de seguridad.

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

> Los endpoints de User todavía no requieren autenticación. La futura capa de autorización deberá impedir el acceso arbitrario a usuarios pertenecientes a otras empresas.

---

## 🧪 Testing

La suite utiliza Pytest.

Ejecutar todos los tests:

```powershell
pytest -q
```

Estado actual:

```text
65 passed
```

Existe actualmente un warning conocido relacionado con `Starlette TestClient` y `httpx`. No bloquea la ejecución de la suite y se abordará de forma independiente.

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

### Seguridad JWT

- creación de access tokens;
- inclusión del usuario en `sub`;
- inclusión de `iat`;
- inclusión de `exp`;
- decodificación de tokens válidos;
- rechazo de tokens manipulados;
- rechazo de tokens expirados.

### Autenticación

- autenticación correcta mediante email y contraseña;
- rechazo de contraseña incorrecta;
- rechazo de email inexistente;
- rechazo de usuario inactivo;
- rechazo de empresa inactiva;
- generación de access token desde `AuthService`;
- asociación del `sub` del token con el usuario autenticado;
- login mediante API;
- respuesta `200 OK` para credenciales válidas;
- respuesta `401 Unauthorized` para credenciales inválidas;
- respuesta genérica para evitar revelar la existencia de cuentas;
- cabecera `WWW-Authenticate: Bearer`.

Los tests de persistencia utilizan transacciones aisladas que se revierten al terminar cada prueba para evitar contaminar la base de desarrollo.

Los tests de integración utilizan `FastAPI TestClient` y sobrescriben temporalmente `get_db` para utilizar la misma sesión aislada.

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
- [x] Configuración JWT mediante variables de entorno
- [x] Generación de JWT
- [x] Validación de JWT
- [x] Expiración de access tokens
- [x] Rechazo de tokens manipulados
- [x] Rechazo de tokens expirados
- [x] Autenticación de credenciales
- [x] Validación de usuario activo durante login
- [x] Validación de empresa activa durante login
- [x] AuthService
- [x] Endpoint de login
- [x] Tests de seguridad JWT
- [x] Tests de AuthService
- [x] Tests de API Auth
- [ ] Usuario autenticado (`get_current_user`)
- [ ] Bearer authentication en endpoints protegidos
- [ ] Protección de endpoints
- [ ] Autorización por empresa
- [ ] Aislamiento de recursos entre empresas
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
