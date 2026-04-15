from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from sqlmodel.pool import StaticPool

from app.main import app, get_uow
from app.uow import SqlModelUnitOfWork


class UowForTests(SqlModelUnitOfWork):
    def __init__(self, engine):
        super().__init__(session_factory=lambda: Session(engine))


def create_test_client() -> TestClient:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    def override_uow() -> SqlModelUnitOfWork:
        return UowForTests(engine)

    app.dependency_overrides[get_uow] = override_uow
    return TestClient(app)


def test_flow_pdf_cases() -> None:
    client = create_test_client()

    product_response = client.post("/products", json={"name": "Teclado", "price": 1000})
    assert product_response.status_code == 201
    assert product_response.json() == {"id": 1, "name": "Teclado", "price": 1000.0}

    order_response = client.post(
        "/orders",
        json={
            "user_email": "test@mail.com",
            "items": [{"product_id": 1, "quantity": 2}],
        },
    )
    assert order_response.status_code == 201
    order_data = order_response.json()
    assert order_data["id"] == 1
    assert order_data["user_email"] == "test@mail.com"
    assert order_data["total_amount"] == 2000.0
    assert order_data["items"] == [{"product_id": 1, "quantity": 2, "unit_price": 1000.0}]

    missing_product_response = client.post(
        "/orders",
        json={
            "user_email": "test@mail.com",
            "items": [{"product_id": 999, "quantity": 1}],
        },
    )
    assert missing_product_response.status_code == 404
    assert missing_product_response.json() == {"detail": "Producto no encontrado"}

    invalid_quantity_response = client.post(
        "/orders",
        json={
            "user_email": "test@mail.com",
            "items": [{"product_id": 1, "quantity": 0}],
        },
    )
    assert invalid_quantity_response.status_code == 422
    assert "greater than 0" in str(invalid_quantity_response.json())

    order_detail_response = client.get("/orders/1")
    assert order_detail_response.status_code == 200
    detail = order_detail_response.json()
    assert detail["id"] == 1
    assert detail["total_amount"] == 2000.0
    assert detail["items"][0]["product"] == {"id": 1, "name": "Teclado", "price": 1000.0}
    assert detail["items"][0]["quantity"] == 2
    assert detail["items"][0]["unit_price"] == 1000.0


def test_pagination() -> None:
    client = create_test_client()
    for index in range(1, 6):
        product_id = client.post(
            "/products", json={"name": f"Prod {index}", "price": 10 * index}
        ).json()["id"]
        client.post(
            "/orders",
            json={
                "user_email": f"user{index}@mail.com",
                "items": [{"product_id": product_id, "quantity": 1}],
            },
        )

    page = client.get("/orders?offset=1&limit=2")
    assert page.status_code == 200
    payload = page.json()
    assert payload["total"] == 5
    assert len(payload["data"]) == 2
    assert payload["data"][0]["id"] == 2
    assert payload["data"][1]["id"] == 3
