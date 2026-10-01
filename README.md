# VeriFactu App

Aplicación web de gestión comercial y facturación orientada a pequeños negocios y autónomos.

El proyecto nace como portfolio técnico y está diseñado para cubrir un flujo comercial sencillo:

```text
Cliente → Pedido → Albarán → Factura → Pago
```

> [!IMPORTANT]
> El proyecto está todavía en desarrollo y **no debe considerarse una implementación conforme con VERI\*FACTU**.
> La parte fiscal definitiva deberá implementarse y validarse contra las especificaciones técnicas vigentes de la AEAT.

---

## Estado actual

| Módulo      | Backend | Frontend |
| ----------- | ------- | -------- |
| Productos   | ✅      | ✅       |
| Clientes    | ✅      | ✅       |
| Pedidos     | ✅      | ✅       |
| Albaranes   | ✅      | ✅       |
| Facturas    | ✅      | 🚧       |
| Pagos       | 🚧      | 🚧       |
| VERI\*FACTU | 🚧      | 🚧       |

Actualmente están terminados de extremo a extremo los flujos de **Productos**, **Clientes**, **Pedidos** y **Albaranes**. El backend de **Facturas** también está implementado y validado.

---

## Funcionalidades implementadas

- autenticación mediante JWT;
- aislamiento multi-tenant por `business_id`;
- gestión de productos;
- gestión de clientes;
- pedidos con líneas y snapshots comerciales;
- cálculo de base imponible, impuestos y total del pedido;
- lifecycle de pedidos `DRAFT / CONFIRMED / CANCELLED`;
- albaranes vinculados a pedidos confirmados;
- entregas parciales;
- control de cantidades ya entregadas;
- bloqueo de sobreentregas;
- lifecycle de albaranes `DRAFT / CONFIRMED / CANCELLED`;
- PostgreSQL + Alembic;
- tests de Repository, Service y API;
- frontend React para Products, Customers, Orders y Delivery Notes.
- facturas en estado `DRAFT / ISSUED`;
- agrupación de albaranes confirmados del mismo cliente;
- snapshots de emisor, cliente y líneas de factura;
- cálculo de base imponible, impuestos y total de factura;
- numeración correlativa por serie al emitir;
- bloqueo de albaranes ya facturados;
- facturas emitidas inmutables;

---

## Stack

### Backend

- Python 3.13
- FastAPI
- SQLAlchemy 2
- PostgreSQL
- Alembic
- Pydantic
- Pydantic Settings
- Psycopg
- PyJWT
- Argon2
- Pytest
- Ruff

### Frontend

- React
- TypeScript
- Vite
- Tailwind CSS
- ESLint

### Desarrollo

- Docker
- Docker Compose

---

## Arquitectura

```text
FastAPI Router
      ↓
   Service
      ↓
 Repository
      ↓
 SQLAlchemy
      ↓
 PostgreSQL
```

- **Router**: contrato HTTP, autenticación y autorización.
- **Service**: reglas de negocio y transacciones.
- **Repository**: acceso a datos.

Los repositorios no realizan `commit()`. El límite transaccional pertenece a la capa Service.

---

## Pedidos

Los pedidos permiten seleccionar cliente, añadir productos y cantidades, guardar snapshots comerciales, calcular importes en backend, editar en `DRAFT`, confirmar y cancelar.

El frontend de pedidos está integrado y validado manualmente.

---

## Albaranes

Un albarán representa una entrega asociada a un pedido previamente confirmado.

Cada línea referencia una `OrderLine`, permitiendo controlar cuánto se ha entregado realmente.

```text
Pedido: 10 unidades

Albarán A CONFIRMED: 4
Albarán B CONFIRMED: 3
Albarán C CONFIRMED: 3

Total entregado: 10
```

Solo los albaranes `CONFIRMED` consumen cantidad entregada.

Antes de confirmar se valida:

```text
cantidad ya entregada
+
cantidad del nuevo albarán
<=
cantidad pedida
```

Cancelar un albarán confirmado libera de nuevo esa cantidad.

El frontend de albaranes permite listar, crear, editar borradores, seleccionar líneas del pedido, indicar cantidades entregadas, confirmar, cancelar y visualizar errores de negocio devueltos por el backend.

El flujo manual de entregas parciales y control de sobreentrega ha sido validado desde navegador.

---

## Facturas

El backend de facturación permite crear borradores a partir de uno o varios albaranes confirmados del mismo cliente.

Las facturas almacenan snapshots del emisor, cliente y líneas para preservar el contenido histórico del documento.

Los borradores no consumen numeración definitiva. Al emitir una factura se asigna una numeración correlativa por serie:

```text
F-000001
F-000002
F-000003

---

## Seguridad y multi-tenant

El tenant se obtiene del usuario autenticado mediante `business_id`.

Los recursos de otros tenants se ocultan mediante `404 Not Found`.

Este patrón se aplica actualmente a Business, User, Product, Customer, Order, Delivery Note e Invoice.

---

## Tests

```text
371 passed, 1 warning
```

Desglose principal:

```text
Product        45 tests
Customer       48 tests
Order          59 tests
Delivery Note  58 tests
Invoice        53 tests
```

El warning conocido procede de la integración entre `Starlette TestClient` y `httpx` y no afecta actualmente al resultado de la suite.

---

## Base de datos

```text
PostgreSQL
Alembic
Head: 36344f288a54
```

Sin operaciones pendientes:

```powershell
alembic check
```

---

## Desarrollo local

### Backend

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
alembic upgrade head
pytest -q
uvicorn app.main:app --reload
```

### Frontend

```powershell
cd frontend
npm install
npm run dev
npm run build
npm run lint
```

---

## Roadmap

```text
Invoice frontend
      ↓
Payment
      ↓
VERI*FACTU
```

La implementación futura de facturación deberá incluir numeración, snapshots históricos, PDF, QR y las reglas fiscales que correspondan.

La fase VERI\*FACTU deberá implementar y validar de forma específica los registros de facturación, encadenamiento, hash, formatos exigidos, integración con AEAT, respuestas, reintentos e integridad.

---

## Objetivo

El objetivo no es construir un ERP completo, sino una aplicación ligera y mantenible para pequeños negocios que permita gestionar su ciclo comercial y sirva como base técnica para una futura integración con VERI\*FACTU.

---

## Licencia

Proyecto desarrollado con fines educativos, profesionales y de portfolio.
