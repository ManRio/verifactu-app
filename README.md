# VeriFactu App

**Aplicación de gestión comercial y facturación para pequeños negocios y autónomos.**

> [!IMPORTANT]
> **Proyecto en desarrollo.** La aplicación es un prototipo técnico y **no implementa ni acredita actualmente el cumplimiento de VERI\*FACTU** ni de todos los requisitos exigibles a un sistema informático de facturación (SIF). No debe utilizarse como solución fiscal conforme en un entorno real. La adaptación normativa y las pruebas correspondientes son tareas pendientes.

## Descripción

El proyecto modela un flujo comercial completo, desde la creación de un pedido hasta el cobro de una factura:

```text
Cliente → Pedido → Albarán → Factura → Pago
```

Su objetivo es desarrollar una aplicación modular, mantenible y multiempresa, poniendo el foco en las reglas de negocio, el control de estados, la trazabilidad de operaciones y la calidad del código. **El flujo de gestión está implementado hasta la emisión de facturas de prueba, tanto en backend como en frontend. La gestión de pagos está pendiente.**

## Estado del desarrollo

| Módulo                         | Backend | Frontend | Estado                                                                        |
| ------------------------------ | :-----: | :------: | ----------------------------------------------------------------------------- |
| Autenticación y usuarios       |   ✅    |    🟡    | Registro y acceso vía API; pantalla de inicio de sesión                       |
| Productos                      |   ✅    |    ✅    | Alta, edición, listado, activación/desactivación y paginación en cliente      |
| Clientes                       |   ✅    |    ✅    | Gestión integrada                                                             |
| Pedidos                        |   ✅    |    ✅    | Creación, edición de borradores, confirmación, cancelación y ficha de detalle |
| Albaranes                      |   ✅    |    ✅    | Entregas parciales, control de cantidades y ficha de detalle                  |
| Facturas                       |   ✅    |    ✅    | Listado, filtros, borradores, edición, emisión y consulta detallada           |
| Pagos                          |   ⏳    |    ⏳    | Pendiente                                                                     |
| Integración fiscal VERI\*FACTU |   ⏳    |    ⏳    | Pendiente de diseño, implementación y validación                              |

**Leyenda:** ✅ implementado · 🟡 parcial · ⏳ pendiente. Los estados describen las funcionalidades presentes en el repositorio, no una certificación de preparación para producción.

### Funcionalidades implementadas

- **Seguridad y multiempresa:** autenticación con JWT, vinculación de recursos a `business_id` y aislamiento de datos entre empresas.
- **Productos y clientes:** creación, consulta y actualización; operaciones de activación/desactivación donde corresponda.
- **Pedidos:** líneas con datos comerciales históricos (_snapshots_), cálculo de base imponible, impuestos y total; estados `DRAFT`, `CONFIRMED` y `CANCELLED`. En la interfaz pueden abrirse fichas de detalle desde el listado.
- **Albaranes:** creación desde pedidos confirmados, entregas parciales y control de sobreentregas. Solo las entregas confirmadas consumen cantidad; cancelar un albarán confirmado libera esa cantidad cuando lo permiten las reglas de negocio. La ficha de detalle enlaza con el pedido de origen.
- **Facturas:** borradores a partir de uno o varios albaranes confirmados del mismo cliente, snapshots de emisor, receptor y líneas, cálculo de importes, emisión y numeración correlativa por serie. El frontend permite crear y editar borradores, consultar su detalle y emitirlos con confirmación. Las facturas emitidas no son editables mediante la API actual y se impide reutilizar albaranes ya facturados.
- **Interfaz:** páginas de Productos, Clientes, Pedidos, Albaranes y Facturas; fichas de detalle y enlaces entre documentos relacionados; navegación lateral adaptable y paginación local de productos (10 por página).
- **Persistencia y calidad:** PostgreSQL, migraciones con Alembic y pruebas con Pytest en capas Repository, Service y API.

## Tecnologías

| Área              | Tecnologías                                                     |
| ----------------- | --------------------------------------------------------------- |
| Backend           | Python 3.13+, FastAPI, Pydantic, SQLAlchemy 2, Psycopg, Alembic |
| Seguridad         | PyJWT, Argon2                                                   |
| Base de datos     | PostgreSQL 17 (entorno Docker incluido)                         |
| Frontend          | React 19, TypeScript, React Router 7, Vite 8, Tailwind CSS 4    |
| Pruebas y calidad | Pytest, Ruff, ESLint, TypeScript                                |
| Entorno local     | Docker Compose, Python `venv`, npm                              |

## Arquitectura

El backend está organizado en capas:

```text
HTTP / FastAPI Router
         ↓
      Service
         ↓
    Repository
         ↓
 SQLAlchemy / PostgreSQL
```

