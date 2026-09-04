# VeriFactu App

Aplicación web de facturación orientada a pequeños negocios y autónomos, desarrollada como proyecto de portfolio con una arquitectura preparada para incorporar los requisitos de **VERI\*FACTU**.

El objetivo es construir una solución ligera y mantenible para negocios que necesitan gestionar productos, clientes y facturas sin recurrir a un ERP o CRM de gran tamaño.

> [!IMPORTANT]
> Este proyecto está actualmente en desarrollo y **no debe considerarse todavía una implementación conforme con VERI\*FACTU**.
>
> La integración definitiva deberá implementarse y validarse contra las especificaciones técnicas vigentes de la AEAT.

---

## Estado actual

El proyecto se encuentra en una fase de desarrollo **backend-first**.

Actualmente están implementadas las bases de:

- configuración del backend;
- conexión con PostgreSQL;
- migraciones con Alembic;
- dominio de empresas;
- ciclo de vida de empresas;
- dominio de usuarios;
- relación Business → Users;
- creación y actualización de usuarios;
- activación y desactivación de usuarios;
- hashing seguro de contraseñas;
- autenticación de usuarios;
- generación y validación de JWT;
- endpoint de login;
- resolución del usuario autenticado mediante Bearer Token;
- endpoint `/auth/me`;
- revocación funcional de acceso para usuarios o empresas inactivas;
- normalización de direcciones de email;
- búsquedas y autenticación de email sin depender de mayúsculas/minúsculas;
- unicidad case-insensitive de email en PostgreSQL;
- fundamentos de autorización y aislamiento por tenant;
- protección inicial del acceso a empresas por tenant.

La suite automatizada cuenta actualmente con:

```text
91 passed
```

Existe además un warning conocido relacionado con la integración entre `Starlette TestClient` y `httpx`. Actualmente no afecta al funcionamiento ni a los tests del proyecto y se tratará como deuda técnica separada.

---

## Objetivo del proyecto

VeriFactu App pretende cubrir las necesidades básicas de facturación de pequeños negocios mediante una interfaz sencilla y una arquitectura preparada para evolucionar hacia una integración completa con VERI\*FACTU.

El MVP contempla:

- gestión de cuenta y negocio;
- gestión de usuarios;
- autenticación y autorización;
- gestión de productos;
- gestión de clientes;
- impuestos y precios;
- facturas completas y simplificadas;
- numeración de facturas;
- generación de PDF;
- generación de QR;
- generación de registros de facturación;
- encadenamiento de registros;
- cálculo de hash según la especificación aplicable;
- registros de alta;
- anulación;
- rectificación y subsanación;
- envío de registros a la AEAT;
- almacenamiento de respuestas e incidencias;
- verificación de la cadena de registros;
- dashboard básico de facturación y estado VERI\*FACTU.

---

## Fuera del alcance inicial

El objetivo no es construir un ERP completo.

Quedan fuera del MVP:

- contabilidad completa;
- conciliación bancaria;
- nóminas;
- gestión avanzada de proveedores;
- compras;
- múltiples almacenes;
- TPV físico;
- comercio electrónico;
- CRM avanzado;
- analítica compleja;
- multiidioma;
- multimoneda;
- soporte inicial para todos los regímenes especiales de IVA.

---

# Stack tecnológico

## Backend

- Python 3.13
- FastAPI
- SQLAlchemy 2
- PostgreSQL
- Alembic
- Pydantic
- Pydantic Settings
- Psycopg
- PyJWT
- pwdlib
- Argon2
- Pytest
- Ruff

## Infraestructura de desarrollo

- Docker
- Docker Compose

## Frontend previsto

El frontend se desarrollará en una fase posterior.

Stack previsto:

- React
- TypeScript
- Vite
- Tailwind CSS

Se valorará además el uso de:

- TanStack Query
- React Hook Form
- Zod

---

# Arquitectura

El backend sigue una separación por responsabilidades.

