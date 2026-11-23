r"""Puebla exclusivamente NovaGest con actividad FICTICIA en 2026.

Uso desde la raíz de verifactu-app:
  python .\demo_novagest_2026\seed.py --dry-run
  python .\demo_novagest_2026\seed.py --apply --confirm NOVAGEST_DEMO_2026

No envía emails, no crea/modifica usuarios ni modifica datos previos.
"""

from __future__ import annotations

import argparse
import calendar
import random
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

from sqlalchemy import MetaData, Table, func, insert, select, update
from sqlalchemy.engine import Connection

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

OWNER_EMAIL = "daniel.novagest@example.com"
WORKER_EMAIL = "laura.novagest@example.com"
MARKER = "DEMO-NOVAGEST-2026-V1"
CONFIRM = "NOVAGEST_DEMO_2026"
CUTOFF = date(2026, 11, 23)
SERIES = "D26"
VAT = Decimal("21.00")
ZERO = Decimal("0.00")
MONTH_COUNTS = (20, 23, 26, 29, 30, 27, 24, 26, 32, 34, 21)

# Catálogo de 100 referencias plausibles, inventadas y genéricas, sin prometer compatibilidad real.
CATALOG_GROUPS: list[tuple[str, list[tuple[str, str]]]] = [
    ("Filtros", [
        ("Filtro aceite rosca M20x1,5", "9.90"), ("Filtro aceite cartucho 65 mm", "11.50"),
        ("Filtro aceite cartucho 74 mm", "12.80"), ("Filtro aire panel compacto", "14.20"),
        ("Filtro aire panel mediano", "18.40"), ("Filtro aire cilíndrico", "21.90"),
        ("Filtro habitáculo antipolen", "13.90"), ("Filtro habitáculo carbón activo", "20.50"),
        ("Filtro combustible diésel", "29.90"), ("Filtro combustible gasolina", "17.50"),
    ]),
    ("Frenos", [
        ("Juego pastillas freno delanteras", "48.90"), ("Juego pastillas freno traseras", "39.90"),
        ("Disco freno delantero ventilado 280 mm", "65.00"), ("Disco freno delantero ventilado 300 mm", "79.00"),
        ("Disco freno trasero 260 mm", "47.50"), ("Kit zapatas freno trasero", "59.90"),
        ("Latiguillo freno delantero", "18.90"), ("Sensor desgaste pastillas", "11.50"),
        ("Bomba freno principal", "119.00"), ("Líquido frenos DOT 4 1 L", "12.90"),
    ]),
    ("Suspensión y dirección", [
        ("Amortiguador delantero", "89.00"), ("Amortiguador trasero", "69.00"),
        ("Copela amortiguador delantera", "29.90"), ("Muelle suspensión delantero", "72.00"),
        ("Bieleta barra estabilizadora", "19.90"), ("Silentblock brazo suspensión", "15.90"),
        ("Brazo suspensión inferior", "82.50"), ("Rótula suspensión", "24.50"),
        ("Terminal dirección", "22.90"), ("Rótula axial dirección", "28.90"),
    ]),
    ("Encendido y electricidad", [
        ("Bujía iridio", "17.90"), ("Bujía estándar", "8.50"),
        ("Bujía precalentamiento diésel", "19.90"), ("Bobina encendido individual", "48.90"),
        ("Batería 60 Ah 540 A", "104.00"), ("Batería 74 Ah 680 A", "139.00"),
        ("Alternador 120 A", "215.00"), ("Motor arranque 1,7 kW", "174.00"),
        ("Relé 12 V 40 A", "9.50"), ("Fusible mini surtido 10 uds", "5.90"),
    ]),
    ("Motor y lubricación", [
        ("Aceite motor 5W30 C3 5 L", "42.90"), ("Aceite motor 0W30 5 L", "54.90"),
        ("Aceite motor 5W40 5 L", "39.90"), ("Correa auxiliar 6PK", "25.90"),
        ("Tensor correa auxiliar", "65.00"), ("Kit distribución con bomba agua", "189.00"),
        ("Junta tapa balancines", "28.50"), ("Soporte motor derecho", "92.00"),
        ("Bomba aceite motor", "165.00"), ("Retén cigüeñal delantero", "17.90"),
    ]),
    ("Refrigeración", [
        ("Termostato refrigerante", "34.90"), ("Bomba agua mecánica", "76.90"),
        ("Radiador refrigeración", "159.00"), ("Ventilador radiador", "135.00"),
        ("Depósito expansión", "39.90"), ("Tapón depósito refrigerante", "10.90"),
        ("Manguito radiador superior", "29.90"), ("Manguito radiador inferior", "26.90"),
        ("Anticongelante G12 5 L", "23.50"), ("Sensor temperatura refrigerante", "21.90"),
    ]),
    ("Transmisión y embrague", [
        ("Kit embrague 3 piezas", "239.00"), ("Volante bimasa", "429.00"),
        ("Cilindro receptor embrague", "69.90"), ("Bombín maestro embrague", "56.90"),
        ("Palier delantero izquierdo", "185.00"), ("Palier delantero derecho", "192.00"),
        ("Fuelle homocinética exterior", "17.90"), ("Junta homocinética", "82.90"),
        ("Aceite transmisión 75W80 1 L", "19.90"), ("Soporte caja cambios", "85.00"),
    ]),
    ("Sensores y gestión electrónica", [
        ("Sensor posición cigüeñal", "38.90"), ("Sensor posición árbol levas", "42.90"),
        ("Sensor presión MAP", "49.90"), ("Caudalímetro aire", "116.00"),
        ("Sonda lambda anterior", "89.00"), ("Sonda lambda posterior", "94.00"),
        ("Sensor ABS rueda delantera", "35.50"), ("Sensor presión aceite", "16.90"),
        ("Válvula EGR", "215.00"), ("Sensor NOx", "285.00"),
    ]),
    ("Iluminación y carrocería", [
        ("Lámpara H7 12 V", "9.90"), ("Lámpara H4 12 V", "8.90"),
        ("Bombilla P21W pack 2", "4.50"), ("Piloto trasero derecho", "89.90"),
        ("Espejo retrovisor derecho", "119.00"), ("Espejo retrovisor izquierdo", "119.00"),
        ("Escobillas limpiaparabrisas 600/450", "24.90"), ("Bomba lavaparabrisas", "18.90"),
        ("Amortiguador portón trasero", "25.90"), ("Maneta puerta exterior", "29.90"),
    ]),
    ("Mantenimiento y taller", [
        ("Limpiador frenos aerosol 500 ml", "6.90"), ("Limpiador contactos 400 ml", "8.90"),
        ("Grasa litio tubo 150 g", "8.50"), ("Silicona juntas alta temperatura", "12.90"),
        ("Abrazaderas inox surtido", "9.90"), ("Bridas nylon pack 100", "5.90"),
        ("Tornillo rueda M12x1,5", "4.50"), ("Tuerca autoblocante M10 pack 10", "6.90"),
        ("Arandela cobre surtido", "7.90"), ("Aditivo limpiador inyectores 300 ml", "16.90"),
    ]),
]

