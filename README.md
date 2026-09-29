# VeriFactu App

Aplicación web de gestión comercial y facturación orientada a pequeños negocios y autónomos, desarrollada como proyecto de portfolio con una arquitectura preparada para evolucionar hacia los requisitos de **VERI\*FACTU**.

El objetivo es construir una solución ligera y mantenible para negocios que necesitan gestionar clientes, productos, pedidos, entregas, facturación y cobros sin recurrir a un ERP o CRM de gran tamaño.

> [!IMPORTANT]
> Este proyecto está actualmente en desarrollo y **no debe considerarse todavía una implementación conforme con VERI\*FACTU**.
>
> La integración fiscal definitiva deberá implementarse y validarse contra las especificaciones técnicas vigentes de la AEAT.

---

## Estado actual

El proyecto comenzó con un enfoque **backend-first** para establecer una base sólida de persistencia, autenticación, autorización, aislamiento multi-tenant y reglas de negocio.

Actualmente están implementados:

- configuración del backend con `pydantic-settings`;
- PostgreSQL y migraciones con Alembic;
- dominio Business;
- dominio User;
- autenticación mediante JWT;
- registro/bootstrap inicial de Business + primer User;
- aislamiento multi-tenant;
- dominio Product;
- dominio Customer;
- frontend funcional para Product y Customer;
- dominio Order;
- líneas de pedido con snapshot de producto;
- cálculo de base, impuestos y total del pedido;
- lifecycle `DRAFT → CONFIRMED / CANCELLED`;
- edición restringida a pedidos en borrador;
- API protegida de pedidos;
- aislamiento multi-tenant de pedidos;
- tests de Repository, Service y API para Order.

La suite automatizada cuenta actualmente con:

```text
260 passed, 1 warning
```

El warning conocido procede de la integración entre `Starlette TestClient` y `httpx`. No afecta actualmente al funcionamiento de la aplicación ni al resultado de los tests y se mantiene como deuda técnica separada.

Los vertical slices de **Product** y **Customer** están implementados de extremo a extremo, incluido frontend.

El vertical slice de **Order** está implementado y probado de extremo a extremo, incluido el frontend React. El flujo manual de creación, edición, confirmación y cancelación de pedidos ha sido validado. El siguiente paso funcional será comenzar el dominio **Delivery Note / Albarán**.

---

# Objetivo del proyecto

VeriFactu App pretende cubrir las necesidades esenciales de gestión comercial y facturación de pequeños negocios mediante una interfaz sencilla y una arquitectura capaz de evolucionar posteriormente hacia VERI\*FACTU.

El flujo comercial previsto para el MVP es:

```text
Cliente
  ↓
Pedido
  ↓
Albarán / entrega
  ↓
Factura
  ↓
Pago
```

Estos conceptos permanecen separados deliberadamente:

- un pedido representa la intención comercial;
- un albarán representa una entrega;
- una factura representa el documento de facturación;
- un pago representa el cobro.

La emisión de una factura no dependerá conceptualmente de que esta se encuentre pagada.

## Alcance previsto del MVP

- gestión de cuenta y negocio;
- gestión de usuarios;
- autenticación y autorización;
- gestión de productos;
- gestión de clientes;
- pedidos y líneas de pedido;
- albaranes y entregas;
- facturación;
- pagos;
- impuestos y precios;
- numeración de facturas;
- factura completa y simplificada cuando corresponda;
- generación de PDF;
- generación de QR;
- registros de facturación;
- encadenamiento de registros;
- cálculo de hash según la especificación aplicable;
- registros de alta;
- anulación;
- rectificación y subsanación;
- integración con AEAT;
- almacenamiento de respuestas e incidencias;
- verificación de la cadena de registros;
- dashboard básico de gestión y estado VERI\*FACTU.

---

# Fuera del alcance inicial

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

- React
- TypeScript
- Vite
- Tailwind CSS
- ESLint

El frontend consume la API REST desarrollada con FastAPI.

