from types import SimpleNamespace

from aiko.access import has_bf_access, is_original_owner, relationship_label


def test_original_owner_is_always_bf_and_owner():
    settings = SimpleNamespace(owner_id=42)
    assert is_original_owner(settings, 42)
    assert has_bf_access(settings, 42, None)
    assert relationship_label(settings, 42, None) == "Owner BF 👑💗"


def test_pass_holder_is_bf_but_not_original_owner():
    settings = SimpleNamespace(owner_id=42)
    row = {"bf_access": 1}
    assert has_bf_access(settings, 77, row)
    assert not is_original_owner(settings, 77)
    assert relationship_label(settings, 77, row) == "BF 💗"


def test_user_without_pass_is_friend():
    settings = SimpleNamespace(owner_id=42)
    row = {"bf_access": 0}
    assert not has_bf_access(settings, 77, row)
    assert relationship_label(settings, 77, row) == "Friend 🤝"


def test_older_row_without_new_column_defaults_to_friend():
    settings = SimpleNamespace(owner_id=42)
    assert not has_bf_access(settings, 77, {"pass_code": None})
