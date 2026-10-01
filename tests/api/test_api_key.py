"""API の合言葉(`DIARY_API_KEYS`)。環境変数にはハッシュだけを置き、届いた鍵のハッシュと比べる。"""
import hashlib

import pytest

from gui.api.app import _caller, _parse_api_keys

KEY = "0123456789abcdef" * 4
DIGEST = hashlib.sha256(KEY.encode()).hexdigest()


def test_hashed_key():
    keys = _parse_api_keys(f"gui=sha256:{DIGEST.upper()}")

    assert (_caller(KEY, keys), _caller("違う鍵", keys), _caller("", keys)) == ("gui", None, None)


def test_plain_key_still_read():
    keys = _parse_api_keys(f"gui={KEY}, other=sha256:{'0' * 64}")

    assert keys == {"gui": DIGEST, "other": "0" * 64}
    assert _caller(KEY, keys) == "gui"


def test_hash_given_as_key_is_rejected():
    keys = _parse_api_keys(f"gui=sha256:{DIGEST}")

    assert _caller(DIGEST, keys) is None
    assert _caller(f"sha256:{DIGEST}", keys) is None


@pytest.mark.parametrize("raw", ["gui", "gui=", "=x", "gui=sha256:abc", f"gui=sha256:{'g' * 64}"])
def test_bad_keys(raw):
    with pytest.raises(ValueError):
        _parse_api_keys(raw)
