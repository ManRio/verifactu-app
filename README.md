# VeriFactu App

Aplicación web de facturación orientada a pequeños negocios y autónomos, desarrollada como proyecto de portfolio con una arquitectura preparada para incorporar los requisitos de **VERI\*FACTU**.

El objetivo es construir una solución ligera y mantenible para negocios que necesitan gestionar productos, clientes y facturas sin recurrir a un ERP o CRM de gran tamaño.

> [!IMPORTANT]
> Este proyecto está actualmente en desarrollo y **no debe considerarse todavía una implementación conforme con VERI\*FACTU**.
>
> La integración definitiva deberá implementarse y validarse contra las especificaciones técnicas vigentes de la AEAT.

---

## Estado actual

El proyecto comenzó con un enfoque **backend-first** para establecer una base sólida de persistencia, autenticación, autorización y aislamiento multi-tenant.

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
- autorización y aislamiento por tenant para Product;
- listado de Business limitado al tenant autenticado;
- listado de Users limitado al tenant autenticado;
- listado de Products limitado al tenant autenticado;
- consulta y actualización de Business protegidas mediante comprobación same-business;
- consulta y actualización de User protegidas mediante comprobación same-business;
- consulta y actualización de Product protegidas mediante comprobación same-business;
- ocultación de recursos cross-tenant mediante `404 Not Found`;
- creación de usuarios asociada internamente al tenant autenticado;
- creación de productos asociada internamente al tenant autenticado;
- contratos HTTP estrictos para impedir la modificación de campos sensibles;
- dominio Product;
- relación Business → Products;
- precios e impuestos representados mediante tipos decimales exactos;
- SKU opcional y único dentro de cada Business;
- repository, service y API de Product;
- ciclo de vida lógico de Product en la capa de dominio;
- suite de aislamiento multi-tenant para Product.

La suite automatizada cuenta actualmente con:

```text
147 passed, 1 warning
```

Existe un warning conocido relacionado con la integración entre `Starlette TestClient` y `httpx`. Actualmente no afecta al funcionamiento ni a los tests del proyecto y se tratará como deuda técnica separada.

El primer vertical slice funcional de **Product** está completado en backend. El siguiente objetivo es comenzar el frontend para disponer de una interfaz visible sobre las funcionalidades ya implementadas mientras el backend continúa evolucionando.

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

## Frontend

Stack previsto para la siguiente etapa:

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
    │       ├── 666e0bbbf372_enforce_case_insensitive_user_email_.py
    │       └── 40cc09359304_create_products_table.py
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
    │   │       ├── product.py
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
    │   │   ├── product/
    │   │   │   ├── __init__.py
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
    │   ├── test_auth_dependencies.py
    │   ├── test_auth_service.py
    │   ├── test_authorization_dependencies.py
    │   ├── test_business_api.py
    │   ├── test_business_repository.py
    │   ├── test_business_service.py
    │   ├── test_health.py
    │   ├── test_identity.py
    │   ├── test_product_api.py
    │   ├── test_product_repository.py
    │   ├── test_product_service.py
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
40cc09359304_create_products_table.py
```

La revisión actual es:

```text
40cc09359304 (head)
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

Una empresa puede tener múltiples usuarios y productos.

```text
Business
   │
   ├── Users
   │
   └── Products
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

# Dominio Product

Cada producto pertenece exactamente a una empresa mediante:

```text
business_id
```

Campos actuales:

```text
id
business_id
name
sku
description
unit_price
tax_rate
is_active
created_at
updated_at
```

La relación es:

```text
Business
   │
   └── Products
