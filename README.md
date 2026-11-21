# VeriFactu App

**Aplicación de gestión comercial y facturación para pequeños negocios y autónomos.**

> [!IMPORTANT]
> **Proyecto en desarrollo.** La aplicación es un prototipo técnico y **no implementa ni acredita actualmente el cumplimiento de VERI\*FACTU** ni de todos los requisitos exigibles a un sistema informático de facturación (SIF). No debe utilizarse como solución fiscal conforme en un entorno real. La adaptación normativa y las pruebas correspondientes son tareas pendientes.

## Descripción

El proyecto modela un flujo comercial completo, desde la creación de un pedido hasta el cobro de una factura:

```text
Cliente → Pedido → Albarán → Factura → Pago
```

Su objetivo es desarrollar una aplicación modular, mantenible y multiempresa, poniendo el foco en las reglas de negocio, el control de estados, la trazabilidad de operaciones y la calidad del código. **El flujo de gestión está implementado hasta la emisión de facturas de prueba, tanto en backend como en frontend. La Fase 6 añade el registro manual de cobros totales y parciales, con saldo pendiente calculado e historial de anulaciones. No procesa dinero.**

La Fase 4 incorpora una **entrada pública de tipo SaaS** con registro de negocio, autenticación y planes mensuales **simulados**. No procesa tarjetas, cobros ni renovaciones automáticas.

La **Fase 5** añade la descarga de **PDF A4 de demostración** para pedidos, albaranes y facturas emitidas. Los archivos se generan bajo demanda desde el backend; no constituyen documentos fiscales conformes.

## Estado del desarrollo

| Módulo                         | Backend | Frontend | Estado                                                                                       |
| ------------------------------ | :-----: | :------: | -------------------------------------------------------------------------------------------- |
| Autenticación y usuarios       |   ✅    |    ✅    | Landing pública, registro de empresa, login, comprobación de sesión y redirección al caducar |
| Productos                      |   ✅    |    ✅    | Alta, edición, listado, activación/desactivación y paginación en cliente                     |
| Clientes                       |   ✅    |    ✅    | Gestión integrada                                                                            |
| Pedidos                        |   ✅    |    ✅    | Creación, edición de borradores, confirmación, cancelación y ficha de detalle                |
| Albaranes                      |   ✅    |    ✅    | Entregas parciales, control de cantidades y ficha de detalle                                 |
| Facturas                       |   ✅    |    ✅    | Listado, filtros, borradores, edición, emisión y consulta detallada                          |
| Suscripciones de demostración  |   ✅    |    ✅    | Planes ficticios, checkout sin tarjeta y consulta del período mensual                        |
| Documentos PDF de demostración |   ✅    |    ✅    | Descarga autenticada de pedidos, albaranes y facturas emitidas                               |
| Cobros de facturas (Fase 6)    |   ✅    |    ✅    | Registro manual de cobros, saldos parciales y totales, anulación auditable                   |
| Integración fiscal VERI\*FACTU |   ⏳    |    ⏳    | Pendiente de diseño, implementación y validación                                             |

**Leyenda:** ✅ implementado · 🟡 parcial · ⏳ pendiente. Los estados describen las funcionalidades presentes en el repositorio, no una certificación de preparación para producción.

### Funcionalidades implementadas

