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
- ciclo de vida lógico de empresas;
- dominio de usuarios;
- relación Business → Users;
- creación y actualización de usuarios;
- activación y desactivación de usuarios en la capa de dominio;
- hashing seguro de contraseñas;
- autenticación de usuarios;
- generación y validación de JWT;
- endpoint de login;
- resolución del usuario autenticado mediante Bearer Token;
- endpoint `/auth/me`;
- registro/bootstrap inicial mediante `/auth/register`;
- creación atómica de Business + primer User;
- emisión de JWT tras el registro;
- rollback completo del registro ante fallos;
- revocación funcional de acceso para usuarios o empresas inactivas;
- normalización de direcciones de email;
- búsquedas y autenticación de email sin depender de mayúsculas/minúsculas;
- unicidad case-insensitive de email en PostgreSQL;
- autorización y aislamiento por tenant para Business;
- autorización y aislamiento por tenant para User;
- listado de Business limitado al tenant autenticado;
- listado de Users limitado al tenant autenticado;
- consulta y actualización de Business protegidas mediante comprobación same-business;
- consulta y actualización de User protegidas mediante comprobación same-business;
- ocultación de recursos Business y User cross-tenant mediante `404 Not Found`;
- creación de usuarios asociada internamente al tenant autenticado;
- `business_id` retirado del payload HTTP de creación ordinaria de usuarios;
- rechazo explícito de campos fuera del contrato en actualizaciones HTTP de Business y User;
- protección frente a intentos de modificar `is_active` mediante `PATCH /businesses/{business_id}`;
- protección frente a intentos de modificar `business_id` mediante `PATCH /users/{user_id}`;
- bootstrap de Business retirado de la API pública ordinaria y centralizado en `/auth/register`;
- activación/desactivación de Business mantenida en dominio, pero no expuesta actualmente mediante HTTP;
- activación/desactivación de User mantenida en dominio, pero no expuesta actualmente mediante HTTP;
- revisión final del aislamiento de los dominios públicos Business y User;
- fase inicial de autenticación, autorización y aislamiento por tenant completada.

La suite automatizada cuenta actualmente con:

```text
108 passed
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

La activación y desactivación continúan implementadas en la capa de dominio, pero actualmente no se exponen mediante endpoints HTTP públicos.

Las actualizaciones HTTP de Business utilizan un contrato estricto. Los campos no declarados en `BusinessUpdate` se rechazan en lugar de ignorarse silenciosamente.

Esto impide, entre otros casos, intentar modificar mediante el endpoint ordinario de actualización campos de ciclo de vida como:

```text
is_active
```

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

En la capa de dominio los usuarios pueden:

- crearse;
- consultarse;
- listarse por empresa;
- actualizarse;
- activarse;
- desactivarse;
- autenticarse.

La API HTTP de User está protegida mediante autenticación y aislamiento por tenant.

La creación ordinaria de usuarios no permite que el cliente seleccione el tenant mediante `business_id`. En su lugar, la empresa se deriva de:

```python
current_user.business_id
```

El schema HTTP de creación rechaza campos adicionales, por lo que un intento de proporcionar manualmente `business_id` no forma parte del contrato válido de la API.

El contrato HTTP de actualización también rechaza campos adicionales. Por tanto, `business_id` no puede introducirse mediante `PATCH /users/{user_id}` para intentar trasladar un usuario a otro tenant.

El listado de usuarios devuelve exclusivamente los usuarios pertenecientes al Business autenticado.

Las consultas y actualizaciones de usuarios aplican comprobación same-business y ocultan mediante `404 Not Found` los usuarios pertenecientes a otros tenants.

Las operaciones de activación y desactivación continúan disponibles en la capa de dominio, pero no se exponen actualmente mediante HTTP hasta disponer de una política administrativa o de roles adecuada.

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

## Registro y bootstrap inicial

El alta inicial de un tenant se realiza mediante:

```text
POST /auth/register
```

El endpoint recibe conjuntamente los datos de:

```text
Business
+
primer User
```

El cliente no proporciona `business_id`. La relación se establece internamente después de crear la empresa.

La operación se ejecuta como una única unidad transaccional:

```text
crear Business
      ↓