```text
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

- rutas;
- parámetros;
- códigos de estado;
- serialización;
- dependencias;
- autenticación;
- autorización HTTP.

### Service

Responsable de:

- reglas de negocio;
- validaciones de dominio;
- coordinación entre repositorios;
- límites de transacción.

### Repository

Responsable exclusivamente del acceso a datos.

Los repositorios utilizan:

```python
flush()
refresh()
```

pero no realizan `commit()`.

El límite de la transacción pertenece a la capa de servicio.

Esta decisión es especialmente importante para futuras operaciones de facturación y VERI\*FACTU, donde varias operaciones deberán ejecutarse de forma atómica.

---

# Estructura actual

```text
verifactu-app/
│
├── .env
├── .env.example
├── .gitignore
├── docker-compose.yml
├── README.md
│
└── backend/
    │
    ├── alembic/
    │   ├── env.py
    │   └── versions/
    │       ├── f59baa15a544_initial_migration.py
    │       ├── 4edaea57d404_create_businesses_table.py
    │       ├── e4eb415b0211_add_is_active_to_businesses.py
    │       ├── a23de07e7fb2_create_users_table.py
    │       └── 666e0bbbf372_enforce_case_insensitive_user_email_.py
    │
    ├── app/
    │   ├── api/
    │   │   ├── dependencies/
    │   │   │   ├── auth.py
    │   │   │   ├── authorization.py
    │   │   │   └── tenant.py
    │   │   └── routes/
    │   │       ├── auth.py
    │   │       ├── business.py
    │   │       └── user.py
    │   │
    │   ├── core/
    │   │   ├── config.py
    │   │   ├── identity.py
    │   │   └── security.py
    │   │
    │   ├── db/
    │   │   ├── base.py
    │   │   ├── models.py
    │   │   └── session.py
    │   │
    │   ├── domain/
    │   │   ├── auth/
    │   │   │   ├── schemas.py
    │   │   │   └── service.py
    │   │   │
    │   │   ├── business/
    │   │   │   ├── model.py
    │   │   │   ├── repository.py
    │   │   │   ├── schemas.py
    │   │   │   └── service.py
    │   │   │
    │   │   └── user/
    │   │       ├── model.py
    │   │       ├── repository.py
    │   │       ├── schemas.py
    │   │       └── service.py
    │   │
    │   └── main.py
    │
    ├── tests/
    │   ├── conftest.py
    │   ├── test_auth_api.py
    │   ├── test_authorization_dependencies.py
    │   ├── test_business_api.py
    │   ├── test_business_repository.py
    │   ├── test_business_service.py
    │   ├── test_health.py
    │   ├── test_identity.py
    │   ├── test_security.py
    │   ├── test_tenant_dependencies.py
    │   ├── test_user_api.py
    │   ├── test_user_repository.py
    │   └── test_user_service.py
    │
    ├── alembic.ini
    └── pyproject.toml
```

---

# Configuración

La configuración se gestiona mediante `pydantic-settings`.

Las variables de entorno se encuentran en un archivo `.env` situado en la raíz del proyecto.

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

El archivo `.env` no debe incluirse en Git.

El repositorio contiene `.env.example` como referencia para configurar un entorno local.

---

# Base de datos

El proyecto utiliza PostgreSQL.

Durante el desarrollo se ejecuta mediante Docker Compose.

Configuración actual:

```text
Database: verifactu
User: verifactu
Container: verifactu-postgres
Host port: 55732
Container port: 5432
```

Para iniciar PostgreSQL:

```powershell
docker compose up -d
```

Para comprobar el estado:

```powershell
docker compose ps
```

---

# Alembic

Alembic gestiona la evolución del esquema de base de datos.

Migraciones actuales:

```text
f59baa15a544_initial_migration.py
4edaea57d404_create_businesses_table.py
e4eb415b0211_add_is_active_to_businesses.py
a23de07e7fb2_create_users_table.py
666e0bbbf372_enforce_case_insensitive_user_email_.py
```

La revisión actual es:

```text
666e0bbbf372 (head)
```

Para aplicar las migraciones:

```powershell
alembic upgrade head
```

Para comprobar la revisión:

```powershell
alembic current
```

Para comprobar que los modelos SQLAlchemy y el esquema gestionado por Alembic están sincronizados:

```powershell
alembic check
```

Estado actual:

```text
No new upgrade operations detected.
```

---

# Dominio Business

Una empresa representa el tenant principal de la aplicación.

Campos actuales:

```text
id
legal_name
tax_id
trade_name
address
postal_code
city
province
country_code
is_active
created_at
updated_at
```

Una empresa puede tener múltiples usuarios.

```text
Business
   │
   └── Users