CUSTOMER_NAMES = [
    "Talleres Mirador", "Autoservicio Bahía", "Motor San Jerónimo", "Mecánica Alameda",
    "Auto Técnica Sur", "Talleres La Estación", "Hermanos Carrera Motor", "Recambios Torneo",
    "Servicios Mecánicos Vega", "Garaje Las Palmeras", "Auto Repair Triana", "Talleres Dos Hermanas",
    "Mecánica Los Olivos", "Autos Guadalquivir", "Talleres Oriente", "Motor Aljarafe",
    "Centro Motor Nervión", "Talleres El Puerto", "Servicio Auto Campana", "Mecánica La Giralda",
    "Taller Los Pinos", "Auto Taller Concordia", "Talleres Aeropuerto", "Automoción Encina",
    "Taller Pino Montano", "Mecánica Virgen del Rocío", "Servicio Motor Sur", "Auto Écija",
    "Taller San Juan", "Talleres Ronda", "Mantenimiento Axati", "Garaje Alameda Norte",
    "Taller Mairena", "Motor Carmona", "Auto Servicio Aracena", "Mecánica Vega Alta",
    "Talleres La Puebla", "Servicio Rápido Itálica", "Autotec Ríos", "Recambios El Paseo",
    "Talleres Campo Verde", "Auto Centro Macarena", "Garaje La Feria", "Talleres Camino Real",
    "Automoción Aljarafe", "Servicio Vehículos Triana", "Motor Montequinto", "Taller Ruta Sur",
]


def eur(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def money_es(value: Decimal) -> str:
    return f"{value:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")