- **Router:** contratos HTTP, dependencias de autenticación/autorización y traducción de errores a respuestas API.
- **Service:** validaciones, reglas comerciales, cambios de estado y límites transaccionales.
- **Repository:** consultas y persistencia, sin asumir el `commit()` de las operaciones de negocio.

Los datos de una empresa se identifican por el `business_id` del usuario autenticado, en lugar de confiar en un identificador de empresa proporcionado libremente por el cliente.

## Flujo de negocio

### Pedidos

Un pedido reúne un cliente y una o varias líneas de producto. El backend calcula los importes y controla las transiciones entre `DRAFT`, `CONFIRMED` y `CANCELLED`.

### Albaranes

Los albaranes representan las entregas asociadas a pedidos confirmados. Por ejemplo:

```text
Pedido confirmado: 10 unidades
Albarán A confirmado: 4
Albarán B confirmado: 3
Albarán C confirmado: 3
Total entregado: 10
```

El backend impide confirmar entregas cuya suma supere la cantidad pedida. Este flujo se probó manualmente desde la interfaz durante el desarrollo.

### Facturas — backend y frontend implementados

Las facturas se crean en estado `DRAFT` a partir de albaranes confirmados de un mismo cliente. Antes de la emisión pueden modificarse los campos admitidos por la API y la relación de albaranes. Al emitir, reciben fecha, serie y numeración correlativa, por ejemplo:

```text
F-000001
F-000002
F-000003
```

Se conservan snapshots de emisor, receptor y líneas, además de los importes calculados. El estado final implementado es `ISSUED`: **no existe todavía un flujo de rectificación, anulación fiscal ni generación de documentos PDF**.

Endpoints disponibles:

| Método  | Ruta                           | Operación                     |
| ------- | ------------------------------ | ----------------------------- |
| `POST`  | `/invoices`                    | Crear borrador                |
| `GET`   | `/invoices`                    | Listar facturas de la empresa |
| `GET`   | `/invoices/{invoice_id}`       | Consultar factura             |
| `PATCH` | `/invoices/{invoice_id}`       | Editar borrador               |
| `PATCH` | `/invoices/{invoice_id}/issue` | Emitir factura                |

La interfaz permite listar y filtrar facturas por estado, crear borradores seleccionando albaranes confirmados disponibles de un mismo cliente, editar borradores, consultar el desglose económico y navegar a los albaranes asociados. La emisión es una acción separada, con confirmación explícita. Una factura emitida se consulta en modo de solo lectura.

### Navegación entre documentos

Las fichas de detalle pueden abrirse directamente mediante estas rutas de React Router:

| Documento | Ruta                              | Contenido principal                                               |
| --------- | --------------------------------- | ----------------------------------------------------------------- |
| Pedido    | `/orders/:orderId`                | Cliente, líneas, importes, estado y albaranes asociados           |
| Albarán   | `/delivery-notes/:deliveryNoteId` | Entrega, cantidades, estado y enlace al pedido                    |
| Factura   | `/invoices/:invoiceId`            | Datos fiscales registrados, líneas, totales y albaranes asociados |

Las rutas se protegen mediante la sesión de la aplicación y el backend valida la pertenencia de los recursos a la empresa autenticada. La disponibilidad de una ficha de consulta no implica permiso para modificar un documento confirmado o emitido.

## Puesta en marcha local

### Requisitos

- Python **3.13 o posterior**.
- Node.js y npm compatibles con las versiones de Vite del proyecto (para desarrollo se utiliza Node.js 24).
- Docker y Docker Compose, o una instalación local de PostgreSQL correctamente configurada.

Los comandos siguientes están pensados para **PowerShell en Windows**.

### 1. Clonar y configurar el entorno

```powershell
git clone https://github.com/ManRio/verifactu-app.git
cd verifactu-app
Copy-Item .env.example .env
```

Edita el archivo **`.env` en la raíz del repositorio**. Si utilizas el `docker-compose.yml` incluido, configura `POSTGRES_PASSWORD=verifactu_dev`, porque ese es el valor utilizado por el contenedor de desarrollo. Ajusta también `JWT_SECRET_KEY` con un secreto local propio, robusto y no compartido.

> El contenedor incluye credenciales **solo para desarrollo local**. No reutilices esta configuración en producción ni subas `.env` al repositorio.

### 2. Levantar PostgreSQL

Desde la raíz del proyecto:

```powershell
docker compose up -d postgres
```

El contenedor publica PostgreSQL en el puerto local **55732**, tal como espera el `.env.example`.