- **Seguridad y multiempresa:** autenticación con JWT, vinculación de recursos a `business_id` y aislamiento de datos entre empresas. Verificación de sesión mediante `GET /auth/me` y redirección al login cuando el token deja de ser válido.
- **Entrada comercial:** landing pública, registro de empresa con usuario administrador, elección de plan ficticio, checkout de demostración y pantalla «Mi suscripción».
- **Suscripciones demo:** persistencia por empresa en PostgreSQL; estado `PENDING` tras el registro y `DEMO_ACTIVE` tras el checkout; fecha de fin calculada a un mes natural. Los negocios existentes sin fila de suscripción mantienen compatibilidad. No se cobra dinero ni se gestionan tarjetas.
- **Productos y clientes:** creación, consulta y actualización; operaciones de activación/desactivación donde corresponda.
- **Pedidos:** líneas con datos comerciales históricos (_snapshots_), cálculo de base imponible, impuestos y total; estados `DRAFT`, `CONFIRMED` y `CANCELLED`. En la interfaz pueden abrirse fichas de detalle desde el listado.
- **Albaranes:** creación desde pedidos confirmados, entregas parciales y control de sobreentregas. Solo las entregas confirmadas consumen cantidad; cancelar un albarán confirmado libera esa cantidad cuando lo permiten las reglas de negocio. La ficha de detalle enlaza con el pedido de origen.
- **Facturas:** borradores a partir de uno o varios albaranes confirmados del mismo cliente, snapshots de emisor, receptor y líneas, cálculo de importes, emisión y numeración correlativa por serie. El frontend permite crear y editar borradores, consultar su detalle y emitirlos con confirmación. Las facturas emitidas no son editables mediante la API actual y se impide reutilizar albaranes ya facturados.
- **Cobros (Fase 6):** registro de transferencias, efectivo, tarjetas ya cobradas por otro medio y otros cobros; consulta de importes abonados y pendientes; anulación de registros sin eliminación del historial. No integra TPV ni pasarela bancaria.
- **Interfaz:** páginas de Productos, Clientes, Pedidos, Albaranes y Facturas; fichas de detalle y enlaces entre documentos relacionados; navegación lateral adaptable y paginación local de productos (10 por página).
- **Documentos PDF (Fase 5):** generación A4 con ReportLab, varias páginas cuando es necesario, datos de empresa y cliente, líneas y totales para pedidos y facturas. Los albaranes se presentan como justificantes de entrega sin importes. La factura solo ofrece descarga después de emitirse; todos los PDF llevan una advertencia de demostración.
- **Persistencia y calidad:** PostgreSQL, migraciones con Alembic y pruebas con Pytest en capas Repository, Service y API.

## Tecnologías

| Área              | Tecnologías                                                                |
| ----------------- | -------------------------------------------------------------------------- |
| Backend           | Python 3.13+, FastAPI, Pydantic, SQLAlchemy 2, Psycopg, Alembic, ReportLab |
| Seguridad         | PyJWT, Argon2                                                              |
| Base de datos     | PostgreSQL 17 (entorno Docker incluido)                                    |
| Frontend          | React 19, TypeScript, React Router 7, Vite 8, Tailwind CSS 4               |
| Pruebas y calidad | Pytest, Ruff, ESLint, TypeScript                                           |
| Entorno local     | Docker Compose, Python `venv`, npm                                         |

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

Se conservan snapshots de emisor, receptor y líneas, además de los importes calculados. El estado final implementado es `ISSUED`: **no existe todavía un flujo de rectificación o anulación fiscal**. Desde la Fase 5 se puede descargar un PDF de demostración de una factura emitida; **no equivale a una factura fiscalmente conforme**.

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

## Fase 5 — Descarga de documentos PDF (demostración)

Las fichas de detalle incluyen la acción **«Descargar PDF»**. FastAPI genera el archivo bajo demanda con **ReportLab** a partir de los datos almacenados en PostgreSQL, sin modificar el pedido, el albarán ni la factura.

| Documento       | Endpoint protegido                           | Contenido                                                                               |
| --------------- | -------------------------------------------- | --------------------------------------------------------------------------------------- |
| Pedido          | `GET /orders/{order_id}/pdf`                 | Emisor, cliente, líneas, cantidades, impuestos y total                                  |
| Albarán         | `GET /delivery-notes/{delivery_note_id}/pdf` | Emisor, destinatario, pedido de origen y cantidades entregadas; sin importes            |
| Factura emitida | `GET /invoices/{invoice_id}/pdf`             | Serie y número, fechas, datos históricos de emisor y cliente, líneas, impuestos y total |