```

## Precios e impuestos

Los valores económicos utilizan tipos decimales exactos.

En Python:

```text
Decimal
```

En PostgreSQL:

```text
unit_price NUMERIC(12, 2)
tax_rate   NUMERIC(5, 2)
```

No se utilizan números de coma flotante para representar importes monetarios.

`unit_price` representa actualmente el precio unitario antes de impuestos.

`tax_rate` representa el porcentaje de impuesto asociado al producto dentro del modelo actual del MVP.

## SKU

El SKU es opcional.

Cuando existe, su unicidad se aplica dentro del Business:

```text
(business_id, sku)
```

Por tanto:

- dos productos del mismo Business no pueden compartir el mismo SKU;
- dos Businesses distintos sí pueden utilizar el mismo SKU;
- pueden existir múltiples productos sin SKU.

La restricción está reforzada en PostgreSQL mediante un índice único compuesto:

```text
uq_products_business_id_sku
```

La comparación de SKU es actualmente exacta y sensible a mayúsculas/minúsculas.

## Ciclo de vida

Product utiliza desactivación lógica mediante:

```text
is_active
```

La activación y desactivación están implementadas en la capa de dominio, pero no forman parte actualmente del contrato HTTP público.

No existe un `DELETE /products/{product_id}` ordinario.

## Aislamiento por tenant

La creación HTTP de Product no acepta `business_id`.

El tenant se obtiene internamente mediante:

```python
current_user.business_id
```

El listado:

```text
GET /products
```

devuelve exclusivamente los productos del Business autenticado.

Las operaciones sobre un producto concreto comprueban que:

```text
product.business_id == current_business_id
```

Los intentos de consultar o modificar productos de otro tenant devuelven:

```text
404 Not Found
```

para no revelar la existencia del recurso.

El contrato `ProductUpdate` es estricto y no permite modificar mediante el `PATCH` ordinario:

```text
business_id
is_active
```

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

Este modelo se aplica actualmente a los dominios públicos asociados a tenant:

```text
Business
User
Product
```

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

La creación inicial de Business se realiza exclusivamente mediante `POST /auth/register`.

### User

```text
POST  /users
GET   /users
GET   /users/{user_id}
PATCH /users/{user_id}
```

Un usuario autenticado:

- puede crear nuevos usuarios únicamente dentro de su propio tenant;
- no puede seleccionar arbitrariamente otro `business_id`;
- solo puede listar usuarios pertenecientes a su propia empresa;
- puede consultar únicamente usuarios de su propia empresa;
- puede actualizar únicamente usuarios de su propia empresa;
- no puede modificar `business_id` mediante el `PATCH` ordinario;
- recibe `404 Not Found` al intentar consultar o modificar usuarios de otro tenant.

### Product

```text
POST  /products
GET   /products
GET   /products/{product_id}
PATCH /products/{product_id}
```

Un usuario autenticado:

- puede crear productos únicamente dentro de su propio tenant;
- no puede proporcionar arbitrariamente otro `business_id`;
- solo puede listar productos de su propia empresa;
- puede consultar únicamente productos de su propia empresa;
- puede actualizar únicamente productos de su propia empresa;
- no puede modificar `business_id` mediante el `PATCH` ordinario;
- no puede modificar `is_active` mediante el `PATCH` ordinario;
- recibe `404 Not Found` al intentar consultar o modificar productos de otro tenant.

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

`GET /businesses` devuelve únicamente la empresa asociada al tenant autenticado.

`GET /businesses/{business_id}` y `PATCH /businesses/{business_id}` aplican comprobación same-business.

Los intentos de acceso cross-tenant devuelven `404 Not Found`.

Los antiguos endpoints públicos de creación y cambio de estado no forman parte actualmente del contrato HTTP.

## Users

```text
POST  /users
GET   /users
GET   /users/{user_id}
PATCH /users/{user_id}
```

Todos los endpoints públicos de User requieren autenticación.

`POST /users` deriva el tenant del usuario autenticado.

`GET /users` devuelve exclusivamente los usuarios del Business autenticado.

Las operaciones sobre un usuario concreto aplican aislamiento same-business.

Los endpoints de activación y desactivación no forman parte actualmente del contrato HTTP público.

## Products

```text
POST  /products
GET   /products
GET   /products/{product_id}
PATCH /products/{product_id}
```

Todos los endpoints de Product requieren autenticación.

`POST /products` deriva `business_id` del tenant autenticado y no permite que el cliente seleccione otra empresa.

`GET /products` devuelve exclusivamente los productos del Business autenticado.

`GET /products/{product_id}` y `PATCH /products/{product_id}` aplican aislamiento same-business.

Los intentos de acceso cross-tenant devuelven:

```text
404 Not Found
```

Los SKU duplicados dentro del mismo Business producen:

```text
409 Conflict
```

El mismo SKU puede existir en Businesses diferentes.

Los campos:

```text
business_id
is_active
```

no forman parte del contrato ordinario de actualización de Product y son rechazados si se intentan proporcionar mediante `PATCH`.

La activación y desactivación lógica de Product existen en la capa de dominio, pero no están expuestas actualmente mediante HTTP.

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
- protección de los endpoints públicos de Business;
- protección de los endpoints públicos de User;
- protección de los endpoints públicos de Product;
- ocultación de recursos cross-tenant mediante `404 Not Found`;
- listados de Business, User y Product limitados al tenant autenticado;
- creación ordinaria de User y Product ligada al tenant autenticado;
- rechazo de `business_id` arbitrario en los contratos HTTP correspondientes;
- rechazo de campos no declarados en contratos de actualización;
- protección frente a modificaciones ordinarias de atributos sensibles;
- registro/bootstrap transaccional;
- rollback completo si falla la creación del Business o del primer User.

La fase inicial de autenticación y autorización está completada y el patrón de aislamiento se aplica ya al dominio Product.

Siguen existiendo mejoras de seguridad previstas para fases posteriores, entre ellas:

- aplicar el mismo patrón de aislamiento a cada nuevo dominio asociado a tenant;
- definir una política de roles/administración para operaciones sensibles;
- revisar los límites transaccionales y errores concurrentes a medida que aparezcan operaciones compuestas;
- definir una estrategia de revocación avanzada de sesiones/tokens si fuese necesaria.

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
147 passed, 1 warning
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
- repository, service y API de Business;
- ciclo de vida Business en dominio;
- aislamiento multi-tenant de Business;
- contratos HTTP estrictos de Business;
- repository, service y API de User;
- ciclo de vida User en dominio;
- aislamiento multi-tenant de User;
- contratos HTTP estrictos de User;
- hashing de contraseñas;
- generación y decodificación de JWT;
- tokens manipulados y expirados;
- login;
- credenciales incorrectas;
- usuarios y empresas inactivas;
- `/auth/me`;
- resolución del usuario autenticado;
- normalización de email;
- autenticación y búsquedas case-insensitive;
- unicidad case-insensitive del email;
- resolución del tenant autenticado;
- autorización same-business;
- registro/bootstrap de Business + primer User;
- emisión de JWT durante el registro;
- rollback transaccional;
- comportamiento de servicios sin `commit()` cuando participan en transacciones coordinadas;
- repository de Product;
- service de Product;
- API de Product;
- creación de Product dentro del tenant autenticado;
- rechazo de `business_id` arbitrario;
- aislamiento del listado de Product por tenant;
- consulta de Product del tenant propio;
- rechazo de consultas cross-tenant;
- actualización de Product del tenant propio;
- rechazo de actualizaciones cross-tenant;
- rechazo de `business_id` e `is_active` en `PATCH`;
- SKU duplicado dentro del mismo Business;
- mismo SKU permitido en Businesses diferentes;
- eliminación opcional del SKU mediante `null`;
- activación y desactivación de Product en dominio;
- comportamiento transaccional de Product sin `commit()`.

La fase Product incorpora actualmente:

```text
16 tests API
 7 tests Repository
