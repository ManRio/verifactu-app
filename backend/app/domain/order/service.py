from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy.orm import Session

from app.domain.business.repository import BusinessRepository
from app.domain.customer.repository import CustomerRepository
from app.domain.order.model import Order, OrderLine
from app.domain.order.repository import OrderRepository
from app.domain.order.schemas import OrderCreate, OrderLineInput, OrderUpdate
from app.domain.product.repository import ProductRepository

MONEY_QUANTIZER = Decimal("0.01")
PERCENT_DIVISOR = Decimal(100)


class OrderBusinessNotFoundError(Exception):
    pass


class OrderBusinessInactiveError(Exception):
    pass


class OrderCustomerNotFoundError(Exception):
    pass


class OrderCustomerInactiveError(Exception):
    pass


class OrderCustomerTenantError(Exception):
    pass


class OrderProductNotFoundError(Exception):
    pass


class OrderProductInactiveError(Exception):
    pass


class OrderProductTenantError(Exception):
    pass


class OrderDuplicatePositionError(Exception):
    pass


class OrderNotEditableError(Exception):
    pass


class OrderCannotConfirmError(Exception):
    pass


class OrderCannotCancelError(Exception):
    pass


class OrderService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = OrderRepository(db)
        self.business_repository = BusinessRepository(db)
        self.customer_repository = CustomerRepository(db)
        self.product_repository = ProductRepository(db)

    def create_order(
        self,
        data: OrderCreate,
        *,
        commit: bool = True,
    ) -> Order:
        business = self.business_repository.get_by_id(
            data.business_id,
        )

        if business is None:
            raise OrderBusinessNotFoundError

        if not business.is_active:
            raise OrderBusinessInactiveError

        customer = self._get_valid_customer(
            business_id=data.business_id,
            customer_id=data.customer_id,
        )

        self._validate_positions(data.lines)

        lines = self._build_order_lines(
            business_id=data.business_id,
            line_inputs=data.lines,
        )

        subtotal, tax_total, total_amount = (
            self._calculate_order_totals(lines)
        )

        order = Order(
            business_id=data.business_id,
            customer_id=customer.id,
            status="DRAFT",
            notes=data.notes,
            subtotal=subtotal,
            tax_total=tax_total,
            total_amount=total_amount,
        )

        order = self.repository.create(
            order,
            lines,
        )

        if commit:
            self.db.commit()
            self.db.refresh(order)

        return order

    def get_by_id(
        self,
        order_id: int,
    ) -> Order | None:
        return self.repository.get_by_id(
            order_id,
        )

    def list_by_business_id(
        self,
        business_id: int,
    ) -> list[Order]:
        return self.repository.list_by_business_id(
            business_id,
        )

    def update_order(
        self,
        order_id: int,
        data: OrderUpdate,
    ) -> Order | None:
        order = self.repository.get_by_id(
            order_id,
        )

        if order is None:
            return None

        if order.status != "DRAFT":
            raise OrderNotEditableError

        update_data = data.model_dump(
            exclude_unset=True,
            exclude={"lines"},
        )

        if "customer_id" in update_data:
            customer_id = update_data["customer_id"]

            if customer_id is None:
                raise OrderCustomerNotFoundError

            customer = self._get_valid_customer(
                business_id=order.business_id,
                customer_id=customer_id,
            )

            order.customer_id = customer.id

        if "notes" in update_data:
            order.notes = update_data["notes"]

        if "lines" in data.model_fields_set:
            line_inputs = data.lines

            if line_inputs is None:
                raise OrderNotEditableError

            self._validate_positions(line_inputs)

            lines = self._build_order_lines(
                business_id=order.business_id,
                line_inputs=line_inputs,
            )

            subtotal, tax_total, total_amount = (
                self._calculate_order_totals(lines)
            )

            order.subtotal = subtotal
            order.tax_total = tax_total
            order.total_amount = total_amount

            self.repository.replace_lines(
                order,
                lines,
            )

        self.db.commit()
        self.db.refresh(order)

        return self.repository.get_by_id(
            order.id,
        )

    def confirm_order(
        self,
        order_id: int,
    ) -> Order | None:
        order = self.repository.get_by_id(
            order_id,
        )

        if order is None:
            return None

        if order.status != "DRAFT":
            raise OrderCannotConfirmError

        if not order.lines:
            raise OrderCannotConfirmError

        order.status = "CONFIRMED"
        order.confirmed_at = datetime.now(UTC)

        self.db.commit()
        self.db.refresh(order)

        return self.repository.get_by_id(
            order.id,
        )

    def cancel_order(
        self,
        order_id: int,
    ) -> Order | None:
        order = self.repository.get_by_id(
            order_id,
        )

        if order is None:
            return None

        if order.status not in {
            "DRAFT",
            "CONFIRMED",
        }:
            raise OrderCannotCancelError

        order.status = "CANCELLED"

        self.db.commit()
        self.db.refresh(order)

        return self.repository.get_by_id(
            order.id,
        )

    def _get_valid_customer(
        self,
        *,
        business_id: int,
        customer_id: int,
    ):
        customer = self.customer_repository.get_by_id(
            customer_id,
        )

        if customer is None:
            raise OrderCustomerNotFoundError

        if customer.business_id != business_id:
            raise OrderCustomerTenantError

        if not customer.is_active:
            raise OrderCustomerInactiveError

        return customer

    def _build_order_lines(
        self,
        *,
        business_id: int,
        line_inputs: list[OrderLineInput],
    ) -> list[OrderLine]:
        return [
            self._build_order_line(
                business_id=business_id,
                line_input=line_input,
            )
            for line_input in line_inputs
        ]

    def _build_order_line(
        self,
        *,
        business_id: int,
        line_input: OrderLineInput,
    ) -> OrderLine:
        product = self.product_repository.get_by_id(
            line_input.product_id,
        )

        if product is None:
            raise OrderProductNotFoundError

        if product.business_id != business_id:
            raise OrderProductTenantError

        if not product.is_active:
            raise OrderProductInactiveError

        base_amount = self._money(
            line_input.quantity * product.unit_price
        )

        tax_amount = self._money(
            base_amount
            * product.tax_rate
            / PERCENT_DIVISOR
        )

        total_amount = self._money(
            base_amount + tax_amount
        )

        return OrderLine(
            product_id=product.id,
            description=product.name,
            quantity=line_input.quantity,
            unit_price=product.unit_price,
            tax_rate=product.tax_rate,
            base_amount=base_amount,
            tax_amount=tax_amount,
            total_amount=total_amount,
            position=line_input.position,
        )

    def _calculate_order_totals(
        self,
        lines: list[OrderLine],
    ) -> tuple[Decimal, Decimal, Decimal]:
        subtotal = sum(
            (line.base_amount for line in lines),
            start=Decimal(0),
        )

        tax_total = sum(
            (line.tax_amount for line in lines),
            start=Decimal(0),
        )

        total_amount = sum(
            (line.total_amount for line in lines),
            start=Decimal(0),
        )

        return (
            self._money(subtotal),
            self._money(tax_total),
            self._money(total_amount),
        )

    def _validate_positions(
        self,
        lines: list[OrderLineInput],
    ) -> None:
        positions = [
            line.position
            for line in lines
        ]

        if len(positions) != len(set(positions)):
            raise OrderDuplicatePositionError

    @staticmethod
    def _money(value: Decimal) -> Decimal:
        return value.quantize(
            MONEY_QUANTIZER,
            rounding=ROUND_HALF_UP,
        )