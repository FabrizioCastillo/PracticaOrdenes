# Sistema de Ordenes API

API REST desarrollada con FastAPI, SQLModel y Pydantic para gestionar productos y ordenes de compra.

## Objetivo de la practica

Implementar un sistema donde:
- Un usuario puede crear ordenes.
- Cada orden contiene multiples productos.
- El total de la orden se calcula automaticamente en backend.

Se aplican los conceptos pedidos en la consigna:
- Modelado relacional correcto.
- Separacion entre modelos y schemas.
- Paginacion.
- Logica de negocio en backend.
- Patron Unit of Work.

## Estructura del proyecto

```text
ordenes-api/
├── app/
│   ├── __init__.py
│   ├── database.py
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   └── uow.py
├── tests/
│   └── test_api.py
├── requirements.txt
└── README.md
```

## Instalacion

1. Crear y activar entorno virtual (opcional si ya existe `.venv`):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Instalar dependencias:

```powershell
python -m pip install -r requirements.txt
```

## Ejecutar la API

```powershell
python -m uvicorn app.main:app --reload
```

Servidor disponible en:
- http://127.0.0.1:8000
- Documentacion Swagger: http://127.0.0.1:8000/docs

## Endpoints

### 1) Crear producto

- Metodo: `POST`
- Ruta: `/products`
- Body:

```json
{
  "name": "Teclado",
  "price": 1000
}
```

- Response esperada:

```json
{
  "id": 1,
  "name": "Teclado",
  "price": 1000.0
}
```

### 2) Crear orden

- Metodo: `POST`
- Ruta: `/orders`
- Body:

```json
{
  "user_email": "test@mail.com",
  "items": [
    {
      "product_id": 1,
      "quantity": 2
    }
  ]
}
```

- Response esperada (total calculado automaticamente):

```json
{
  "id": 1,
  "user_email": "test@mail.com",
  "total_amount": 2000.0,
  "created_at": "2026-01-01T00:00:00",
  "items": [
    {
      "product_id": 1,
      "quantity": 2,
      "unit_price": 1000.0
    }
  ]
}
```

### 3) Crear orden con producto inexistente

- Metodo: `POST`
- Ruta: `/orders`
- Body:

```json
{
  "user_email": "test@mail.com",
  "items": [
    {
      "product_id": 999,
      "quantity": 1
    }
  ]
}
```

- Response:

```json
{
  "detail": "Producto no encontrado"
}
```

### 4) Crear orden con cantidad invalida

Si `quantity` es 0 (o menor), FastAPI/Pydantic devuelve error de validacion (422).

### 5) Obtener una orden por id

- Metodo: `GET`
- Ruta: `/orders/{order_id}`

Devuelve la orden con sus items y los datos del producto asociado.

### 6) Listar ordenes con paginacion

- Metodo: `GET`
- Ruta: `/orders?offset=1&limit=2`

Response tipo:

```json
{
  "total": 5,
  "data": [
    {
      "id": 2,
      "user_email": "user2@mail.com",
      "total_amount": 20.0,
      "created_at": "2026-01-01T00:00:00",
      "items": []
    },
    {
      "id": 3,
      "user_email": "user3@mail.com",
      "total_amount": 30.0,
      "created_at": "2026-01-01T00:00:00",
      "items": []
    }
  ]
}
```

## Correr tests

```powershell
python -m pytest -q
```

Estado actual:
- 2 tests pasando.


## Autor
Fabrizio Castillo