def timestamp(day: date, hour: int = 12) -> datetime:
    return datetime.combine(day, time(hour, 15), tzinfo=UTC)


@dataclass(frozen=True)
class ProductSpec:
    sku: str
    name: str
    category: str
    price: Decimal


@dataclass(frozen=True)
class LineSpec:
    product_index: int
    quantity: int
    unit_price: Decimal
    base: Decimal
    tax: Decimal
    total: Decimal


@dataclass(frozen=True)
class PaymentSpec:
    amount: Decimal
    paid_on: date
    method: str
    status: str = "RECORDED"
    voided_on: date | None = None


@dataclass(frozen=True)
class SaleSpec:
    index: int
    month: int
    customer_index: int
    order_date: date
    delivery_date: date
    invoice_date: date
    order_status: str
    delivery_status: str | None
    invoice_status: str | None
    lines: tuple[LineSpec, ...]
    payments: tuple[PaymentSpec, ...]

    @property
    def subtotal(self) -> Decimal:
        return sum((x.base for x in self.lines), ZERO)

    @property
    def taxes(self) -> Decimal:
        return sum((x.tax for x in self.lines), ZERO)

    @property
    def total(self) -> Decimal:
        return sum((x.total for x in self.lines), ZERO)


def make_products() -> list[ProductSpec]:
    products = []
    for category, values in CATALOG_GROUPS:
        for name, price in values:
            products.append(ProductSpec(
                sku=f"DEM26-{len(products) + 1:04d}",
                name=name,
                category=category,
                price=Decimal(price),
            ))
    if len(products) != 100 or len({x.sku for x in products}) != 100:
        raise RuntimeError("El catálogo debe contener 100 referencias distintas")
    return products


def make_sales(products: list[ProductSpec]) -> list[SaleSpec]:
    rng = random.Random(20261123)
    sales = []
    weights = [9 if i < 10 else 7 if i < 20 else 5 if i < 40 else 3 if i < 80 else 2 for i in range(100)]
    for month, count in enumerate(MONTH_COUNTS, 1):
        max_day = min(calendar.monthrange(2026, month)[1], CUTOFF.day if month == 11 else 31)
        for _ in range(count):
            # Mantener pedidos/albaranes/facturas con fechas razonables en el mismo mes.
            day = rng.randint(8, max_day)
            invoice_day = date(2026, month, day)
            order_day = invoice_day - timedelta(days=rng.randint(3, 6))
            delivery_day = invoice_day - timedelta(days=rng.randint(1, 2))
            customer_idx = rng.randrange(len(CUSTOMER_NAMES))
            line_count = rng.choices([1, 2, 3, 4, 5], [12, 34, 31, 17, 6], k=1)[0]
            chosen = []
            while len(chosen) < line_count:
                idx = rng.choices(range(100), weights=weights, k=1)[0]
                if idx not in chosen:
                    chosen.append(idx)
            lines = []
            for product_idx in chosen:
                item = products[product_idx]
                qty = rng.choices([1, 2, 3, 4, 5, 6, 8, 10], [17, 29, 20, 12, 8, 6, 5, 3], k=1)[0]
                base = eur(item.price * qty)
                tax = eur(base * VAT / 100)
                lines.append(LineSpec(product_idx, qty, item.price, base, tax, base + tax))
            roll = rng.random()
            if roll < 0.065:
                order_status, delivery_status, invoice_status = "DRAFT", None, None
            elif roll < 0.10:
                order_status, delivery_status, invoice_status = "CANCELLED", None, None
            elif roll < 0.16:
                order_status, delivery_status, invoice_status = "CONFIRMED", "DRAFT", None
            elif roll < 0.185:
                order_status, delivery_status, invoice_status = "CONFIRMED", "CANCELLED", None
            elif roll < 0.255:
                order_status, delivery_status, invoice_status = "CONFIRMED", "CONFIRMED", "DRAFT"
            else:
                order_status, delivery_status, invoice_status = "CONFIRMED", "CONFIRMED", "ISSUED"
            payments: list[PaymentSpec] = []
            if invoice_status == "ISSUED":
                gross = sum((x.total for x in lines), ZERO)
                paid_kind = rng.random()
                if month >= 11:
                    whole_cut, partial_cut = 0.30, 0.67
                elif month >= 9:
                    whole_cut, partial_cut = 0.53, 0.80
                else:
                    whole_cut, partial_cut = 0.77, 0.92
                if paid_kind < whole_cut:
                    pay_total = gross
                elif paid_kind < partial_cut:
                    pay_total = eur(gross * Decimal(str(rng.uniform(0.25, 0.79))))
                else:
                    pay_total = ZERO
                if pay_total > ZERO:
                    first_pay_day = min(invoice_day + timedelta(days=rng.randint(0, 11)), CUTOFF)
                    method = rng.choices(["TRANSFER", "CARD", "CASH", "OTHER"], [55, 25, 16, 4], k=1)[0]
                    if pay_total == gross and rng.random() < 0.30 and pay_total >= 30:
                        amount_a = eur(pay_total * Decimal("0.40"))
                        amount_b = pay_total - amount_a
                        other_day = min(first_pay_day + timedelta(days=rng.randint(1, 21)), CUTOFF)
                        payments.extend([PaymentSpec(amount_a, first_pay_day, method), PaymentSpec(amount_b, other_day, method)])
                    else:
                        payments.append(PaymentSpec(pay_total, first_pay_day, method))
                    # Un apunte anulado y rehecho para demostrar auditoría; nunca suma en caja.
                    if rng.random() < 0.035 and first_pay_day < CUTOFF:
                        void_day = min(first_pay_day + timedelta(days=1), CUTOFF)
                        payments.append(PaymentSpec(pay_total, first_pay_day, method, "VOIDED", void_day))
            sales.append(SaleSpec(
                index=len(sales) + 1, month=month, customer_index=customer_idx,
                order_date=order_day, delivery_date=delivery_day, invoice_date=invoice_day,
                order_status=order_status, delivery_status=delivery_status,
                invoice_status=invoice_status, lines=tuple(lines), payments=tuple(payments),
            ))
    return sales


