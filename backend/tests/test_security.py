from datetime import timedelta

import pytest

from app.core.security import (
    create_access_token,
    decode_access_token,
)


def test_create_and_decode_access_token():
    token = create_access_token("123")

    payload = decode_access_token(token)

    assert payload["sub"] == "123"
    assert "iat" in payload
    assert "exp" in payload


def test_decode_access_token_rejects_tampered_token():
    token = create_access_token("123")

    header, payload, signature = token.split(".")

    tampered_signature = (
        ("a" if signature[0] != "a" else "b")
        + signature[1:]
    )

    tampered_token = ".".join(
        [
            header,
            payload,
            tampered_signature,
        ]
    )

    with pytest.raises(
        ValueError,
        match="Invalid access token",
    ):
        decode_access_token(tampered_token)


def test_decode_access_token_rejects_expired_token():
    token = create_access_token(
        "123",
        expires_delta=timedelta(seconds=-1),
    )

    with pytest.raises(
        ValueError,
        match="Invalid access token",
    ):
        decode_access_token(token)