La autenticación utiliza JWT mediante Bearer Token. El token de acceso se mantiene en el cliente y se incorpora a las peticiones dirigidas a endpoints protegidos.

Actualmente existen flujos frontend funcionales para:

```text
Login
  ↓
Autenticación JWT
  ↓
Productos
  ├── listar
  ├── crear
  ├── editar
  └── activar / desactivar
  ↓
Clientes
  ├── listar
  ├── crear
  ├── editar
  └── activar / desactivar
```

La integración `Frontend → FastAPI → PostgreSQL` ha sido verificada manualmente para Product y Customer.

---

# Arquitectura

El backend sigue una separación explícita por responsabilidades:

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

## Router

Responsable del contrato HTTP: rutas, parámetros, códigos de estado, serialización, dependencias, autenticación y autorización.

## Service

Responsable de reglas de negocio, validaciones de dominio, coordinación entre repositorios y límites de transacción.

## Repository

Responsable exclusivamente del acceso a datos.

Los repositorios utilizan `flush()` y `refresh()`, pero no realizan `commit()`.

El límite de la transacción pertenece a la capa de servicio. Esta decisión será especialmente importante en futuras operaciones compuestas de facturación y VERI\*FACTU.

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
├── backend/
│   ├── alembic/
│   │   └── versions/
│   │       ├── f59baa15a544_initial_migration.py
│   │       ├── 4edaea57d404_create_businesses_table.py
│   │       ├── e4eb415b0211_add_is_active_to_businesses.py
│   │       ├── a23de07e7fb2_create_users_table.py
│   │       ├── 666e0bbbf372_enforce_case_insensitive_user_email_.py
│   │       ├── 40cc09359304_create_products_table.py
│   │       ├── 42772bf4e57d_create_customers_table.py
│   │       └── 6a6fffec7d19_create_orders_and_order_lines.py
│   │
│   ├── app/
│   │   ├── api/
│   │   │   ├── dependencies/
│   │   │   └── routes/
│   │   │       ├── auth.py
│   │   │       ├── business.py
│   │   │       ├── customer.py
│   │   │       ├── order.py
│   │   │       ├── product.py
│   │   │       └── user.py
│   │   ├── core/
│   │   ├── db/
│   │   ├── domain/
│   │   │   ├── auth/
│   │   │   ├── business/
│   │   │   ├── customer/
│   │   │   ├── order/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── model.py
│   │   │   │   ├── repository.py
│   │   │   │   ├── schemas.py
│   │   │   │   └── service.py
│   │   │   ├── product/
│   │   │   └── user/
│   │   └── main.py
│   │
│   └── tests/
│       ├── test_order_api.py
│       ├── test_order_repository.py
│       └── test_order_service.py
│
└── frontend/
    ├── src/
    │   ├── components/
    │   ├── pages/
    │   ├── services/
    │   ├── types/
    │   └── App.tsx
    ├── package.json
    └── vite.config.ts
```

---

# Configuración

La configuración del backend se gestiona mediante `pydantic-settings`.

Ejemplo de `.env`:

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

El archivo `.env` no debe incluirse en Git. El repositorio contiene `.env.example` como referencia.

---

# Base de datos y Alembic

Configuración actual:

```text
Database:       verifactu
User:           verifactu
Container:      verifactu-postgres
Host port:      55732
Container port: 5432
```

Migraciones actuales:

```text
f59baa15a544_initial_migration.py
4edaea57d404_create_businesses_table.py
e4eb415b0211_add_is_active_to_businesses.py
a23de07e7fb2_create_users_table.py
666e0bbbf372_enforce_case_insensitive_user_email_.py
40cc09359304_create_products_table.py
42772bf4e57d_create_customers_table.py
6a6fffec7d19_create_orders_and_order_lines.py
```

Revisión actual:

```text
6a6fffec7d19 (head)
```

Comprobación de sincronización:

```powershell
alembic check
```

Resultado actual:

```text
No new upgrade operations detected.
```

---

# Dominios principales

## Business

Business representa el tenant principal de la aplicación.

Relaciones actuales:

```text
Business
   ├── Users
   ├── Products
   ├── Customers
   └── Orders