```

El ciclo de vida utiliza desactivación lógica.

No se realiza borrado físico ordinario porque la futura información fiscal y de facturación debe conservar trazabilidad.

---

# Dominio User

Cada usuario pertenece exactamente a una empresa mediante:

```text
business_id
```

Campos actuales:

```text
id
business_id
email
password_hash
full_name
is_active
created_at
updated_at
```

Las contraseñas nunca se almacenan en texto plano.

El hashing se realiza mediante Argon2 utilizando `pwdlib`.

Los usuarios pueden:

- crearse;
- consultarse;
- actualizarse;
- activarse;
- desactivarse;
- autenticarse.

---

# Normalización e identidad del email

El email funciona como identificador global de usuario para el MVP.

Antes de persistirlo o utilizarlo en operaciones de identidad se normaliza mediante:

```python
email.strip().lower()
```

La normalización se aplica actualmente en:

- creación de usuario;
- actualización del email;
- búsqueda mediante `UserService.get_by_email()`;
- autenticación.

Por tanto, operaciones como:

```text
user@example.com
USER@EXAMPLE.COM
User@Example.Com
```

se consideran equivalentes dentro de la aplicación.

La base de datos refuerza esta regla mediante un índice funcional único de PostgreSQL:

```sql
lower(email)
```

La estructura lógica es:

```text
ix_users_email
    índice normal
    unique = false

uq_users_email_lower
    índice funcional
    lower(email)
    unique = true