### 3. Preparar el backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload
```

API: `http://127.0.0.1:8000`  
Documentación interactiva: `http://127.0.0.1:8000/docs`  
Comprobación básica: `http://127.0.0.1:8000/health`

En una terminal distinta, dentro de `backend` y con el entorno virtual activado, puedes ejecutar:

```powershell
pytest -q
ruff check .
alembic check
```

Las pruebas de integración utilizan la base de datos configurada; ejecútalas únicamente contra un **entorno de desarrollo/pruebas**.

### 4. Preparar el frontend

En otra terminal, desde la raíz del repositorio:

```powershell
cd frontend
npm install
npm run dev
```

Interfaz local: `http://localhost:5173`. **Mantén el mismo puerto** al iniciar Vite: actualmente FastAPI solo autoriza por CORS los orígenes `http://localhost:5173` y `http://127.0.0.1:5173`. Si Vite cambia a `5174` por tener `5173` ocupado, el inicio de sesión será bloqueado por CORS hasta que recuperes el puerto o actualices la configuración del backend.

Para iniciar sesión, registra primero una empresa y su usuario mediante `POST /auth/register` en la documentación interactiva de la API. Después utiliza la página `/login`.

Comprobaciones adicionales del frontend:

```powershell
npm run lint
npm run build
```

> Actualmente los servicios del frontend emplean direcciones locales de API definidas en código (`localhost:8000` y `127.0.0.1:8000`). Centralizar esta configuración mediante variables de entorno es una mejora pendiente antes de desplegar.

## Pruebas y migraciones

El backend cuenta con pruebas automatizadas en capas Repository, Service y API.

**Última verificación registrada del backend (20/11/2026):**

- Pytest: **371 pruebas superadas**, con 1 advertencia conocida relacionada con Starlette TestClient y `httpx`.
- Ruff: `All checks passed!`.
- Alembic: revisión `36344f288a54` aplicada y `alembic check` sin diferencias pendientes.

**Última verificación registrada del frontend (21/11/2026, Fase 3):**

- `npm run lint`: sin errores.
- `npm run build`: compilación TypeScript y build de Vite 8.3.0 completados.
- Pruebas funcionales manuales: consulta de pedidos y albaranes, enlaces entre documentos, creación y edición de borradores de factura, emisión con confirmación, visualización tras recarga e inmutabilidad de facturas emitidas. Se emitió una factura de prueba (`F-000001`) en el entorno local.

> La validación manual no sustituye pruebas automatizadas de interfaz ni verifica conformidad normativa. Los resultados del backend corresponden a la ejecución del 20/11/2026 y deben repetirse antes de la entrega si se modifican sus archivos.

Las migraciones se gestionan con Alembic. El último cambio de esquema registrado para facturas corresponde a la revisión `36344f288a54`; el estado efectivo de la base de datos debe comprobarse con:

```powershell
alembic current
alembic heads
alembic check
```

## Hoja de ruta

- [x] Autenticación y aislamiento multiempresa en el backend.
- [x] Gestión de productos, clientes, pedidos y albaranes en backend y frontend.
- [x] API de borradores y emisión de facturas.
- [x] Navegación lateral adaptable.
- [x] Paginación local de productos.
- [x] Fichas de detalle de pedidos, albaranes y facturas, con navegación entre documentos relacionados.
- [x] **Interfaz de facturas:** listado, filtros, detalle, creación y edición de borradores, emisión con confirmación y estados de carga/error.
- [ ] **Pagos:** modelo, migración, servicios, endpoints, pruebas y pantalla de cobros.
- [ ] **Mejoras transversales:** cliente HTTP único, cierre o redirección de sesión ante respuestas `401`, configuración de API y CORS por entorno, paginación/filtros compartidos, accesibilidad y validación UX.
- [ ] **Documentos:** generación de PDFs imprimibles de pedidos, albaranes y facturas, incorporando cuando proceda los elementos fiscales obligatorios.
- [ ] **Integración normativa:** analizar y desarrollar los registros de facturación, encadenamiento, huellas/hash, códigos QR, formatos, comunicaciones con la AEAT, gestión de respuestas y errores, conforme a las especificaciones aplicables.
- [ ] **Endurecimiento y entrega:** revisión de seguridad, pruebas de extremo a extremo, documentación operativa y despliegue de demostración adecuado al estado del proyecto.

## Alcance y uso previsto

El propósito actual es **educativo y de portfolio profesional**. Se utiliza para demostrar diseño de APIs, modelado de datos, arquitectura por capas, reglas de negocio, pruebas y desarrollo frontend. No se presenta como ERP completo, servicio de facturación listo para producción ni solución conforme a VERI\*FACTU.

## Autoría

Desarrollado por [ManRio](https://github.com/ManRio) como proyecto personal de desarrollo full stack.
