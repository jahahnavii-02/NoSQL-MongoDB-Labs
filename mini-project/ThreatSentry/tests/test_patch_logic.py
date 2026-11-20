import pytest
from backend.services.retrieval import detect_filters
from backend.services import mitigation_service as ms


def test_detect_filters():
    assert detect_filters("What active threats affect Windows?") == ("Windows", "Active")
    assert detect_filters("resolved iOS issues") == ("iOS", "Resolved")
    assert detect_filters("tell me about scenarios") == (None, None)  # 'ios' inside a word must not match


def test_build_command_is_allow_listed():
    assert ms.build_command("openssl") == ["apt-get", "install", "--only-upgrade", "-y", "openssl"]
    for bad in ["openssl; rm -rf /", "$(id)", "a b", "", "-y", "../x"]:
        with pytest.raises(ValueError):
            ms.build_command(bad)


def test_chat_command_regex():
    assert ms.COMMAND_RE.match("approve a1b2c3d4").group(1) == "approve"
    assert ms.COMMAND_RE.match("/reject a1b2c3").group(1) == "reject"
    assert ms.FIX_RE.search("fix openssl")
    assert not ms.FIX_RE.search("how do I fix openssl?")
    assert not ms.FIX_RE.search("update me on windows threats")