crear primer User
      ↓
generar access token
      ↓
commit
```

Los servicios de Business y User permiten omitir su `commit()` cuando participan en esta operación coordinada, manteniendo el límite final de la transacción en `AuthService`.

Si cualquier paso falla, se realiza:

```text
rollback
```

evitando dejar una empresa creada sin su usuario inicial.

El registro devuelve un JWT utilizable inmediatamente por el nuevo usuario.

Los conflictos conocidos de identidad devuelven:

```text
409 Conflict
```

tanto para un `tax_id` de empresa ya existente como para un email de usuario ya registrado.

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

La autorización responde a:

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

Este modelo se aplica actualmente a todos los dominios públicos que contienen recursos asociados a tenant: Business y User.

La revisión final de esta fase ha comprobado además que los contratos HTTP de actualización no acepten silenciosamente campos sensibles fuera del schema. `BusinessUpdate` y `UserUpdate` utilizan configuración estricta para rechazar campos adicionales mediante validación `422 Unprocessable Entity`.

### Business

```text
GET   /businesses
GET   /businesses/{business_id}
PATCH /businesses/{business_id}
```

Un usuario autenticado:

- solo puede listar su propia empresa;
- puede consultar únicamente su propia empresa;
- puede actualizar únicamente su propia empresa;
- recibe `404 Not Found` al intentar acceder o modificar una empresa perteneciente a otro tenant;
- no puede modificar `is_active` mediante el `PATCH` ordinario de Business.

La creación inicial de Business ya no se realiza mediante `POST /businesses`. El bootstrap del tenant se realiza exclusivamente mediante `POST /auth/register`, que crea de forma transaccional el Business y su primer User.

### User

```text
POST  /users
GET   /users
GET   /users/{user_id}
PATCH /users/{user_id}
```

Un usuario autenticado:

- puede crear nuevos usuarios únicamente dentro de su propio tenant;
- no puede seleccionar arbitrariamente otro `business_id` durante la creación;
- solo puede listar usuarios pertenecientes a su propia empresa;
- puede consultar únicamente usuarios de su propia empresa;
- puede actualizar únicamente usuarios de su propia empresa;
- no puede modificar `business_id` mediante el `PATCH` ordinario de User;
- recibe `404 Not Found` al intentar consultar o modificar usuarios de otro tenant.

Las operaciones de activación y desactivación de Business y User continúan disponibles en sus respectivas capas de dominio, pero no están expuestas actualmente mediante la API pública.

Su futura exposición requerirá una política explícita de autorización administrativa o roles.

---

# Endpoints actuales

## Health

```text
GET /health
GET /health/db
```

## Auth

```text
POST /auth/register
POST /auth/login
GET  /auth/me
```

## Businesses

```text
GET   /businesses
GET   /businesses/{business_id}
PATCH /businesses/{business_id}
```

Todos los endpoints públicos de Business requieren autenticación.

`GET /businesses` devuelve únicamente la empresa asociada al tenant autenticado y nunca expone el listado global de empresas.

`GET /businesses/{business_id}` y `PATCH /businesses/{business_id}` aplican comprobación `same-business`.

Los intentos de acceso cross-tenant devuelven `404 Not Found` para evitar revelar la existencia de recursos pertenecientes a otras empresas.

El contrato de actualización rechaza campos adicionales. En particular, `is_active` no puede modificarse mediante el endpoint ordinario `PATCH /businesses/{business_id}`.

La creación inicial de empresas se realiza mediante:

```text
POST /auth/register
```

Este endpoint crea de forma atómica el Business y su primer User.

Los antiguos endpoints públicos:

```text
POST  /businesses
PATCH /businesses/{business_id}/deactivate
PATCH /businesses/{business_id}/activate
```

ya no forman parte del contrato HTTP público.

La activación y desactivación lógica continúan implementadas en la capa de dominio y podrán integrarse posteriormente en un flujo administrativo con una política de autorización adecuada.

## Users

```text
POST  /users
GET   /users
GET   /users/{user_id}
PATCH /users/{user_id}
```

Todos los endpoints públicos de User requieren autenticación.

`POST /users` crea el usuario dentro del tenant autenticado. El cliente proporciona los datos del usuario, pero no selecciona `business_id`; dicho identificador se obtiene internamente a partir del usuario autenticado.

`GET /users` devuelve exclusivamente los usuarios pertenecientes al Business autenticado.

`GET /users/{user_id}` y `PATCH /users/{user_id}` aplican aislamiento same-business.

Los intentos de consultar o modificar usuarios pertenecientes a otro tenant devuelven:

```text
404 Not Found
```

El contrato de actualización rechaza campos adicionales. En particular, `business_id` no puede modificarse mediante `PATCH /users/{user_id}`.

Los endpoints:

```text
PATCH /users/{user_id}/deactivate
PATCH /users/{user_id}/activate
```

no forman parte actualmente del contrato HTTP público.

La activación y desactivación lógica siguen disponibles en la capa de dominio y podrán exponerse posteriormente cuando exista una política de roles o administración adecuada.

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
- aislamiento por tenant basado en `current_user.business_id`;
- protección completa de los endpoints públicos de Business;
- protección de los endpoints públicos actuales de User;
- ocultación de recursos cross-tenant mediante `404 Not Found`;
- listado de Business limitado al tenant autenticado;
- listado de Users limitado al tenant autenticado;
- actualización de Business limitada al tenant autenticado;
- consulta y actualización de User limitadas al tenant autenticado;
- creación ordinaria de User ligada al tenant autenticado;
- rechazo de `business_id` arbitrario en el payload HTTP de creación de User;
- rechazo de campos no declarados en las actualizaciones HTTP de Business y User;
- protección frente a modificación de `is_active` mediante el `PATCH` ordinario de Business;
- protección frente a modificación de `business_id` mediante el `PATCH` ordinario de User;
- registro/bootstrap transaccional;
- rollback completo si falla la creación del Business o del primer User;
- revisión de aislamiento de todos los dominios públicos actualmente asociados a tenant.

La fase inicial de autenticación, autorización y aislamiento necesaria para continuar con los siguientes dominios del MVP se considera completada.

Siguen existiendo mejoras de seguridad previstas para fases posteriores, entre ellas:

- ampliar la batería de aislamiento a cada nuevo dominio asociado a tenant;
- definir una política de roles/administración para operaciones sensibles;
- revisar los límites transaccionales y errores concurrentes a medida que aparezcan operaciones compuestas;
- definir una estrategia de revocación avanzada de sesiones/tokens si fuese necesaria.

Estas mejoras no se consideran bloqueantes para comenzar el dominio Product y deberán incorporarse cuando el modelo funcional correspondiente las requiera.

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
108 passed, 1 warning
```