El servidor exige autenticación JWT y autorización por empresa. La descarga de una factura en estado `DRAFT` se rechaza: solo se genera el PDF cuando la factura está en estado `ISSUED` y dispone de número y fecha de emisión. La respuesta utiliza `application/pdf`, descarga como adjunto y `Cache-Control: no-store, private`. Los PDF no se guardan como archivos en el servidor.

El formato es **A4 imprimible**, con paginación para documentos largos y marca visible de **demostración**. No se generan registros fiscales, códigos QR normativos ni comunicaciones con la AEAT. **Estos PDF no deben emplearse como documentación fiscal real** ni presentarse como documentos conformes con VERI\*FACTU.

Para instalar ReportLab con las dependencias del proyecto (desde `backend`, con el entorno virtual activado):

```powershell
python -m pip install -e ".[dev]"
```

**Esta fase no necesita migración de PostgreSQL.**

## Landing, sesiones y contratación simulada

### Recorrido de un nuevo negocio

```text
Landing pública (/) → Registro (/register) → Checkout simulado (/checkout)
       → Panel de gestión (/products) → Mi suscripción (/subscription)
```

- **Landing (`/`):** presenta características y precios ilustrativos, con acceso a registro e inicio de sesión.
- **Registro (`/register`):** envía `POST /auth/register` y crea empresa, primer usuario y suscripción `PENDING` en la misma transacción. El usuario recibe un JWT para continuar al checkout.
- **Login (`/login`):** utiliza `POST /auth/login`. El guard de rutas privadas comprueba localmente la expiración del JWT y consulta `GET /auth/me` para validar la sesión en el servidor.
- **Checkout (`/checkout`):** activa uno de los planes ficticios con `POST /subscriptions/demo-checkout`, sin introducir tarjeta ni procesar pagos.
- **Mi suscripción (`/subscription`):** consulta el plan actual, fecha de activación y fin del período mediante `GET /subscriptions/me`.

| Plan demo   | Código    | Precio ilustrativo | Cobro real |
| ----------- | --------- | -----------------: | ---------- |
| Inicio      | `STARTER` |        12,90 €/mes | **0 €**    |
| Profesional | `PRO`     |        24,90 €/mes | **0 €**    |

La activación fija el siguiente vencimiento en **un mes natural**; no hay renovación automática, recibos ni pasarela de pago. Cambiar de plan o volver a activarlo reinicia el período de demostración en el estado actual del prototipo.

### Endpoints de la Fase 4

| Método | Ruta                           | Acceso      | Función                                                  |
| ------ | ------------------------------ | ----------- | -------------------------------------------------------- |
| `POST` | `/auth/register`               | Público     | Registrar negocio, administrador y suscripción pendiente |
| `POST` | `/auth/login`                  | Público     | Obtener JWT                                              |
| `GET`  | `/auth/me`                     | Autenticado | Validar sesión y consultar usuario                       |
| `GET`  | `/subscriptions/plans`         | Público     | Consultar planes de demostración                         |
| `GET`  | `/subscriptions/me`            | Autenticado | Consultar la suscripción de la empresa                   |
| `POST` | `/subscriptions/demo-checkout` | Autenticado | Activar un plan simulado, sin cobro                      |

El backend exige un plan `DEMO_ACTIVE` no caducado en las rutas que utilizan la dependencia `get_current_business_id`, devolviendo `402` si falta o ha caducado. **Este control aún no es una autorización de licencias exhaustiva:** deben revisarse las demás rutas y dependencias antes de cualquier despliegue público. Las empresas anteriores que no tengan registro de suscripción pueden seguir accediendo al panel.

El frontend comparte la URL de API mediante `VITE_API_URL` y una función HTTP común que gestiona respuestas `401` y redirige al checkout ante determinadas respuestas `402`. **El JWT sigue almacenándose en `localStorage`.** Antes de producción harán falta, entre otras medidas, sesiones seguras, revocación/renovación, recuperación de contraseña, rate limiting, protección CSRF cuando corresponda y pruebas de autorización de extremo a extremo.

## Fase 6 — Cobros manuales de facturas

