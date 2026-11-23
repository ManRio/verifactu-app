# NovaGest 2026 — Datos sintéticos de demostración

Cargador **local, de una sola aplicación**, para la VeriFactu App (Fase 8).

## Destino exclusivo

Busca estas dos cuentas **existentes**:

- `daniel.novagest@example.com` → `SUPERUSER`
- `laura.novagest@example.com` → `WORKER`

Antes de escribir comprueba que ambas existen, tienen el correo verificado, están activas, pertenecen al **mismo `business_id`** y la empresa se identifica como **NovaGest**. **No crea ni modifica usuarios, contraseñas, suscripciones, permisos ni otras empresas.** Los dos usuarios verán la misma información, sujeta a los permisos de Fase 8.

**Seguridad:** bloquea `APP_ENVIRONMENT` distinto de `development` y conexiones PostgreSQL que no sean locales; requiere una confirmación literal antes de insertar. No es un script para entornos de producción. Haz copia de la base local antes de ejecutarlo si deseas conservar el estado previo.

## Qué genera

| Recurso | Registros |
|---|---:|
| Productos / recambios | **100** referencias, en diez familias |
| Clientes (talleres y pequeños negocios ficticios) | **48** |
| Pedidos | **292** |
| Líneas de pedido | **811** |
| Albaranes | **260** |
| Líneas de albarán | **720** |
| Facturas (emitidas + borradores) | **234** |
| Facturas **emitidas** | **217** |
| Líneas de factura | **646** |
| Movimientos de cobro, incluidos algunos anulados | **242** |

Todas las fechas se sitúan entre enero y el **23 de noviembre de 2026**. Los pedidos se distribuyen por meses, con variación estacional, diferentes cantidades de recambios, pendientes de preparación, albaranes pendientes y facturas en borrador. Las facturas emitidas pueden quedar pagadas, parcialmente cobradas o sin cobrar. Los métodos registrados son transferencia, tarjeta, efectivo y otros; **son apuntes de prueba, no transacciones reales**.

**Importes sintéticos aproximados (solo lote generado):** 132.539,72 € facturados; 107.486,29 € cobrados; 25.053,43 € pendientes. Pueden variar las cifras del panel si la empresa ya contiene otras operaciones previas.

Los productos contienen nombres y precios plausibles de recambios, pero **no son referencias comerciales verificadas ni garantizan compatibilidad con vehículos**. El IVA aplicado en el juego de datos es el 21 %.

## Instalación en Windows / VS Code

1. Descomprime la carpeta `demo_novagest_2026` **en la raíz** `verifactu-app`, a la misma altura que `backend` y `frontend`.
2. Verifica que Docker/PostgreSQL esté activo y que el `.env` raíz configure `APP_ENVIRONMENT=development` y una base local.
3. Abre PowerShell en la **raíz** del repositorio y activa el venv del backend si aún no está activo:

```powershell
.\backend\.venv\Scripts\Activate.ps1
# Solo si la base no está levantada:
docker compose up -d postgres
```

4. Vista preliminar **sin conexión a base de datos**:

```powershell
python .\demo_novagest_2026\seed.py --preview
```

5. Preflight de conexión, roles, empresa, serie disponible y duplicados. **No escribe datos**:

```powershell
python .\demo_novagest_2026\seed.py --dry-run
```

6. **Solo si el resultado anterior es correcto**, aplicar una vez, de manera atómica:

```powershell
python .\demo_novagest_2026\seed.py --apply --confirm NOVAGEST_DEMO_2026
```

7. Revisar después el lote existente sin modificar registros:

```powershell
python .\demo_novagest_2026\seed.py --verify
```

Una segunda ejecución de `--apply` **no duplica registros**: detecta el prefijo de SKU `DEM26-`, el marcador de pedidos y la serie `D26`, y cancela.

## Qué revisar en la aplicación

- Entrar con **Daniel**: catálogo, clientes, pedidos, albaranes, facturas, cobros y **Panorama económico**.
- Elegir meses de enero a noviembre de 2026 en el resumen contable. Habrá importes, cobros, pendientes, productos más vendidos y evolución temporal.
- Entrar con **Laura**: debe poder gestionar la actividad comercial de la misma empresa, pero no abrir las zonas reservadas al superusuario.
- Buscar facturas de la serie **`D26`** y SKU **`DEM26-`**. Los registros están etiquetados como **DEMO**.

**Importante:** el panel usa el mes de emisión para facturación y el mes de pago para caja. Si se cobra en octubre una factura de septiembre, octubre muestra ese cobro sin sumar de nuevo la venta. No es un estado contable fiscal oficial.

## Precauciones

- El cargador escribe directamente en las tablas del sistema **solo para pruebas locales**, en lugar de utilizar las rutas API; esto permite crear un histórico de once meses con fechas coherentes.
- No registra información ante la AEAT ni genera cobros, correos, ventas o clientes reales. **No envíes facturas de demostración a terceros como documentos fiscales.**
- Las fechas históricas son un juego de datos ficticio; las cuentas de Daniel y Laura no existían necesariamente cuando supuestamente ocurrieron las operaciones.
- Todos los inserts se ejecutan dentro de **una sola transacción PostgreSQL**. Si falla cualquiera, se revierte el lote completo.
- No incorpora un borrado automático: si deseas limpiar el histórico después, debe planificarse una eliminación **por el marcador**, preservando relaciones y otros datos. No hagas `DELETE` masivos por fecha.
- No es necesario correr Alembic ni modificar el frontend.

## Validación realizada antes de entrega

Se comprobó que el script compila, el generador produce las cantidades anteriores, los montos cuadran, las fechas no exceden el 23/11/2026 y los registros se pueden insertar en un **esquema SQLAlchemy de prueba con SQLite**; también se validó que el preflight detecta un segundo intento. **No se ha ejecutado contra tu PostgreSQL local**, que es lo que verificará el `--dry-run` y la aplicación final.