16 tests Service
-------------------
39 tests Product
```

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

En el cierre del vertical slice Product, los archivos modificados y añadidos han superado la comprobación dirigida de Ruff ignorando únicamente la regla `B008` ya conocida para dependencias FastAPI.

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
- [x] protección de Business
- [x] aislamiento cross-tenant de Business
- [x] protección de User
- [x] aislamiento cross-tenant de User
- [x] creación de User ligada al tenant autenticado
- [x] contratos HTTP estrictos
- [x] ocultación de recursos cross-tenant mediante `404`
- [x] tests de aislamiento y autenticación
- [x] cierre de la fase inicial de autenticación/autorización

## Fase 5 — Products

- [x] modelo Product
- [x] relación Business → Products
- [x] precios mediante `Decimal` / `NUMERIC`
- [x] porcentaje de impuesto mediante `Decimal` / `NUMERIC`
- [x] SKU opcional
- [x] unicidad de SKU por Business
- [x] repository
- [x] service
- [x] API
- [x] autenticación
- [x] aislamiento multi-tenant
- [x] contratos HTTP estrictos
- [x] activación/desactivación lógica en dominio
- [x] migración Alembic
- [x] tests Repository
- [x] tests Service
- [x] tests API
- [x] tests cross-tenant
- [x] vertical slice Product completado

## Fase 6 — Frontend inicial

- [ ] React
- [ ] TypeScript
- [ ] Vite
- [ ] Tailwind CSS
- [ ] estructura base y routing
- [ ] cliente HTTP
- [ ] autenticación
- [ ] persistencia y envío del Bearer Token
- [ ] layout principal
- [ ] listado de productos
- [ ] creación de productos
- [ ] edición de productos
- [ ] estados de carga y error

## Fase 7 — Customers

- [ ] modelo Customer
- [ ] repository
- [ ] service
- [ ] API
- [ ] aislamiento multi-tenant
- [ ] tests
- [ ] integración frontend

## Fase 8 — Invoicing

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
- [ ] integración frontend

## Fase 9 — VERI\*FACTU

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
- [ ] estado VERI\*FACTU en frontend

---

# Próximos pasos

El vertical slice de **Product** queda completado en backend.

La aplicación dispone ahora de una base suficiente para comenzar a construir una interfaz real sobre funcionalidades ya probadas:

```text
Business
   │
   ├── Users
   │
   └── Products
```

El siguiente bloque de trabajo será el **frontend inicial**.

La primera iteración estará orientada a obtener cuanto antes un flujo funcional visible:

```text
Login
  ↓
Layout autenticado
  ↓
Listado de productos
  ↓
Crear producto
  ↓
Editar producto
```

El frontend consumirá la API FastAPI existente y respetará el modelo de autenticación mediante Bearer Token.

Una vez establecida esta base visual, el desarrollo podrá continuar de forma vertical, incorporando nuevos dominios backend y su correspondiente interfaz sin esperar a completar todo el backend previamente.

Después del frontend inicial, el siguiente dominio principal será **Customer**, seguido del núcleo de facturación.

Las mejoras futuras de roles, administración avanzada, sesiones y robustez frente a determinadas condiciones concurrentes se abordarán cuando exista un requisito funcional que las necesite.

---

# Estado de calidad actual

En el checkpoint actual:

```text
Tests:           147 passed, 1 warning
Product tests:   39 passed
Alembic:         synchronized
Database head:   40cc09359304
Email identity:  case-insensitive
Registration:    atomic bootstrap implemented
Business API:    tenant-protected
User API:        tenant-protected
Product API:     tenant-protected
Tenant model:    Business/User/Product isolation
Auth/Authz:      initial phase completed
Product:         vertical slice completed
Next milestone:  frontend initial slice
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