```

## User

Cada usuario pertenece exactamente a una empresa mediante `business_id`. Las contraseñas se almacenan mediante Argon2 y la API aplica autenticación y aislamiento por tenant.

## Product

Cada producto pertenece a un Business.

Los valores monetarios utilizan `Decimal` en Python y `NUMERIC` en PostgreSQL.

El SKU es opcional y único dentro de cada Business cuando existe.

Lifecycle HTTP:

```text
PATCH /products/{product_id}/activate
PATCH /products/{product_id}/deactivate
```

## Customer

Cada cliente pertenece a un Business.

`tax_id` es opcional en el modelo actual y, cuando existe, es único dentro del Business.

Lifecycle HTTP:

```text
PATCH /customers/{customer_id}/activate
PATCH /customers/{customer_id}/deactivate
```

## Order

Order representa el pedido comercial previo a la entrega y a la facturación.

Cada pedido pertenece a un Business y a un Customer y contiene una o más líneas.

### Campos principales de Order

```text
id
business_id
customer_id
status
notes
subtotal
tax_total
total_amount
created_at
updated_at
confirmed_at
```

### Campos principales de OrderLine

```text
id
order_id
product_id
description
quantity
unit_price
tax_rate
base_amount
tax_amount
total_amount
position
created_at
```

### Snapshot comercial

Las líneas conservan una copia de `description`, `unit_price` y `tax_rate` del Product utilizado en el momento de creación o sustitución de la línea.

De esta forma, una modificación posterior del producto no altera los datos comerciales ya persistidos en el pedido.

### Cantidades e importes

```text
quantity     NUMERIC(12, 3)
subtotal     NUMERIC(14, 2)
tax_total    NUMERIC(14, 2)
total_amount NUMERIC(14, 2)
```

El backend calcula bases, impuestos y totales. El cliente HTTP no puede suministrar directamente esos importes.

La capa Service utiliza `ROUND_HALF_UP` para el redondeo monetario del pedido.

> Las reglas fiscales definitivas de cálculo y redondeo de Invoice se validarán específicamente al implementar el dominio de facturación.

### Lifecycle de Order

Estados actuales:

```text
DRAFT
CONFIRMED
CANCELLED
```

Flujo:

```text
DRAFT
 ├── editar
 ├── confirmar → CONFIRMED
 └── cancelar  → CANCELLED

CONFIRMED
 └── cancelar  → CANCELLED
```

Un pedido confirmado no puede editarse mediante la operación ordinaria. Un pedido cancelado se conserva para mantener trazabilidad.

### Tenant y validaciones

La creación HTTP de Order no acepta `business_id`.

El backend valida que Customer y Product pertenecen al mismo Business del usuario autenticado y que están activos. Los accesos cross-tenant se ocultan mediante `404 Not Found`.

---

# Autenticación y autorización

La autenticación utiliza JWT con Bearer Token.

El tenant autenticado se deriva de:

```python
current_user.business_id
```

La aplicación utiliza:

```text
get_current_business_id
ensure_same_business
```

Cuando se intenta acceder a un recurso de otro tenant se devuelve `404 Not Found` para no revelar que el recurso existe.

Este modelo se aplica actualmente a:

```text
Business
User
Product
Customer
Order
```

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

## Users

```text
POST  /users
GET   /users
GET   /users/{user_id}
PATCH /users/{user_id}
```

## Products

```text
POST  /products
GET   /products
GET   /products/{product_id}
PATCH /products/{product_id}
PATCH /products/{product_id}/activate
PATCH /products/{product_id}/deactivate
```

## Customers

```text
POST  /customers
GET   /customers
GET   /customers/{customer_id}
PATCH /customers/{customer_id}
PATCH /customers/{customer_id}/activate
PATCH /customers/{customer_id}/deactivate
```

## Orders

```text
POST  /orders
GET   /orders
GET   /orders/{order_id}
PATCH /orders/{order_id}
PATCH /orders/{order_id}/confirm
PATCH /orders/{order_id}/cancel
```

Todos los endpoints de Order requieren autenticación y aislamiento por tenant.

---

# Frontend

El frontend está desarrollado con React, TypeScript, Vite y Tailwind CSS.

Actualmente están integrados:

- Login;
- listado, creación, edición y lifecycle de Products;
- listado, creación, edición y lifecycle de Customers.

El backend de Orders ya está implementado. La integración frontend de Order está implementada y permite:

- listar pedidos;
- crear un borrador;
- seleccionar cliente;
- añadir productos y cantidades;
- editar pedidos `DRAFT`;
- mostrar base, impuestos y total calculados por backend;
- confirmar pedidos;
- cancelar pedidos;
- consultar su estado.

El último checkpoint frontend ha superado:

```powershell
npm run build
npm run lint
```

---

# Tests

Para ejecutar toda la suite:

```powershell
pytest -q
```

Estado actual:

```text
260 passed, 1 warning
```

Desglose de los principales vertical slices:

```text
Product
22 API
 7 Repository
