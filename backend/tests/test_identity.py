from app.core.identity import normalize_email


def test_normalize_email_converts_to_lowercase():
    assert normalize_email(
        "User@Example.COM"
    ) == "user@example.com"


def test_normalize_email_removes_surrounding_whitespace():
    assert normalize_email(
        "  user@example.com  "
    ) == "user@example.com"


def test_normalize_email_is_idempotent():
    email = "user@example.com"

    assert normalize_email(
        normalize_email(email)
    ) == email