def validate_plan(products: list[ProductSpec], sales: list[SaleSpec]) -> None:
    """Validación local de relaciones, fechas e importes ANTES de conectar a la BD."""
    if len(products) != 100 or not sales or len({s.index for s in sales}) != len(sales):
        raise RuntimeError("Plan sintético duplicado o sin registros")
    months = {sale.month for sale in sales}
    if months != set(range(1, 12)):
        raise RuntimeError("El período 2026 no cubre todos los meses hasta noviembre")
    for sale in sales:
        if not (date(2026, 1, 1) <= sale.order_date <= sale.delivery_date <= sale.invoice_date <= CUTOFF):
            raise RuntimeError(f"Fechas inconsistentes en pedido #{sale.index}")
        if sale.order_status != "CONFIRMED" and sale.delivery_status is not None:
            raise RuntimeError(f"Pedido no confirmado con albarán #{sale.index}")
        if sale.delivery_status != "CONFIRMED" and sale.invoice_status is not None:
            raise RuntimeError(f"Factura sin albarán confirmado #{sale.index}")
        if sale.invoice_status != "ISSUED" and sale.payments:
            raise RuntimeError(f"Cobros de factura no emitida #{sale.index}")
        if not sale.lines or sale.total != sale.subtotal + sale.taxes:
            raise RuntimeError(f"Factura sin detalle o importes incorrectos #{sale.index}")
        if len({line.product_index for line in sale.lines}) != len(sale.lines):
            raise RuntimeError(f"Producto duplicado en líneas #{sale.index}")
        for line in sale.lines:
            if line.quantity <= 0 or line.total != line.base + line.tax:
                raise RuntimeError(f"Importe o cantidad incorrectos #{sale.index}")
        payments = [p for p in sale.payments if p.status == "RECORDED"]
        if sum((p.amount for p in payments), ZERO) > sale.total:
            raise RuntimeError(f"Cobros superiores a la factura #{sale.index}")
        for pay in sale.payments:
            if not (sale.invoice_date <= pay.paid_on <= CUTOFF):
                raise RuntimeError(f"Cobro fuera del período #{sale.index}")


