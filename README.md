# VeriFactu App

**Aplicación de gestión comercial y facturación para pequeños negocios y autónomos.**

> [!IMPORTANT]
> **Proyecto en desarrollo.** La aplicación es un prototipo técnico y **no implementa ni acredita actualmente el cumplimiento de VERI\*FACTU** ni de todos los requisitos exigibles a un sistema informático de facturación (SIF). No debe utilizarse como solución fiscal conforme en un entorno real. La adaptación normativa y las pruebas correspondientes son tareas pendientes.

## Descripción

VeriFactu App es un **prototipo full stack de gestión comercial y facturación multiempresa** orientado a pequeños negocios y autónomos. Su flujo principal es:

```text
Cliente → Pedido → Albarán → Factura emitida → Cobro manual
```

Incluye gestión de productos y clientes; entregas parciales; facturación numerada por series; PDF A4 de prueba; cobros parciales y anulaciones auditables; acceso mediante usuarios y roles; verificación de email; suscripciones simuladas por número de trabajadores; y un panorama económico con facturación, caja, pendientes y artículos más vendidos.

**Estado a 23/11/2026: fases 1–8 de demostración implementadas y comprobadas localmente.** La integración fiscal con **VERI\*FACTU / AEAT es la siguiente línea de desarrollo**. Las suscripciones no cobran dinero; los cobros de clientes son registros manuales de pagos que supuestamente han ocurrido por otros medios.

## Estado del desarrollo

| Módulo                                   | Backend | Frontend | Estado                                                         |
| ---------------------------------------- | :-----: | :------: | -------------------------------------------------------------- |
| Registro, login y verificación de correo |   ✅    |    ✅    | Acceso unificado y enlace de activación de un solo uso         |
| Usuarios y roles por empresa             |   ✅    |    ✅    | `SUPERUSER` / `WORKER`, invitación, activación y desactivación |
| Productos y clientes                     |   ✅    |    ✅    | Gestión, búsqueda y listados paginados                         |
| Pedidos y albaranes                      |   ✅    |    ✅    | Borradores, confirmaciones, entregas parciales y trazabilidad  |
| Facturas                                 |   ✅    |    ✅    | Borradores, edición, emisión, numeración y detalle             |
| PDF A4 de demostración                   |   ✅    |    ✅    | Pedidos, albaranes y facturas emitidas                         |
| Cobros manuales                          |   ✅    |    ✅    | Abonos parciales/totales, saldos y anulaciones auditables      |
| Planes SaaS simulados                    |   ✅    |    ✅    | Límites de 0/5/10 trabajadores, sin pagos reales               |
| Panorama económico                       |   ✅    |    ✅    | Indicadores mensuales, tendencia y ranking de productos        |
| Integración fiscal VERI\*FACTU           |   ⏳    |    ⏳    | Pendiente de diseño normativo, desarrollo y validación         |

**Leyenda:** ✅ implementado en la demo · ⏳ pendiente. No implica certificación normativa ni preparación para producción.

### Funcionalidades principales

- **Aislamiento multiempresa:** las operaciones se relacionan con el `business_id` de la sesión; el backend aplica controles de autorización.
- **Acceso (Fases 7A–7B):** pantalla unificada y animada para login y registro, validaciones y visibilidad de contraseñas. Los nuevos usuarios deben verificar su correo antes de iniciar sesión.
- **Roles:** el propietario es `SUPERUSER` y administra trabajadores, plan y panorama económico. Los usuarios `WORKER` realizan operaciones comerciales, pero no pueden acceder a los endpoints administrativos. Ocultar enlaces en el frontend no sustituye la autorización en FastAPI.
- **Usuarios:** el propietario invita trabajadores por email; el destinatario activa su cuenta y define su contraseña. Las invitaciones pendientes cuentan para el límite del plan; desactivar una cuenta libera plaza.
- **Comercial:** productos, clientes, pedidos, albaranes confirmados, facturas emitidas por serie, PDF y cobros manuales. Se mantienen los estados y snapshots históricos de documentos.
- **Suscripciones:** los tres planes y sus límites se aplican en el backend; el checkout únicamente simula una activación mensual y no tiene pasarela de pago.
- **Panorama económico:** consulta por mes, facturación de facturas emitidas, caja por fecha de cobro, deuda pendiente, porcentaje cobrado, tendencia y artículos más vendidos.
- **Calidad:** PostgreSQL 17, Alembic, suite Pytest y análisis estático Ruff/ESLint/TypeScript.

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

