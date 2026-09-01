from uuid import uuid4

def build_business_payload():
    return {
        "legal_name": "Test Business API SL",
        "tax_id": f"TEST-{uuid4().hex[:12]}",
        "trade_name": "Test API",
        "address": "Calle Prueba 123",
        "postal_code": "41001",
        "city": "Sevilla",
        "province": "Sevilla",
        "country_code": "ES",
    }

def test_create_business(client):
    payload = build_business_payload()

    response = client.post(
        "/businesses",
        json=payload,
    )

    assert response.status_code == 201

    body = response.json()

    assert body["id"] is not None
    assert body["legal_name"] == payload["legal_name"]
    assert body["tax_id"] == payload["tax_id"]
    assert body["trade_name"] == payload["trade_name"]
    assert body["address"] == payload["address"]
    assert body["postal_code"] == payload["postal_code"]
    assert body["city"] == payload["city"]
    assert body["province"] == payload["province"]
    assert body["country_code"] == "ES"
    assert body["created_at"] is not None
    assert body["updated_at"] is not None

def test_get_business(client):
    payload = build_business_payload()

    create_response = client.post(
        "/businesses",
        json=payload,
    )

    assert create_response.status_code == 201

    created_business = create_response.json()
    business_id = created_business["id"]

    response = client.get(
        f"/businesses/{business_id}"
    )

    assert response.status_code == 200

    body = response.json()

    assert body["id"] == business_id
    assert body["legal_name"] == payload["legal_name"]
    assert body["tax_id"] == payload["tax_id"]
    assert body["trade_name"] == payload["trade_name"]
    assert body["address"] == payload["address"]
    assert body["postal_code"] == payload["postal_code"]
    assert body["city"] == payload["city"]
    assert body["province"] == payload["province"]
    assert body["country_code"] == payload["country_code"]

def test_duplicate_tax_id_returns_409(client):
    payload = build_business_payload()

    first_response = client.post(
        "/businesses",
        json=payload,
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/businesses",
        json=payload,
    )

    assert second_response.status_code == 409

    body = second_response.json()

    assert "detail" in body
    assert payload["tax_id"] in body["detail"]

def test_get_nonexistent_business_returns_404(client):
    response = client.get(
        "/businesses/999999999"
    )

    assert response.status_code == 404

    body = response.json()

    assert body["detail"] == "Business not found."