El warning conocido es:

```text
StarletteDeprecationWarning:
Using `httpx` with `starlette.testclient` is deprecated;
install `httpx2` instead.
```

No bloquea actualmente el desarrollo y se resolverá de forma separada.

La suite cubre actualmente, entre otros:

- health endpoints;
- repositorio Business;
- servicio Business;
- API Business;
- ciclo de vida Business en la capa de dominio;
- autenticación obligatoria de los endpoints públicos Business;
- listado de Business limitado al tenant autenticado;
- acceso autenticado a la empresa propia;
- rechazo de consulta cross-tenant de Business;
- actualización de la empresa propia;
- rechazo de actualización cross-tenant de Business;
- rechazo de `is_active` como campo extra en la actualización HTTP de Business;
- retirada de la creación directa de Business de la API pública;
- retirada de activación/desactivación de Business de la API pública;
- repositorio User;
- servicio User;
- API User;
- autenticación obligatoria de los endpoints públicos User;
- creación de usuarios dentro del tenant autenticado;
- rechazo de `business_id` arbitrario en la creación HTTP de User;
- listado de usuarios limitado al tenant autenticado;
- acceso a usuarios del propio tenant;
- rechazo de consulta cross-tenant de User;
- actualización de usuarios del propio tenant;
- rechazo de actualización cross-tenant de User;
- rechazo de `business_id` como campo extra en la actualización HTTP de User;
- rechazo de actualización a un email ya existente;
- retirada de activación/desactivación de User de la API pública;
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
- registro/bootstrap de Business + primer User;
- emisión de JWT durante el registro;
- utilización inmediata del token mediante `/auth/me`;
- normalización de email durante el registro;
- rechazo de `tax_id` duplicado durante el registro;
- rechazo de email duplicado durante el registro;
- rollback del Business cuando falla la creación del primer User;
- comportamiento transaccional sin `commit()` de los servicios Business y User.

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
- [x] registro/bootstrap inicial
- [x] creación atómica de Business + primer User
- [x] JWT tras registro
- [x] rollback transaccional ante fallos de registro