El módulo `/payments` registra **cobros recibidos fuera de la aplicación** (contabilidad auxiliar),
no procesa transacciones bancarias ni tarjetas. Solo admite movimientos sobre **facturas emitidas**
y **no modifica los importes, la numeración ni el estado `ISSUED` de la factura**.

- Cobros parciales o completos en EUR con `Decimal(12,2)`, fecha, medio, referencia y notas.
- Saldos calculados desde movimientos `RECORDED`; estados `UNPAID`, `PARTIAL` y `PAID`.
- Anulación de registros erróneos con motivo obligatorio, usuario y fecha, conservando el movimiento original.
- Imposibilidad de superar el saldo pendiente, con bloqueo transaccional de la factura para evitar carreras concurrentes.
- Aislamiento por empresa autenticada y verificación de suscripción demo mediante las dependencias existentes.
- Vista de Cobros y sección de movimientos dentro del detalle de cada factura emitida.

| Método | Endpoint                          | Descripción                                      |
| ------ | --------------------------------- | ------------------------------------------------ |
| `GET`  | `/payments`                       | Saldos de las facturas emitidas de la empresa    |
| `GET`  | `/payments/invoices/{invoice_id}` | Estado e historial de movimientos de una factura |
| `POST` | `/payments`                       | Registrar un cobro ya recibido                   |
| `POST` | `/payments/{payment_id}/void`     | Anular movimiento, preservando su auditoría      |

La migración **`c64d9f20e4a1`** incorpora la tabla `payments`. Este módulo no efectúa
cargos ni transferencias, no devuelve dinero y no realiza conciliación bancaria automática.
Los cobros de facturas de clientes son independientes de las suscripciones SaaS simuladas.

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

Interfaz local: `http://localhost:5173`. Vite está configurado con `strictPort: true`: si el puerto está ocupado, se detiene en vez de pasar silenciosamente a `5174`. FastAPI permite en desarrollo los orígenes `localhost`/`127.0.0.1` en los puertos `5173` y `5174`.

Abre la landing en `/`, crea una empresa desde `/register`, completa el plan ficticio en `/checkout` y entra en el panel. Los negocios anteriores a la Fase 4 conservan su acceso. **Mantén Uvicorn ejecutándose en otra terminal**: `pytest` no deja el servidor iniciado.

Para usar otra URL de API, copia `frontend/.env.example` a `frontend/.env` y ajusta `VITE_API_URL`. No incluyas secretos en variables `VITE_*`, ya que forman parte del código entregado al navegador.

Comprobaciones adicionales del frontend:

```powershell
npm run lint
npm run build
```

> El frontend emplea `VITE_API_URL` (predeterminado: `http://127.0.0.1:8000`) y una función HTTP común para detectar sesiones no válidas. No equivale a una arquitectura de autenticación lista para producción.

## Pruebas y migraciones

El backend cuenta con pruebas automatizadas en capas Repository, Service y API.

**Última verificación registrada del backend (21/11/2026, Fase 4):**

- Pytest: **380 pruebas superadas**, con 1 warning conocido de compatibilidad entre Starlette TestClient y `httpx`.
- Ruff: `All checks passed!` tras ordenar las importaciones.
- Alembic: migración `b8f43c12ad90` (`add demo subscriptions`) aplicada y `alembic check` sin operaciones nuevas.
- La prueba de la dependencia de empresa se actualizó para proporcionar una sesión de SQLAlchemy simulada; se añadieron comprobaciones de suscripción pendiente y activa.

**Última verificación registrada del frontend (21/11/2026, Fase 4):**

- `npm run lint`: sin errores.
- `npm run build`: compilación TypeScript y build de Vite 8.3.0 completados.
- Fase 3: consulta de pedidos y albaranes, enlaces entre documentos, borradores y emisión de facturas de prueba; se emitió `F-000001` en local.
- Fase 4: comprobaciones manuales satisfactorias de landing, registro, checkout simulado, acceso al panel, «Mi suscripción», cierre y reinicio de sesión, compatibilidad del usuario anterior y redirección de sesión caducada.

