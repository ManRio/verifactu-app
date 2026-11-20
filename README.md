# VeriFactu App

**Aplicación de gestión comercial y facturación para pequeños negocios y autónomos.**

> [!IMPORTANT]
> **Proyecto en desarrollo.** La aplicación es un prototipo técnico y **no implementa ni acredita actualmente el cumplimiento de VERI\*FACTU** ni de todos los requisitos exigibles a un sistema informático de facturación (SIF). No debe utilizarse como solución fiscal conforme en un entorno real. La adaptación normativa y las pruebas correspondientes son tareas pendientes.

## Descripción

El proyecto modela un flujo comercial completo, desde la creación de un pedido hasta el cobro de una factura:

```text
Cliente → Pedido → Albarán → Factura → Pago
```

Su objetivo es desarrollar una aplicación modular, mantenible y multiempresa, poniendo el foco en las reglas de negocio, el control de estados, la trazabilidad de operaciones y la calidad del código. **El flujo está completado hasta albaranes en la interfaz; facturas dispone de backend, mientras que pagos todavía está pendiente.**

## Estado del desarrollo

| Módulo                         | Backend | Frontend | Estado                                                                   |
| ------------------------------ | :-----: | :------: | ------------------------------------------------------------------------ |
| Autenticación y usuarios       |   ✅    |    🟡    | Registro y acceso vía API; pantalla de inicio de sesión                  |
| Productos                      |   ✅    |    ✅    | Alta, edición, listado, activación/desactivación y paginación en cliente |
| Clientes                       |   ✅    |    ✅    | Gestión integrada                                                        |
| Pedidos                        |   ✅    |    ✅    | Borradores, confirmación, cancelación y cálculo de importes              |
| Albaranes                      |   ✅    |    ✅    | Entregas parciales y control de cantidades                               |
| Facturas                       |   ✅    |    ⏳    | API implementada; interfaz pendiente                                     |
| Pagos                          |   ⏳    |    ⏳    | Pendiente                                                                |
| Integración fiscal VERI\*FACTU |   ⏳    |    ⏳    | Pendiente de diseño, implementación y validación                         |

**Leyenda:** ✅ implementado · 🟡 parcial · ⏳ pendiente. Los estados describen las funcionalidades presentes en el repositorio, no una certificación de preparación para producción.

### Funcionalidades implementadas

- **Seguridad y multiempresa:** autenticación con JWT, vinculación de recursos a `business_id` y aislamiento de datos entre empresas.
- **Productos y clientes:** creación, consulta y actualización; operaciones de activación/desactivación donde corresponda.
- **Pedidos:** líneas con datos comerciales históricos (_snapshots_), cálculo de base imponible, impuestos y total; estados `DRAFT`, `CONFIRMED` y `CANCELLED`.
- **Albaranes:** creación desde pedidos confirmados, entregas parciales y control de sobreentregas. Solo las entregas confirmadas consumen cantidad; cancelar un albarán confirmado libera esa cantidad cuando lo permiten las reglas de negocio.
- **Facturas (backend):** borradores a partir de uno o varios albaranes confirmados del mismo cliente, snapshots de emisor, receptor y líneas, cálculo de importes, emisión y asignación de número correlativo por serie. Las facturas emitidas no se pueden editar mediante la API actual y se impide reutilizar albaranes ya facturados.
- **Interfaz:** páginas de Productos, Clientes, Pedidos y Albaranes; navegación lateral adaptable y paginación local de productos (10 por página).
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

### Facturas — backend implementado

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

La interfaz de facturación todavía no está desarrollada.

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

- **API:** `http://127.0.0.1:8000`
- **Documentación interactiva:** `http://127.0.0.1:8000/docs`
- **Comprobación básica:** `http://127.0.0.1:8000/health`

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

Interfaz local: `http://localhost:5173`.

Para iniciar sesión, registra primero una empresa y su usuario mediante `POST /auth/register` en la documentación interactiva de la API. Después utiliza la página `/login`.

Comprobaciones adicionales del frontend:

```powershell
npm run lint
npm run build
```

> Actualmente los servicios del frontend emplean direcciones locales de API definidas en código (`localhost:8000` y `127.0.0.1:8000`). Centralizar esta configuración mediante variables de entorno es una mejora pendiente antes de desplegar.

## Pruebas y migraciones

Hay tests de Repository, Service y API para los principales módulos comerciales. En una ejecución registrada durante el desarrollo se informaron **371 pruebas superadas**, pero **ese resultado no se ha vuelto a ejecutar ni verificado como parte de esta actualización del README**. Para conocer el estado real, ejecuta `pytest -q` en tu entorno local.

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
- [ ] **Interfaz de facturas:** listado, detalle, creación y edición de borradores, emisión, errores y estados.
- [ ] **Pagos:** modelo, migración, servicios, endpoints, pruebas y pantalla de cobros.
- [ ] **Mejoras transversales:** cliente HTTP único, configuración de API por entorno, paginación/filtros compartidos, accesibilidad y validación UX.
- [ ] **Documentos:** generación de facturas PDF y, cuando proceda, sus elementos fiscales obligatorios.
- [ ] **Integración normativa:** analizar y desarrollar los registros de facturación, encadenamiento, huellas/hash, códigos QR, formatos, comunicaciones con la AEAT, gestión de respuestas y errores, conforme a las especificaciones aplicables.
- [ ] **Endurecimiento y entrega:** revisión de seguridad, pruebas de extremo a extremo, documentación operativa y despliegue de demostración adecuado al estado del proyecto.

## Alcance y uso previsto

El propósito actual es **educativo y de portfolio profesional**. Se utiliza para demostrar diseño de APIs, modelado de datos, arquitectura por capas, reglas de negocio, pruebas y desarrollo frontend. No se presenta como ERP completo, servicio de facturación listo para producción ni solución conforme a VERI\*FACTU.

## Autoría

Desarrollado por [ManRio](https://github.com/ManRio) como proyecto personal de desarrollo full stack.
