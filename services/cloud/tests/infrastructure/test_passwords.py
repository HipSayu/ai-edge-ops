from cloud.infrastructure.security.passwords import hash_password, verify_password


def test_correct_password_verifies():
    stored = hash_password("admin123")
    assert verify_password("admin123", stored)


def test_wrong_password_is_rejected():
    stored = hash_password("admin123")
    assert not verify_password("admin124", stored)


def test_malformed_hash_is_rejected_without_raising():
    assert not verify_password("x", "not-a-hash")