## Registro, sesiones y planes simulados

### Recorrido de un negocio nuevo

```text
Landing (/) → Acceder (/login: login o registro) → Verificar correo (/verify-email)
→ Login → Seleccionar plan demo (/checkout) → Panel comercial
```

El registro crea la empresa, el primer usuario `SUPERUSER` y una suscripción inicialmente `PENDING`, pero **no entrega un JWT utilizable hasta que el correo esté verificado y el usuario inicie sesión**. Los enlaces de verificación son de un solo uso, caducan a las 24 horas y el token se almacena como hash. Los usuarios históricos conservan acceso según la migración de Fase 7B.

| Plan    | Código interno | Superusuarios | Trabajadores activos o invitados | Precio de demostración |
| ------- | -------------- | ------------: | -------------------------------: | ---------------------: |
| Inicio  | `STARTER`      |             1 |                                0 |            12,90 €/mes |
| Equipo  | `PRO`          |             1 |                          Hasta 5 |            24,90 €/mes |
| Empresa | `BUSINESS`     |             1 |                         Hasta 10 |            39,90 €/mes |

Estos **precios son ficticios** y la cuota efectivamente cobrada es **0 €**. El código `PRO` se conserva por compatibilidad. Cambiar a un plan inferior se rechaza si las cuentas activas o invitadas superan su cupo; la invitación o reactivación de trabajadores también se bloquea cuando no quedan plazas. La suscripción demo dura un mes natural, sin renovación ni pago automático.

| Método  | Ruta                           | Uso                                              |
| ------- | ------------------------------ | ------------------------------------------------ |
| `POST`  | `/auth/register`               | Registrar empresa con verificación pendiente     |
| `POST`  | `/auth/verify-email`           | Confirmar email / completar activación           |
| `POST`  | `/auth/login`                  | Obtener JWT tras verificar la cuenta             |
| `GET`   | `/auth/me`                     | Consultar sesión y rol                           |
| `GET`   | `/subscriptions/plans`         | Consultar planes disponibles                     |
| `GET`   | `/subscriptions/me`            | Consultar plan y ocupación de plazas             |
| `POST`  | `/subscriptions/demo-checkout` | Activar/cambiar plan ficticio (superusuario)     |
| `GET`   | `/users`                       | Listar trabajadores de la empresa (superusuario) |
| `POST`  | `/users`                       | Invitar trabajador (superusuario)                |
| `PATCH` | `/users/{user_id}/status`      | Activar/desactivar trabajador (superusuario)     |

**Seguridad pendiente:** el JWT se guarda actualmente en `localStorage`; faltan sesiones endurecidas, recuperación de contraseña, protección antiabuso, políticas de secretos y pruebas E2E de seguridad. Una empresa antigua sin fila de suscripción conserva una compatibilidad temporal. Los trabajadores pueden visualizar facturas y cobros individuales; aunque no tengan acceso al resumen agregado, eso no constituye confidencialidad contable estricta.

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

## Fases 7A–7B — Experiencia y permisos

**Fase 7A:** interfaz de acceso unificado, validaciones y errores legibles, búsqueda y paginación en los listados, cantidades enteras para el flujo de productos y mejoras de selección de líneas en albaranes. Se corrigieron problemas de edición de borradores de factura y de relaciones entre documentos.

**Fase 7B:** roles `SUPERUSER` y `WORKER`, invitaciones, activación y verificación de email y protección de rutas administrativas en el backend. La migración `f7b20c81a611` asigna el rol `SUPERUSER` al primer usuario existente de cada empresa y `WORKER` a los demás, conservando las cuentas antiguas como verificadas. En empresas con varios usuarios históricos se deben revisar los roles asignados.

### Configuración de correo en desarrollo

Edita el `.env` de la **raíz del proyecto**:

```dotenv
APP_ENVIRONMENT=development
FRONTEND_BASE_URL=http://localhost:5173
EMAIL_BACKEND=console
```

En este modo, la URL de activación se imprime en la consola de Uvicorn, **sin enviar un correo real**. No compartas tokens, enlaces ni trazas de activación.