```

El modelo SQLAlchemy declara explícitamente este índice funcional, manteniendo sincronizados:

```text
SQLAlchemy
Alembic
PostgreSQL
```

`alembic check` confirma actualmente que no existen operaciones de actualización pendientes.

---

# Autenticación

La autenticación utiliza JWT.

Configuración actual:

```text
Algorithm: HS256
Access token expiration: 30 minutes
```

Los tokens incluyen:

```text
sub
iat
exp
```

`sub` contiene el identificador del usuario como string.

El endpoint de login recibe JSON.

Por esta razón se utiliza `HTTPBearer` para resolver las credenciales de las peticiones autenticadas, en lugar de anunciar un flujo OAuth2 Password basado en formulario.

---

# Resolución del usuario autenticado

La dependencia `get_current_user`:

1. obtiene el Bearer Token;
2. valida el JWT;
3. obtiene `sub`;
4. convierte `sub` al ID del usuario;
5. consulta el usuario en PostgreSQL;
6. comprueba que el usuario existe;
7. comprueba que está activo;
8. comprueba que su empresa existe;
9. comprueba que la empresa está activa.

Esto significa que un JWT válido no garantiza por sí solo acceso permanente.

Si el usuario o su empresa son desactivados, las siguientes peticiones autenticadas dejan de ser válidas aunque el token todavía no haya expirado.

---

# Autorización y aislamiento por tenant

La autenticación responde a:

```text
¿Quién es el usuario?
```

La autorización debe responder a:

```text
¿Puede este usuario acceder a este recurso?
```

El tenant autenticado se deriva de:

```python
current_user.business_id
```

La aplicación incorpora una dependencia específica para obtener el identificador de la empresa autenticada:

```text
get_current_business_id
```

También existe una comprobación central:

```text
ensure_same_business
```

Su objetivo es impedir que un usuario acceda a recursos pertenecientes a otra empresa.

Cuando se intenta acceder a un recurso de otro tenant se utiliza:

```text
404 Not Found
```

en lugar de revelar mediante un `403 Forbidden` que dicho recurso existe.

Actualmente se ha iniciado la aplicación de este modelo al endpoint:

```text
GET /businesses/{business_id}
```

Un usuario autenticado puede consultar su propia empresa, pero no una empresa perteneciente a otro tenant.

La protección del resto de endpoints de Business y User se realizará progresivamente durante la siguiente fase.

---

# Endpoints actuales

## Health

```text
GET /health
```

## Auth

```text
POST /auth/login
GET  /auth/me
```

## Businesses

```text
POST  /businesses
GET   /businesses
GET   /businesses/{business_id}
PATCH /businesses/{business_id}
PATCH /businesses/{business_id}/deactivate
PATCH /businesses/{business_id}/activate
```

Actualmente:

```text
GET /businesses/{business_id}
```

ya aplica autenticación y comprobación de tenant.

El resto de endpoints de Business todavía debe integrarse en el modelo definitivo de autorización/bootstrap.

## Users

Las operaciones del dominio User están implementadas, pero la protección completa de sus endpoints por tenant forma parte de la siguiente fase de autorización.

---

# Seguridad

Actualmente están implementadas las siguientes medidas:

- contraseñas almacenadas mediante hash;
- Argon2;
- JWT firmados;
- expiración de access tokens;
- validación de firma;
- rechazo de tokens expirados;
- rechazo de tokens manipulados;
- comprobación del usuario contra la base de datos en cada petición autenticada;
- rechazo de usuarios inactivos;
- rechazo de usuarios pertenecientes a empresas inactivas;
- errores HTTP genéricos durante autenticación;
- mitigación de diferencias temporales para usuarios inexistentes mediante verificación Argon2 ficticia;
- normalización consistente del email;
- unicidad case-insensitive del email en PostgreSQL;
- aislamiento inicial por tenant.

Todavía quedan medidas de seguridad por implementar, entre ellas:

- protección completa de endpoints Business;
- protección completa de endpoints User;
- aislamiento cross-tenant completo;
- flujo seguro de registro/bootstrap;
- estrategia futura de revocación de sesiones/tokens si fuese necesaria.

---

# Tests

Los tests utilizan `pytest`.

La fixture de base de datos abre una transacción por test y realiza rollback al finalizar, manteniendo aislados los casos de prueba.

Para ejecutar toda la suite:

```powershell
pytest -q
```

Estado actual:

```text
91 passed, 1 warning
```

El warning conocido es:

```text
StarletteDeprecationWarning:
Using `httpx` with `starlette.testclient` is deprecated;
install `httpx2` instead.
```

No bloquea actualmente el desarrollo y se resolverá de forma separada.

La suite cubre actualmente, entre otros:

- health endpoint;
- repositorio Business;
- servicio Business;
- API Business;
- ciclo de vida Business;
- repositorio User;
- servicio User;
- API User;
- hashing de contraseñas;
- generación y decodificación de JWT;
- tokens manipulados;
- tokens expirados;
- login;
- credenciales incorrectas;
- usuarios inactivos;
- empresas inactivas;
- `/auth/me`;
- resolución del usuario autenticado;
- normalización de email;
- autenticación con distinta capitalización del email;
- actualización normalizada del email;
- búsqueda case-insensitive mediante `UserService`;
- rechazo de emails duplicados con distinta capitalización;
- resolución del tenant autenticado;
- autorización same-business;
- rechazo de acceso cross-tenant;
- acceso autenticado a la empresa propia.

---

# Ruff

Ruff se utiliza para análisis estático y mantenimiento de calidad del código.

Puede ejecutarse mediante:

```powershell
ruff check .
```

Actualmente existe deuda de lint heredada en algunos archivos históricos y migraciones generadas por Alembic.

Además, la regla `B008` detecta el patrón:

```python
Depends(...)
```

utilizado de forma habitual por FastAPI en parámetros de dependencias.

Esta configuración se revisará en una tarea de tooling independiente para evitar mezclar cambios de estilo globales con cambios funcionales.

No se utiliza actualmente un `ruff check . --fix` indiscriminado sobre todo el proyecto.

---

# Desarrollo local

Desde la raíz del proyecto:

```powershell
.\backend\.venv\Scripts\Activate.ps1
```

O desde `backend`:

```powershell
.\.venv\Scripts\Activate.ps1
```

Iniciar PostgreSQL:

```powershell
docker compose up -d
```

Entrar en backend:

```powershell
cd backend
```

Aplicar migraciones:

```powershell
alembic upgrade head
```

Comprobar sincronización del esquema:

```powershell
alembic check
```

Ejecutar tests:

```powershell
pytest -q
```

Arrancar FastAPI en desarrollo:

```powershell
uvicorn app.main:app --reload
```

---

# Principios de diseño para VERI\*FACTU

La futura implementación de registros de facturación seguirá varios principios importantes.

## Inmutabilidad

Los registros fiscales emitidos no deberán modificarse como registros ordinarios.

Las correcciones deberán representarse mediante nuevos registros relacionados con los anteriores.

## Tipos de registro previstos

```text
ALTA
ANULACION
SUBSANACION
```

## Encadenamiento

Los registros deberán mantener relación con el registro anterior.

La arquitectura prevista contempla:

```text
previous_record_id
```

para representar la cadena.

## Correcciones

Las relaciones de corrección podrán utilizar:

```text
corrects_record_id
```

sin sobrescribir el registro original.

## Hash

El hash se calculará exactamente sobre los campos y con el procedimiento definidos por la especificación técnica aplicable.

No se asumirá que el hash corresponde simplemente al XML completo.

## Envíos

Los registros de facturación y los intentos de envío se modelarán por separado.

Está prevista una entidad similar a:

```text
VerifactuSubmission
```

para conservar:

- fecha del intento;
- estado;
- respuesta;
- errores;
- reintentos.

## Concurrencia

La numeración de facturas y el encadenamiento deberán ser seguros frente a concurrencia.

Se utilizarán transacciones PostgreSQL y, cuando sea necesario, mecanismos de bloqueo para impedir:

- números duplicados;
- saltos provocados por carreras;
- cadenas inconsistentes.

## Importes

Los importes monetarios utilizarán tipos decimales exactos:

```text
Decimal
NUMERIC
```

y no números de coma flotante.

---

# Roadmap

## Fase 1 — Infraestructura

- [x] FastAPI
- [x] configuración mediante `.env`
- [x] PostgreSQL
- [x] Docker Compose
- [x] SQLAlchemy
- [x] Alembic
- [x] Pytest
- [x] Ruff

## Fase 2 — Business

- [x] modelo Business
- [x] schemas
- [x] repository
- [x] service
- [x] API
- [x] tests
- [x] activación/desactivación lógica

## Fase 3 — User y autenticación

- [x] modelo User
- [x] relación Business → Users
- [x] schemas
- [x] repository
- [x] service
- [x] API
- [x] hashing Argon2
- [x] autenticación
- [x] JWT
- [x] login
- [x] Bearer authentication
- [x] `get_current_user`
- [x] `/auth/me`
- [x] revocación funcional mediante estado de User/Business
- [x] normalización de email
- [x] búsqueda y login case-insensitive
- [x] unicidad case-insensitive en PostgreSQL
- [x] índice funcional `lower(email)`
- [x] sincronización SQLAlchemy/Alembic/PostgreSQL
- [x] mitigación temporal en login
- [ ] registro/bootstrap inicial

## Fase 4 — Autorización y tenants

- [x] identidad del tenant mediante `current_user.business_id`
- [x] dependencia `get_current_business_id`
- [x] comprobación reutilizable same-business
- [x] protección inicial de `GET /businesses/{business_id}`
- [x] test de acceso cross-tenant para Business
- [ ] proteger listado de Business
- [ ] proteger actualización de Business
- [ ] definir activación/desactivación de Business
- [ ] proteger creación/listado/actualización de User
- [ ] aislamiento completo entre empresas
- [ ] batería completa de tests cross-tenant

## Fase 5 — Products

- [ ] modelo Product
- [ ] impuestos
- [ ] precios
- [ ] repository
- [ ] service
- [ ] API
- [ ] tests

## Fase 6 — Customers

- [ ] modelo Customer
- [ ] repository
- [ ] service
- [ ] API
- [ ] tests

## Fase 7 — Invoicing

- [ ] modelo Invoice
- [ ] líneas de factura
- [ ] cálculo de bases imponibles
- [ ] impuestos
- [ ] totales
- [ ] numeración
- [ ] factura completa
- [ ] factura simplificada
- [ ] PDF
- [ ] QR
- [ ] tests de concurrencia

## Fase 8 — VERI\*FACTU

- [ ] BillingRecord
- [ ] ALTA
- [ ] ANULACION
- [ ] SUBSANACION
- [ ] encadenamiento
- [ ] hash
- [ ] validación de cadena
- [ ] XML
- [ ] integración AEAT
- [ ] respuestas
- [ ] reintentos
- [ ] histórico de envíos
- [ ] tests de integridad
- [ ] tests de manipulación
- [ ] tests de concurrencia

## Fase 9 — Frontend

- [ ] React
- [ ] TypeScript
- [ ] Vite
- [ ] Tailwind CSS
- [ ] autenticación
- [ ] dashboard
- [ ] productos
- [ ] clientes
- [ ] facturas
- [ ] estado VERI\*FACTU

---

# Próximos pasos

El siguiente bloque de trabajo se centrará en completar la seguridad y el aislamiento multi-tenant antes de comenzar los dominios funcionales de facturación.

Prioridades:

1. diseñar e implementar el flujo de registro/bootstrap;
2. proteger el resto de endpoints Business;
3. proteger los endpoints User;
4. completar los tests de aislamiento cross-tenant;
5. cerrar la fase de autenticación/autorización;
6. comenzar el dominio Product.

---

# Estado de calidad actual

En el checkpoint actual:

```text
Tests:          91 passed
Alembic:        synchronized
Database head:  666e0bbbf372
Email identity: case-insensitive
Tenant model:   foundations implemented
```

El proyecto mantiene como principio que cada nuevo bloque funcional debe cerrarse con:

```text
implementación
    ↓
tests específicos
    ↓
suite completa
    ↓
comprobación de migraciones
    ↓
revisión README
    ↓
Git commit
```

---

# Licencia

Proyecto desarrollado con fines educativos, profesionales y de portfolio.

La futura publicación o distribución de una versión utilizable en producción requerirá completar las validaciones técnicas, fiscales y de seguridad correspondientes.