16 Service
---------
45 total

Customer
23 API
 8 Repository
17 Service
---------
48 total

Order
27 API
 6 Repository
26 Service
---------
59 total
```

La suite de Order cubre, entre otros:

- creación de pedidos;
- snapshots de producto;
- cálculo de importes;
- redondeo monetario;
- Customer inexistente, inactivo o cross-tenant;
- Product inexistente, inactivo o cross-tenant;
- posiciones duplicadas;
- aislamiento por tenant;
- edición de pedidos `DRAFT`;
- sustitución de líneas;
- recálculo de totales;
- confirmación;
- cancelación;
- bloqueo de operaciones incompatibles con el estado;
- autenticación de endpoints;
- respuestas HTTP de error.

Warning conocido:

```text
StarletteDeprecationWarning:
Using `httpx` with `starlette.testclient` is deprecated;
install `httpx2` instead.
```

---

# Ruff

Ruff se utiliza para análisis estático y mantenimiento de calidad.

No se ejecuta un `ruff check . --fix` indiscriminado sobre el proyecto para evitar mezclar deuda de estilo histórica con cambios funcionales.

Los archivos nuevos de Order, su migración y sus tests han sido comprobados de forma dirigida.

---

# Desarrollo local

## Base de datos

```powershell
docker compose up -d
docker compose ps
```

## Backend

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
alembic upgrade head
alembic check
pytest -q
uvicorn app.main:app --reload
```

API local:

```text
http://127.0.0.1:8000
```

## Frontend

```powershell
cd frontend
npm install
npm run dev
```

Comprobaciones:

```powershell
npm run build
npm run lint
```

---

# Principios de diseño para el ciclo comercial y VERI\*FACTU

## Separación del ciclo comercial

```text
Order
  ↓
Delivery Note
  ↓
Invoice
  ↓
Payment
```

Entrega, facturación y pago representan conceptos distintos. El estado de pago no se utilizará como condición para emitir una factura.

Los documentos posteriores deberán conservar snapshots suficientes para no reconstruir información histórica a partir de datos mutables.

## Inmutabilidad

Los futuros registros fiscales emitidos no deberán modificarse como registros ordinarios. Las correcciones deberán representarse conforme al mecanismo previsto por la especificación aplicable.

## Hash y encadenamiento

El hash, los campos participantes y el procedimiento de encadenamiento se implementarán exactamente según la especificación técnica aplicable. No se asumirá que el hash corresponde simplemente al XML completo.

## Envíos

Los registros de facturación y los intentos de envío se modelarán por separado para conservar estado, respuesta, errores y reintentos.

## Concurrencia

La numeración de facturas y cualquier encadenamiento fiscal deberán ser seguros frente a concurrencia mediante transacciones PostgreSQL y los mecanismos de bloqueo que resulten necesarios.

## Importes

Los importes monetarios utilizarán `Decimal` / `NUMERIC`, no tipos de coma flotante.

