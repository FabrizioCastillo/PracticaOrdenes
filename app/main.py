from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Session, func, select

from app.database import create_db_and_tables
from app.models import Order, OrderItem, Product
from app.schemas import (
    OrderCreate,
    OrderDetailRead,
    OrderItemRead,
    OrderItemReadWithProduct,
    OrderRead,
    PaginatedOrders,
    ProductCreate,
    ProductRead,
)
from app.uow import SqlModelUnitOfWork


@asynccontextmanager
async def lifespan(_: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(title="Sistema de Ordenes API", lifespan=lifespan)


def get_uow() -> SqlModelUnitOfWork:
    return SqlModelUnitOfWork()

@app.post("/products", response_model=ProductRead, status_code=201)
def create_product(payload: ProductCreate, uow: Annotated[SqlModelUnitOfWork, Depends(get_uow)]) -> Product:
    with uow:
        assert uow.session is not None
        product = Product(name=payload.name, price=payload.price)
        uow.session.add(product)
        uow.commit()
        uow.session.refresh(product)
        return product


@app.post("/orders", response_model=OrderRead, status_code=201)
def create_order(payload: OrderCreate, uow: Annotated[SqlModelUnitOfWork, Depends(get_uow)]) -> OrderRead:
    with uow:
        assert uow.session is not None
        session: Session = uow.session

        order = Order(user_email=str(payload.user_email))
        session.add(order)
        session.flush()

        order_items_out: list[OrderItemRead] = []
        total_amount = 0.0

        for item in payload.items:
            product = session.get(Product, item.product_id)
            if product is None:
                raise HTTPException(status_code=404, detail="Producto no encontrado")

            unit_price = float(product.price)
            line_total = unit_price * item.quantity
            total_amount += line_total

            order_item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=item.quantity,
                unit_price=unit_price,
            )
            session.add(order_item)
            order_items_out.append(
                OrderItemRead(product_id=product.id, quantity=item.quantity, unit_price=unit_price)
            )

        order.total_amount = total_amount
        uow.commit()
        session.refresh(order)

        return OrderRead(
            id=order.id,
            user_email=order.user_email,
            total_amount=order.total_amount,
            created_at=order.created_at,
            items=order_items_out,
        )


@app.get("/orders/{order_id}", response_model=OrderDetailRead)
def get_order(order_id: int, uow: Annotated[SqlModelUnitOfWork, Depends(get_uow)]) -> OrderDetailRead:
    with uow:
        assert uow.session is not None
        session: Session = uow.session

        order = session.get(Order, order_id)
        if order is None:
            raise HTTPException(status_code=404, detail="Orden no encontrada")

        items_stmt = select(OrderItem, Product).join(Product, Product.id == OrderItem.product_id).where(
            OrderItem.order_id == order_id
        )
        rows = session.exec(items_stmt).all()

        items = [
            OrderItemReadWithProduct(product=ProductRead.model_validate(product), quantity=item.quantity, unit_price=item.unit_price)
            for item, product in rows
        ]

        return OrderDetailRead(
            id=order.id,
            user_email=order.user_email,
            total_amount=order.total_amount,
            created_at=order.created_at,
            items=items,
        )


@app.get("/orders", response_model=PaginatedOrders)
def list_orders(
    uow: Annotated[SqlModelUnitOfWork, Depends(get_uow)],
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
) -> PaginatedOrders:
    with uow:
        assert uow.session is not None
        session: Session = uow.session

        total = session.exec(select(func.count()).select_from(Order)).one()
        orders = session.exec(select(Order).order_by(Order.id).offset(offset).limit(limit)).all()

        data: list[OrderRead] = []
        for order in orders:
            order_items = session.exec(select(OrderItem).where(OrderItem.order_id == order.id)).all()
            mapped_items = [
                OrderItemRead(product_id=item.product_id, quantity=item.quantity, unit_price=item.unit_price)
                for item in order_items
            ]
            data.append(
                OrderRead(
                    id=order.id,
                    user_email=order.user_email,
                    total_amount=order.total_amount,
                    created_at=order.created_at,
                    items=mapped_items,
                )
            )

        return PaginatedOrders(total=total, data=data)
