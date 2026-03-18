"""Integration tests for shop MVP."""

from app.core.enums import PaymentStatus


async def create_user(client) -> int:
    """Helper to register user."""

    response = await client.post(
        "/api/users/telegram",
        json={
            "telegram_id": 111111,
            "username": "tester",
            "first_name": "Test",
            "last_name": "User",
            "phone": "+70000000000",
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


async def create_catalog(client) -> int:
    """Helper to create category and product."""

    category_response = await client.post(
        "/api/admin/categories",
        json={"name": "Books", "slug": "books", "parent_id": None, "is_active": True, "sort_order": 0},
    )
    assert category_response.status_code == 201
    category_id = category_response.json()["id"]

    product_response = await client.post(
        "/api/admin/products",
        json={
            "category_id": category_id,
            "name": "Python 101",
            "slug": "python-101",
            "description": "Book",
            "price": "100.00",
            "old_price": "120.00",
            "currency": "RUB",
            "stock_qty": 10,
            "is_active": True,
            "image_urls": ["https://example.com/img.jpg"],
        },
    )
    assert product_response.status_code == 201
    return product_response.json()["id"]


async def test_create_user(client) -> None:
    response = await client.post(
        "/api/users/telegram",
        json={
            "telegram_id": 1001,
            "username": "shopper",
            "first_name": "Alice",
            "last_name": "Doe",
            "phone": "+79998887766",
        },
    )

    assert response.status_code == 201
    assert response.json()["telegram_id"] == 1001


async def test_add_to_cart(client) -> None:
    user_id = await create_user(client)
    product_id = await create_catalog(client)

    response = await client.post(f"/api/cart/{user_id}/items", json={"product_id": product_id, "qty": 2})

    assert response.status_code == 201
    body = response.json()
    assert len(body["items"]) == 1
    assert body["items"][0]["qty"] == 2


async def test_change_cart_quantity(client) -> None:
    user_id = await create_user(client)
    product_id = await create_catalog(client)
    add_response = await client.post(f"/api/cart/{user_id}/items", json={"product_id": product_id, "qty": 1})
    item_id = add_response.json()["items"][0]["id"]

    response = await client.patch(f"/api/cart/{user_id}/items/{item_id}", json={"qty": 4})

    assert response.status_code == 200
    assert response.json()["items"][0]["qty"] == 4


async def test_create_order(client) -> None:
    user_id = await create_user(client)
    product_id = await create_catalog(client)
    await client.post(f"/api/cart/{user_id}/items", json={"product_id": product_id, "qty": 2})

    response = await client.post(
        f"/api/orders/{user_id}",
        json={
            "recipient_name": "Alice",
            "phone": "+79998887766",
            "delivery_type": "courier",
            "delivery_address": "Lenina 1",
            "comment": "Call me",
            "payment_method": "cash",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "new"
    assert body["total_amount"] == "200.00"
    assert len(body["items"]) == 1


async def test_create_order_empty_cart_error(client) -> None:
    user_id = await create_user(client)

    response = await client.post(
        f"/api/orders/{user_id}",
        json={
            "recipient_name": "Alice",
            "phone": "+79998887766",
            "delivery_type": "courier",
            "delivery_address": "Lenina 1",
            "comment": "Call me",
            "payment_method": "cash",
        },
    )

    assert response.status_code == 400
    assert "empty cart" in response.json()["detail"].lower()


async def test_payment_webhook(client) -> None:
    user_id = await create_user(client)
    product_id = await create_catalog(client)
    await client.post(f"/api/cart/{user_id}/items", json={"product_id": product_id, "qty": 1})
    order_response = await client.post(
        f"/api/orders/{user_id}",
        json={
            "recipient_name": "Alice",
            "phone": "+79998887766",
            "delivery_type": "courier",
            "delivery_address": "Lenina 1",
            "comment": "Call me",
            "payment_method": "online",
        },
    )
    order_id = order_response.json()["id"]

    payment_response = await client.post(f"/api/payments/{order_id}", json={"method": "online"})
    external_payment_id = payment_response.json()["external_payment_id"]

    webhook_response = await client.post(
        "/api/payments/webhook",
        json={"external_payment_id": external_payment_id, "status": PaymentStatus.PAID.value},
    )

    assert webhook_response.status_code == 200
    assert webhook_response.json()["status"] == "paid"

    order_check = await client.get(f"/api/orders/{user_id}/{order_id}")
    assert order_check.json()["status"] == "paid"


async def test_payment_webhook_idempotent(client) -> None:
    user_id = await create_user(client)
    product_id = await create_catalog(client)
    await client.post(f"/api/cart/{user_id}/items", json={"product_id": product_id, "qty": 1})
    order_response = await client.post(
        f"/api/orders/{user_id}",
        json={
            "recipient_name": "Alice",
            "phone": "+79998887766",
            "delivery_type": "courier",
            "delivery_address": "Lenina 1",
            "comment": "Call me",
            "payment_method": "online",
        },
    )
    order_id = order_response.json()["id"]

    payment_response = await client.post(f"/api/payments/{order_id}", json={"method": "online"})
    external_payment_id = payment_response.json()["external_payment_id"]

    first = await client.post(
        "/api/payments/webhook",
        json={"external_payment_id": external_payment_id, "status": PaymentStatus.PAID.value},
    )
    second = await client.post(
        "/api/payments/webhook",
        json={"external_payment_id": external_payment_id, "status": PaymentStatus.PAID.value},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["paid_at"] == second.json()["paid_at"]