---

# Roadmap

## Fases 1–7 — Base del MVP

- [x] Infraestructura
- [x] Business
- [x] User y autenticación
- [x] Autorización y tenants
- [x] Products backend
- [x] Products frontend
- [x] Customers backend
- [x] Customers frontend

## Fase 8A — Orders

- [x] modelo Order
- [x] modelo OrderLine
- [x] relaciones con Business, Customer y Product
- [x] migración Alembic
- [x] schemas
- [x] repository
- [x] service
- [x] snapshot de Product
- [x] cálculo de importes
- [x] lifecycle `DRAFT / CONFIRMED / CANCELLED`
- [x] edición exclusiva de `DRAFT`
- [x] API
- [x] autenticación
- [x] aislamiento multi-tenant
- [x] tests Repository
- [x] tests Service
- [x] tests API
- [x] suite completa
- [x] integración frontend

## Fase 8B — Delivery Notes / Albaranes

- [ ] modelo DeliveryNote
- [ ] líneas de entrega
- [ ] relación con Order
- [ ] entregas parciales
- [ ] cantidades entregadas
- [ ] lifecycle
- [ ] API
- [ ] multi-tenant
- [ ] tests
- [ ] frontend

## Fase 8C — Invoicing

- [ ] modelo Invoice
- [ ] líneas de factura
- [ ] snapshots históricos
- [ ] relación con entregas pendientes de facturar
- [ ] agrupación de entregas cuando corresponda
- [ ] bases imponibles
- [ ] impuestos
- [ ] totales
- [ ] numeración
- [ ] factura completa
- [ ] factura simplificada
- [ ] PDF
- [ ] QR
- [ ] tests de concurrencia
- [ ] frontend

## Fase 8D — Payments

- [ ] modelo Payment
- [ ] relación con Invoice
- [ ] cobro total/parcial
- [ ] estado de cobro derivado
- [ ] API
- [ ] tests
- [ ] frontend

## Fase 9 — VERI\*FACTU

- [ ] BillingRecord
- [ ] registros de alta
- [ ] anulación
- [ ] subsanación/corrección según especificación aplicable
- [ ] encadenamiento
- [ ] hash
- [ ] validación de cadena
- [ ] formatos exigidos
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

Estado de los vertical slices principales:

```text
Product  → backend + frontend
Customer → backend + frontend
Order    → backend + frontend
```

El vertical slice de Order está completado de extremo a extremo:

```text
Order
  ↓
React frontend
  ↓
FastAPI
  ↓
Service / Repository
  ↓
PostgreSQL
```

Siguiente paso inmediato:

```text
Delivery Note / Albarán backend
     ↓
Delivery Note frontend
     ↓
Invoice
     ↓
Payment
     ↓
VERI*FACTU
```

---

# Estado de calidad actual

```text
Backend tests:        260 passed, 1 warning

Product API tests:     22 passed
Product total tests:   45 passed

Customer API tests:    23 passed
Customer total tests:  48 passed

Order API tests:       27 passed
Order Repository:       6 passed
Order Service:         26 passed
Order total tests:     59 passed

Alembic:               synchronized
Database head:         6a6fffec7d19

Business API:          tenant-protected
User API:              tenant-protected
Product API:           tenant-protected
Customer API:          tenant-protected
Order API:             tenant-protected

Product frontend:      integrated
Customer frontend:     integrated
Order backend:         vertical slice completed
Order frontend:        integrated and manually verified

Frontend build:        passing
Frontend lint:         passing
```

Cada bloque funcional se cierra siguiendo:

```text
implementación
    ↓
tests específicos
    ↓
suite completa
    ↓
comprobación de migraciones
    ↓
integración frontend cuando corresponda
    ↓
revisión README
    ↓
Git commit
```

---

# Licencia

Proyecto desarrollado con fines educativos, profesionales y de portfolio.

La futura publicación o distribución de una versión utilizable en producción requerirá completar las validaciones técnicas, fiscales y de seguridad correspondientes.
