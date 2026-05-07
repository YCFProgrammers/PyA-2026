import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

# permitir importar el cog sin instalar el paquete
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cogs.moderation import Moderation  # noqa: E402


def _make_msg(content: str, *, attachments=None, stickers=None, embeds=None):
    guild = MagicMock()
    guild.members = []
    guild.roles = []
    guild.channels = []
    return SimpleNamespace(
        content=content,
        guild=guild,
        attachments=attachments or [],
        stickers=stickers or [],
        embeds=embeds or [],
    )


def _cog():
    return Moderation(bot=MagicMock())


def test_repeated_chars():
    cog = _cog()
    spam, _ = cog.is_spam(_make_msg("aaaaaaaa hola"))
    assert spam is True


def test_repeated_word():
    cog = _cog()
    spam, _ = cog.is_spam(_make_msg("hola hola hola hola"))
    assert spam is True


def test_normal_message_not_spam():
    cog = _cog()
    spam, _ = cog.is_spam(_make_msg("Hola, ¿cómo están todos?"))
    assert spam is False


def test_url_not_spam():
    cog = _cog()
    spam, _ = cog.is_spam(_make_msg("mira esto https://tenor.com/view/some-very-long-gif-id-xyz"))
    assert spam is False


def test_custom_emoji_not_spam():
    cog = _cog()
    spam, _ = cog.is_spam(_make_msg("<:custom_emoji_name:123456789012345678>"))
    assert spam is False


def test_alternating_caps_detected():
    cog = _cog()
    assert cog.has_alternating_caps("HOLA mundo ESTO es TEST") is True


def test_alternating_caps_short():
    cog = _cog()
    assert cog.has_alternating_caps("HOLA") is False


def test_alternating_caps_normal():
    cog = _cog()
    assert cog.has_alternating_caps("hola que tal") is False


def test_url_only_not_alternating():
    cog = _cog()
    assert cog.has_alternating_caps("https://example.com/PATH") is False