def show_plan(products: list[ProductSpec], sales: list[SaleSpec]) -> None:
    print("\nDATOS GENERADOS (solo demostración; operaciones ficticias)")
    print(f"Período: 2026-01-01 al {CUTOFF.isoformat()} | {len(products)} productos | {len(CUSTOMER_NAMES)} clientes")
    print(f"{len(sales)} pedidos; {sum(s.delivery_status is not None for s in sales)} albaranes; "
          f"{sum(s.invoice_status is not None for s in sales)} facturas "
          f"({sum(s.invoice_status == 'ISSUED' for s in sales)} emitidas)")
    print("Mes       Pedidos  Facturas emitidas   Facturado        Cobrado anotado")
    all_billed, all_paid = ZERO, ZERO
    for month in range(1, 12):
        selected = [s for s in sales if s.month == month]
        billed = sum((s.total for s in selected if s.invoice_status == "ISSUED"), ZERO)
        paid = sum((p.amount for s in sales for p in s.payments
                    if p.status == "RECORDED" and p.paid_on.month == month), ZERO)
        all_billed += billed
        all_paid += paid
        print(f"2026-{month:02d}   {len(selected):>6}   {sum(s.invoice_status == 'ISSUED' for s in selected):>10} "
              f"       {money_es(billed):>12} €  {money_es(paid):>12} €")
    print(f"Total facturado: {money_es(all_billed)} € | Cobrado: {money_es(all_paid)} € | "
          f"Pendiente: {money_es(all_billed - all_paid)} €")
    print("NOTA: no son facturas fiscales reales. La serie D26 se reserva para esta demo.")


def load_tables(connection: Connection) -> dict[str, Table]:
    names = (
        "users", "businesses", "products", "customers", "orders", "order_lines",
        "delivery_notes", "delivery_note_lines", "invoice_series", "invoices",
        "invoice_delivery_notes", "invoice_lines", "payments",
    )
    meta = MetaData()
    result = {name: Table(name, meta, autoload_with=connection) for name in names}
    expected = {
        "users": {"email", "business_id", "role", "email_verified", "is_active"},
        "products": {"sku", "unit_price", "tax_rate", "business_id"},
        "customers": {"business_id", "legal_name", "tax_id"},
        "invoices": {"business_id", "issue_date", "issued_at", "status", "full_number", "total_amount"},
        "invoice_lines": {"delivery_note_line_id", "order_line_id", "invoice_id"},
        "payments": {"invoice_id", "amount", "status", "payment_date", "created_by_user_id"},
    }
    for name, fields in expected.items():
        if missing := fields - set(result[name].c.keys()):
            raise RuntimeError(f"Esquema incompatible: {name} sin columnas {sorted(missing)}")
    return result


def verify_target(connection: Connection, tables: dict[str, Table], *, allow_seeded: bool = False) -> tuple[int, int, int, dict]:
    users = tables["users"]
    first = connection.execute(select(users).where(func.lower(users.c.email) == OWNER_EMAIL)).mappings().one_or_none()
    second = connection.execute(select(users).where(func.lower(users.c.email) == WORKER_EMAIL)).mappings().one_or_none()
    if first is None or second is None:
        raise RuntimeError("No se encuentran AMBOS usuarios. No se ha modificado nada.")
    if first["business_id"] != second["business_id"]:
        raise RuntimeError("Daniel y Laura pertenecen a empresas distintas. Carga cancelada.")
    if (first["role"], second["role"]) != ("SUPERUSER", "WORKER"):
        raise RuntimeError("Los roles esperados son SUPERUSER para Daniel y WORKER para Laura.")
    for user in (first, second):
        if not user["is_active"] or not user["email_verified"]:
            raise RuntimeError("Ambas cuentas deben estar activas y verificadas.")
    businesses = tables["businesses"]
    business = connection.execute(select(businesses).where(businesses.c.id == first["business_id"])).mappings().one()
    business_name = f"{business['legal_name']} {business.get('trade_name') or ''}".lower()
    if "novagest" not in business_name:
        raise RuntimeError("Los usuarios no están asociados a la empresa NovaGest. Carga cancelada.")
    if not business["is_active"]:
        raise RuntimeError("La empresa está desactivada.")
    products = tables["products"]
    existing = connection.scalar(select(func.count()).select_from(products).where(
        products.c.business_id == business["id"], products.c.sku.like("DEM26-%"),
    ))
    orders = tables["orders"]
    existing_orders = connection.scalar(select(func.count()).select_from(orders).where(
        orders.c.business_id == business["id"], orders.c.notes.like(f"%{MARKER}%"),
    ))
    series = tables["invoice_series"]
    existing_series = connection.scalar(select(func.count()).select_from(series).where(
        series.c.business_id == business["id"], series.c.code == SERIES,
    ))
    if not allow_seeded and (existing or existing_orders or existing_series):
        raise RuntimeError("La carga parece aplicada previamente o la serie D26 está ocupada. "
                           "No se insertará nada para evitar duplicados.")
    return business["id"], first["id"], second["id"], dict(business)