**Validación funcional manual de Fase 5 (21/11/2026):** seis comprobaciones satisfactorias de descarga y contenido de PDF para pedidos, albaranes y facturas emitidas, incluida la restricción de borradores. La fase incorporó pruebas automatizadas adicionales de PDF, autenticación y autorización.

**Última ejecución comunicada del backend (21/11/2026, Fase 6):**

- Pytest: **396 pruebas superadas**, con 1 advertencia conocida de Starlette TestClient y `httpx`.
- Alembic: migración `c64d9f20e4a1` (`add invoice payments`) aplicada; `alembic current` muestra esa revisión como `head` y `alembic check` indica `No new upgrade operations detected`.
- Ruff: la primera ejecución detectó dos ajustes automáticos (`I001` y `PLR1730`) en el módulo de pagos. **Pendiente de confirmar el resultado de la nueva ejecución de `ruff check .` después de `ruff check . --fix`.**
- Frontend Fase 6: **pendiente de adjuntar las salidas finales** de `npm run lint` y `npm run build` tras esta integración.
- Pruebas manuales: **6 comprobaciones funcionales realizadas satisfactoriamente**, que incluyen cobro parcial, cobro total, rechazo del exceso de cobro y anulación conservando el historial.

> Las comprobaciones manuales no sustituyen las pruebas automatizadas E2E, una auditoría de seguridad ni la verificación normativa. Las 396 pruebas corresponden a la ejecución del backend tras integrar la Fase 6; las verificaciones finales de Ruff y del frontend se deben completar antes del commit.

Las migraciones se gestionan con Alembic: `36344f288a54` introduce la facturación, `b8f43c12ad90` añade `subscriptions` y `c64d9f20e4a1` incorpora `payments`. El esquema efectivo se comprueba con:

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
- [x] **Fase 4 — experiencia SaaS demo:** landing, registro, checkout ficticio, pantalla de suscripción, validación de sesión y migración de suscripciones.
- [x] **Calidad de Fase 4:** 380 pruebas backend, lint y build frontend, y validación funcional manual.
- [x] **Fase 5 — PDF de demostración:** generación y descarga protegida de pedidos, albaranes y facturas emitidas.
- [x] **Fase 6 — Cobros:** modelo, migración, registro de cobros manuales, control de saldos, historial de anulaciones, endpoints y pantalla de gestión.
- [ ] **Cobros futuros:** importación de extractos, conciliación bancaria, devoluciones reales y documentación de recibos.
- [ ] **Mejoras transversales:** revisar autorización por suscripción en todas las rutas; sesiones con cookies seguras y renovación/revocación; recuperación de contraseña; controles de abuso; paginación, accesibilidad y pruebas E2E.
- [ ] **Documentación fiscal:** adaptación de los documentos, QR y elementos normativos que resulten exigibles antes del uso real.
- [ ] **Integración normativa:** analizar y desarrollar los registros de facturación, encadenamiento, huellas/hash, códigos QR, formatos, comunicaciones con la AEAT, gestión de respuestas y errores, conforme a las especificaciones aplicables.
- [ ] **Endurecimiento y entrega:** revisión de seguridad, pruebas de extremo a extremo, documentación operativa y despliegue de demostración adecuado al estado del proyecto.

## Alcance y uso previsto

El propósito actual es **educativo y de portfolio profesional**. Se utiliza para demostrar diseño de APIs, modelado de datos, arquitectura por capas, reglas de negocio, pruebas y desarrollo frontend. La contratación SaaS es una simulación sin pagos; los cobros de facturas son anotaciones manuales de importes supuestamente recibidos por otros medios, no transacciones procesadas ni verificadas por esta aplicación. No se presenta como ERP completo, servicio de facturación listo para producción ni solución conforme a VERI\*FACTU.

## Autoría

Desarrollado por [ManRio](https://github.com/ManRio) como proyecto personal de desarrollo full stack.