Para correo real puede configurarse `EMAIL_BACKEND=smtp` y las variables `SMTP_HOST`, `SMTP_PORT`, `SMTP_FROM`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_STARTTLS` y `SMTP_SSL`; los secretos deben permanecer fuera de Git. En producción, el backend `console` no está permitido. Todavía faltan colas de entrega/outbox, observabilidad y controles antiabuso para un despliegue real.

## Fase 8 — Plazas por plan y panorama económico

El superusuario gestiona la capacidad de trabajadores desde `/users` y consulta el panel en `/accounting`, alimentado por `GET /reports/summary?month=AAAA-MM`. El backend comprueba las plazas durante la invitación, reactivación y cambio de plan; los roles se validan igualmente en la API.

| Indicador                   | Definición                                                                             |
| --------------------------- | -------------------------------------------------------------------------------------- |
| Facturado del mes           | Total con IVA de facturas `ISSUED` cuya `issue_date` pertenece al mes                  |
| Caja del mes                | Total de cobros `RECORDED` cuya `payment_date` pertenece al mes                        |
| Cobrado de facturas del mes | Cobros vigentes imputados a las facturas emitidas en el mes, aunque se cobren después  |
| Pendiente del mes           | Saldo actual de las facturas emitidas ese mes                                          |
| Pendiente total             | Saldo de todas las facturas emitidas que siguen sin liquidarse                         |
| Desviación de flujo         | Facturado del mes menos caja del mes; **no equivale a deuda pendiente**                |
| Productos más vendidos      | Unidades de las líneas de facturas emitidas ese mes, sin duplicar pedidos ni albaranes |
| Evolución                   | Comparación mensual de facturación y cobros durante seis meses                         |

No es un libro mayor, contabilidad oficial, conciliación bancaria ni un módulo fiscal. Todos los cobros se introducen manualmente.

## Datos sintéticos de demostración — NovaGest 2026

El script opcional `demo_novagest_2026/seed.py` permite preparar un entorno **local de desarrollo** para una tienda ficticia de recambios de automóvil. Solo actúa si existen dos cuentas de prueba, verificadas y activas, dentro de la misma empresa NovaGest. No crea usuarios, ni altera roles, contraseñas o suscripciones.

| Recurso                                   | Volumen del lote |
| ----------------------------------------- | ---------------: |
| Referencias de producto                   |              100 |
| Clientes                                  |               48 |
| Pedidos / albaranes                       |        292 / 260 |
| Facturas (emitidas / totales)             |        217 / 234 |
| Movimientos de cobro (incluidos anulados) |              242 |

Los datos cubren **enero a 23 de noviembre de 2026** e incluyen cobros completos, parciales y deuda pendiente para mostrar gráficos realistas. La serie `D26` y los SKU con prefijo `DEM26-` distinguen el lote de los datos anteriores. Son registros ficticios, no facturas fiscales reales ni operaciones comunicadas a la AEAT.

Si incluyes este script opcional en tu copia del repositorio, la guía detallada está en `demo_novagest_2026/LEEME.md`. Su uso recomendado desde la raíz es:

```powershell
python .\demo_novagest_2026\seed.py --preview
python .\demo_novagest_2026\seed.py --dry-run
# Solo tras confirmar la base local y tener copia de seguridad:
python .\demo_novagest_2026\seed.py --apply --confirm NOVAGEST_DEMO_2026
python .\demo_novagest_2026\seed.py --verify
```

El script restringe conexiones a PostgreSQL local y `APP_ENVIRONMENT=development`, comprueba la empresa destino y evita la carga duplicada. Inserta en una sola transacción. Su ejecución en la base local **no forma parte de las 407 pruebas de Pytest** y debe verificarse por separado.

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

Edita el archivo **`.env` en la raíz del repositorio** y configura las variables de correo de desarrollo indicadas en Fase 7B. Si utilizas el `docker-compose.yml` incluido, configura `POSTGRES_PASSWORD=verifactu_dev`, porque ese es el valor utilizado por el contenedor de desarrollo. Ajusta también `JWT_SECRET_KEY` con un secreto local propio, robusto y no compartido.

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

Abre la landing en `/`, utiliza **Acceder** para abrir el login/registro unificados en `/login`, verifica el email con la URL mostrada por Uvicorn, inicia sesión y activa un plan ficticio desde `/checkout`. Los negocios anteriores a la Fase 4 conservan su acceso. **Mantén Uvicorn ejecutándose en otra terminal**: `pytest` no deja el servidor iniciado.

Para usar otra URL de API, copia `frontend/.env.example` a `frontend/.env` y ajusta `VITE_API_URL`. No incluyas secretos en variables `VITE_*`, ya que forman parte del código entregado al navegador.

Comprobaciones adicionales del frontend:

```powershell
npm run lint
npm run build
```

> El frontend emplea `VITE_API_URL` (predeterminado: `http://127.0.0.1:8000`) y una función HTTP común para detectar sesiones no válidas. No equivale a una arquitectura de autenticación lista para producción.

