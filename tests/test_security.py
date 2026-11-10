from datetime import timedelta

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
)


def test_valid_access_token_is_decoded():
    token = create_access_token({"sub": "1"})

    payload = decode_access_token(token)

    assert payload is not None
    assert payload["sub"] == "1"
    assert payload["type"] == "access"


def test_valid_refresh_token_is_decoded():
    token = create_refresh_token({"sub": "1"})

    payload = decode_refresh_token(token)

    assert payload is not None
    assert payload["sub"] == "1"
    assert payload["type"] == "refresh"
    assert payload["jti"]


def test_refresh_token_cannot_be_used_as_access_token():
    token = create_refresh_token({"sub": "1"})

    assert decode_access_token(token) is None


def test_access_token_cannot_be_used_as_refresh_token():
    token = create_access_token({"sub": "1"})

    assert decode_refresh_token(token) is None


def test_expired_access_token_is_rejected():
    token = create_access_token(
        {"sub": "1"},
        expires_delta=timedelta(seconds=-1),
    )

    assert decode_access_token(token) is None


def test_malformed_access_token_is_rejected():
    assert decode_access_token("not.a.valid.jwt") is None


def test_malformed_refresh_token_is_rejected():
    assert decode_refresh_token("not.a.valid.jwt") is None


def test_refresh_token_without_subject_is_rejected():
    token = create_refresh_token({})

    assert decode_refresh_token(token) is None

def test_access_token_without_subject_is_rejected():
    token = create_access_token({})

    assert decode_access_token(token) is None