def add(connection: Connection, table: Table, values: dict) -> int:
    return connection.execute(insert(table).values(**values).returning(table.c.id)).scalar_one()


def insert_seed(connection: Connection, t: dict[str, Table], data: tuple[int, int, int, dict],
                products: list[ProductSpec], sales: list[SaleSpec]) -> Counter:
    business_id, owner_id, worker_id, business = data
    counts: Counter = Counter()
    product_ids = []
    for product in products:
        product_ids.append(add(connection, t["products"], {
            "business_id": business_id, "name": product.name, "sku": product.sku,
            "description": f"{product.category}. REFERENCIA FICTICIA / {MARKER}. Compatibilidad no verificada.",
            "unit_price": product.price, "tax_rate": VAT, "is_active": True,
            "created_at": timestamp(date(2026, 1, 2)), "updated_at": timestamp(date(2026, 1, 2)),
        }))
        counts["products"] += 1
    customer_ids = []
    cities = ("Sevilla", "Dos Hermanas", "Mairena del Aljarafe", "Alcalá de Guadaíra", "Camas", "Carmona")
    for number, name in enumerate(CUSTOMER_NAMES, 1):
        city = cities[(number - 1) % len(cities)]
        customer_ids.append(add(connection, t["customers"], {
            "business_id": business_id, "legal_name": f"{name} (DEMO)", "trade_name": name,
            "tax_id": f"DEMO26CLI{number:04d}", "address": f"Calle de Prueba {number}, nave {number % 9 + 1}",
            "postal_code": f"{41000 + (number % 90):05d}", "city": city, "province": "Sevilla",
            "country_code": "ES", "email": f"taller{number:02d}@example.invalid", "is_active": True,
            "created_at": timestamp(date(2026, 1, 2)), "updated_at": timestamp(date(2026, 1, 2)),
        }))
        counts["customers"] += 1
    series_id = add(connection, t["invoice_series"], {
        "business_id": business_id, "code": SERIES, "next_number": 1,
        "created_at": timestamp(date(2026, 1, 2)), "updated_at": timestamp(date(2026, 1, 2)),
    })
    counts["series"] += 1
    next_number = 1
    for sale in sales:
        customer_id = customer_ids[sale.customer_index]
        customer = connection.execute(select(t["customers"]).where(t["customers"].c.id == customer_id)).mappings().one()
        note = f"{MARKER} | operación sintética #{sale.index:04d}. No emitir ni enviar como factura real."
        order_id = add(connection, t["orders"], {
            "business_id": business_id, "customer_id": customer_id, "status": sale.order_status,
            "notes": note, "subtotal": sale.subtotal, "tax_total": sale.taxes,
            "total_amount": sale.total, "created_at": timestamp(sale.order_date, 10),
            "updated_at": timestamp(sale.order_date, 11),
            "confirmed_at": timestamp(sale.order_date, 12) if sale.order_status == "CONFIRMED" else None,
        })
        counts["orders"] += 1
        order_line_ids = []
        for pos, line in enumerate(sale.lines, 1):
            p = products[line.product_index]
            order_line_ids.append(add(connection, t["order_lines"], {
                "order_id": order_id, "product_id": product_ids[line.product_index],
                "description": p.name, "quantity": Decimal(line.quantity), "unit_price": line.unit_price,
                "tax_rate": VAT, "base_amount": line.base, "tax_amount": line.tax,
                "total_amount": line.total, "position": pos,
                "created_at": timestamp(sale.order_date, 10),
            }))
            counts["order_lines"] += 1
        if sale.delivery_status is None:
            continue
        delivery_id = add(connection, t["delivery_notes"], {
            "business_id": business_id, "order_id": order_id, "status": sale.delivery_status,
            "delivery_date": sale.delivery_date, "notes": note,
            "created_at": timestamp(sale.delivery_date, 10),
            "updated_at": timestamp(sale.delivery_date, 11),
            "confirmed_at": timestamp(sale.delivery_date, 12) if sale.delivery_status == "CONFIRMED" else None,
        })
        counts["delivery_notes"] += 1
        delivery_line_ids = []
        for pos, (line, order_line_id) in enumerate(zip(sale.lines, order_line_ids, strict=True), 1):
            p = products[line.product_index]
            delivery_line_ids.append(add(connection, t["delivery_note_lines"], {
                "delivery_note_id": delivery_id, "order_line_id": order_line_id,
                "description": p.name, "quantity": Decimal(line.quantity), "unit_price": line.unit_price,
                "tax_rate": VAT, "position": pos, "created_at": timestamp(sale.delivery_date, 10),
            }))
            counts["delivery_note_lines"] += 1
        if sale.invoice_status is None:
            continue
        issued = sale.invoice_status == "ISSUED"
        invoice_id = add(connection, t["invoices"], {
            "business_id": business_id, "customer_id": customer_id,
            "invoice_series_id": series_id if issued else None,
            "status": sale.invoice_status, "invoice_type": "STANDARD",
            "series": SERIES if issued else None,
            "number": next_number if issued else None,
            "full_number": f"{SERIES}-{next_number:06d}" if issued else None,
            "issue_date": sale.invoice_date if issued else None,
            "operation_date": sale.delivery_date,
            "issuer_legal_name": business["legal_name"], "issuer_tax_id": business["tax_id"],
            "issuer_address": business["address"], "issuer_postal_code": business["postal_code"],
            "issuer_city": business["city"], "issuer_province": business["province"],
            "issuer_country_code": business["country_code"],
            "customer_legal_name": customer["legal_name"], "customer_tax_id": customer["tax_id"],
            "customer_address": customer["address"], "customer_postal_code": customer["postal_code"],
            "customer_city": customer["city"], "customer_province": customer["province"],
            "customer_country_code": customer["country_code"],
            "subtotal": sale.subtotal, "tax_total": sale.taxes, "total_amount": sale.total,
            "notes": note, "created_at": timestamp(sale.invoice_date, 10),
            "updated_at": timestamp(sale.invoice_date, 16),
            "issued_at": timestamp(sale.invoice_date, 17) if issued else None,
        })
        counts["invoices"] += 1
        if issued:
            next_number += 1
            counts["issued_invoices"] += 1
        add(connection, t["invoice_delivery_notes"], {
            "invoice_id": invoice_id, "delivery_note_id": delivery_id,
            "created_at": timestamp(sale.invoice_date, 11),
        })
        counts["invoice_delivery_notes"] += 1
        for pos, (line, order_line_id, delivery_line_id) in enumerate(
            zip(sale.lines, order_line_ids, delivery_line_ids, strict=True), 1
        ):
            add(connection, t["invoice_lines"], {
                "invoice_id": invoice_id, "delivery_note_line_id": delivery_line_id,
                "order_line_id": order_line_id, "description": products[line.product_index].name,
                "quantity": Decimal(line.quantity), "unit_price": line.unit_price, "tax_rate": VAT,
                "base_amount": line.base, "tax_amount": line.tax, "total_amount": line.total,
                "position": pos, "created_at": timestamp(sale.invoice_date, 11),
            })
            counts["invoice_lines"] += 1
        for idx, payment in enumerate(sale.payments):
            is_void = payment.status == "VOIDED"
            author = (owner_id, worker_id)[(sale.index + idx) % 2]
            add(connection, t["payments"], {
                "business_id": business_id, "invoice_id": invoice_id,
                "amount": payment.amount, "payment_date": payment.paid_on,
                "method": payment.method,
                "reference": f"DEM26-{sale.index:04d}-{idx+1}",
                "notes": f"{MARKER}. Cobro simulado; no es movimiento bancario real.",
                "status": payment.status, "created_by_user_id": author,
                "voided_by_user_id": owner_id if is_void else None,
                "void_reason": "Anulado para mostrar la auditoría de demostración" if is_void else None,
                "created_at": timestamp(payment.paid_on, 13),
                "voided_at": timestamp(payment.voided_on, 14) if is_void and payment.voided_on else None,
            })
            counts["payments"] += 1
    connection.execute(update(t["invoice_series"]).where(t["invoice_series"].c.id == series_id).values(
        next_number=next_number,
    ))
    return counts