## Pruebas y migraciones

**Última verificación comunicada: 23/11/2026, después de la Fase 8 y sus correcciones.**

| Comprobación                | Resultado                                                                         |
| --------------------------- | --------------------------------------------------------------------------------- |
| Pytest, backend             | **407 passed, 1 warning**                                                         |
| Ruff, backend               | `All checks passed!`                                                              |
| Alembic                     | `f7b20c81a611 (head)`; `No new upgrade operations detected`                       |
| ESLint, frontend            | Sin errores                                                                       |
| TypeScript y Vite, frontend | `npm run build` correcto                                                          |
| Pruebas manuales            | Flujos de usuarios, permisos, planes y panorama económico revisados en desarrollo |

El único aviso de Pytest procede de una deprecación en la combinación Starlette TestClient / `httpx`. Las verificaciones manuales son indicativas; faltan una suite E2E completa, auditoría de seguridad y cualquier validación normativa.

**Revisiones relevantes de Alembic:** `36344f288a54` (facturación), `b8f43c12ad90` (suscripciones demo), `c64d9f20e4a1` (cobros) y `f7b20c81a611` (roles y verificación de correo). La Fase 8 no añade migración.

Ejecuta desde `backend` y con PostgreSQL local activo:

```powershell
ruff check .
pytest -q
alembic current
alembic check
```

Y desde `frontend`:

```powershell
npm run lint
npm run build
```

**Nunca ejecutes los tests de integración contra una base de datos de producción.**

## Hoja de ruta

- [x] **Fases 1–3:** arquitectura multiempresa, productos y clientes, pedidos, albaranes, facturas y frontend de gestión.
- [x] **Fase 4:** landing y suscripciones de demostración.
- [x] **Fase 5:** PDF A4 de prueba para documentos comerciales.
- [x] **Fase 6:** cobros manuales, saldos y auditoría de anulaciones.
- [x] **Fase 7A:** UX, acceso unificado, filtros y mejoras de formularios.
- [x] **Fase 7B:** roles, permisos administrativos y verificación de correo.
- [x] **Fase 8:** límites por plan y panorama económico mensual.
- [x] **Calidad técnica:** 407 tests superados; Ruff, Alembic, lint y build correctos (23/11/2026).
- [ ] **Siguiente fase: integración fiscal VERI\*FACTU.** Analizar requisitos técnicos vigentes y especificaciones oficiales de la AEAT; diseñar registros de facturación, encadenamiento, huellas, QR, comunicación, gestión de respuestas, errores y trazabilidad, con pruebas y revisión legal/técnica.
- [ ] **Seguridad para producción:** SMTP transaccional robusto, protección frente a abuso, sesiones y cookies seguras, recuperación de contraseña, permisos granulares, auditoría, pruebas E2E y revisión de despliegue.
- [ ] **Operativa financiera avanzada:** conciliación bancaria, importación de movimientos y, si se decide implementarlos, cobros electrónicos reales.

## Alcance y uso previsto

El propósito actual es **educativo, de demostración y de portfolio profesional**. Se utiliza para demostrar diseño de APIs, modelado de datos, arquitectura por capas, reglas de negocio, pruebas y desarrollo frontend. La contratación SaaS es una simulación sin pagos; los cobros de facturas son anotaciones manuales de importes supuestamente recibidos por otros medios, no transacciones procesadas ni verificadas por esta aplicación. No se presenta como ERP completo, servicio listo para producción ni sistema conforme a VERI\*FACTU. La integración fiscal sigue pendiente.

## Autoría

Desarrollado por [ManRio](https://github.com/ManRio) como proyecto personal de desarrollo full stack.