## Fase 4 — Autorización y tenants

- [x] identidad del tenant mediante `current_user.business_id`
- [x] dependencia `get_current_business_id`
- [x] comprobación reutilizable same-business
- [x] protección de `GET /businesses/{business_id}`
- [x] protección de `GET /businesses`
- [x] listado de Business limitado al tenant autenticado
- [x] protección de `PATCH /businesses/{business_id}`
- [x] aislamiento cross-tenant en consulta y actualización de Business
- [x] retirada de `POST /businesses` del contrato público
- [x] retirada de activación/desactivación de Business de la API pública
- [x] tests de aislamiento y autenticación para Business
- [x] protección de `POST /users`
- [x] protección de `GET /users`
- [x] protección de `GET /users/{user_id}`
- [x] protección de `PATCH /users/{user_id}`
- [x] creación de User ligada al tenant autenticado
- [x] retirada de `business_id` del contrato HTTP de creación de User
- [x] listado de User limitado al tenant autenticado
- [x] aislamiento cross-tenant en consulta y actualización de User
- [x] retirada de activación/desactivación de User de la API pública
- [x] tests de aislamiento y autenticación para User
- [x] aislamiento de los dominios públicos actuales Business y User
- [x] contratos estrictos de actualización para Business y User
- [x] rechazo de campos sensibles fuera de contrato en operaciones PATCH
- [x] revisión final de aislamiento y límites de autorización
- [x] cierre de la fase de autenticación/autorización

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

Las fases iniciales de autenticación, autorización y aislamiento por tenant quedan cerradas para los dominios públicos actuales.

Business y User requieren autenticación, derivan el tenant del usuario autenticado y aplican aislamiento cross-tenant. Los contratos HTTP de actualización rechazan además campos fuera del schema para impedir modificaciones implícitas de atributos sensibles como `is_active` o `business_id`.

El siguiente bloque de trabajo comienza el dominio **Product**.

Prioridades:

1. definir el modelo y las reglas de negocio de Product;
2. definir la relación Product → Business y su aislamiento por tenant;
3. modelar precios e impuestos utilizando tipos decimales exactos;
4. implementar repository y service;
5. implementar la API protegida de Product;
6. cubrir el dominio con tests unitarios, de integración y de aislamiento cross-tenant.

Las mejoras futuras de roles, administración avanzada y gestión de sesiones se abordarán cuando exista un requisito funcional que las necesite, sin bloquear el desarrollo de los dominios principales del MVP.

---

# Estado de calidad actual

En el checkpoint actual:

```text
Tests:          108 passed
Alembic:        synchronized
Database head:  666e0bbbf372
Email identity: case-insensitive
Registration:   atomic bootstrap implemented
Business API:   tenant-protected
User API:       tenant-protected
Tenant model:   Business/User isolation reviewed
Auth/Authz:     Phase 4 completed
Next domain:    Product
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