def main() -> int:
    parser = argparse.ArgumentParser(description="Generador SEGURO de datos de demostración NovaGest 2026")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--dry-run", action="store_true", help="Inspección sin escritura (por defecto)")
    group.add_argument("--apply", action="store_true", help="Insertar los datos en UNA transacción")
    group.add_argument("--preview", action="store_true", help="Ver números previstos sin conectar a PostgreSQL")
    group.add_argument("--verify", action="store_true", help="Consultar la carga ya realizada, sin escribir")
    parser.add_argument("--confirm", default="", help=f"Confirmación necesaria en --apply: {CONFIRM}")
    args = parser.parse_args()
    products = make_products()
    sales = make_sales(products)
    validate_plan(products, sales)
    show_plan(products, sales)
    if args.preview:
        print("PREVIEW: no se ha conectado a ninguna base de datos.")
        return 0
    if args.apply and args.confirm != CONFIRM:
        print(f"ERROR: para aplicar exige --confirm {CONFIRM}. No se ha escrito nada.", file=sys.stderr)
        return 2
    try:
        # Importar solo al ejecutar, dentro del entorno de la aplicación.
        from app.core.config import settings
        from app.db.session import engine

        if str(getattr(settings, "app_environment", "development")).lower() != "development":
            raise RuntimeError("Se requiere APP_ENVIRONMENT=development; producción bloqueada.")
        if engine.url.host not in {"localhost", "127.0.0.1", "::1", "postgres", "host.docker.internal"}:
            raise RuntimeError("Solo se permite una base de datos local de desarrollo.")
        # En modo lectura no abrir engine.begin(): no se generan escrituras.
        if not args.apply:
            with engine.connect() as connection:
                tables = load_tables(connection)
                business_id, owner_id, worker_id, business = verify_target(
                    connection, tables, allow_seeded=args.verify,
                )
                print(f"\nEMPRESA COMPROBADA: {business['legal_name']} (business_id={business_id}).")
                print(f"Cuentas: Daniel #{owner_id} SUPERUSER; Laura #{worker_id} WORKER.")
                if args.verify:
                    p, o, i, pay = (tables[k] for k in ("products", "orders", "invoices", "payments"))
                    products_count = connection.scalar(select(func.count()).select_from(p).where(
                        p.c.business_id == business_id, p.c.sku.like("DEM26-%")))
                    orders_count = connection.scalar(select(func.count()).select_from(o).where(
                        o.c.business_id == business_id, o.c.notes.like(f"%{MARKER}%")))
                    issued_count = connection.scalar(select(func.count()).select_from(i).where(
                        i.c.business_id == business_id, i.c.series == SERIES, i.c.status == "ISSUED"))
                    invoiced_total = connection.scalar(select(func.coalesce(func.sum(i.c.total_amount), ZERO)).where(
                        i.c.business_id == business_id, i.c.series == SERIES, i.c.status == "ISSUED"))
                    received_total = connection.scalar(select(func.coalesce(func.sum(pay.c.amount), ZERO))
                        .select_from(pay.join(i, pay.c.invoice_id == i.c.id))
                        .where(i.c.business_id == business_id, i.c.series == SERIES, pay.c.status == "RECORDED"))
                    print(f"VERIFICACIÓN DEMO: {products_count} productos, {orders_count} pedidos, "
                          f"{issued_count} facturas emitidas.")
                    print(f"Facturado: {money_es(invoiced_total)} € | Cobrado: {money_es(received_total)} € | "
                          f"Pendiente: {money_es(invoiced_total - received_total)} €")
                    if not products_count or not orders_count:
                        raise RuntimeError("La carga de demostración aún no está aplicada")
                else:
                    print("DRY-RUN: no se ha insertado ningún registro ni alterado ninguna cuenta.")
        else:
            # Operación atómica. Cualquier excepción revierte TODO.
            with engine.begin() as connection:
                tables = load_tables(connection)
                # Bloqueo empresa para evitar que dos cargas simultáneas superen el preflight.
                company = tables["businesses"]
                # Verificamos la empresa por el owner sin mutar datos previos.
                users = tables["users"]
                owner_business_id = connection.scalar(select(users.c.business_id).where(
                    func.lower(users.c.email) == OWNER_EMAIL,
                ))
                if owner_business_id is None:
                    raise RuntimeError("No se encuentra la cuenta de Daniel")
                connection.execute(select(company.c.id).where(company.c.id == owner_business_id).with_for_update()).one()
                data = verify_target(connection, tables)
                counters = insert_seed(connection, tables, data, products, sales)
                print("\nAPLICACIÓN COMPLETADA EN UNA TRANSACCIÓN:")
                for key, amount in sorted(counters.items()):
                    print(f"  {key:<23} {amount:>5}")
            print("CONFIRMADO: datos DEMO insertados, sin modificar usuarios ni operaciones anteriores.")
        return 0
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"\nERROR: {exc}. No se ha confirmado ninguna nueva escritura.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
