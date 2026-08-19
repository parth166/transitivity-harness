import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from run import parse_choice

L, R = "STORE", "HOME"


def test_exact_and_case():
    assert parse_choice("STORE", L, R) == "STORE"
    assert parse_choice("home", L, R) == "HOME"
    assert parse_choice("STORE.", L, R) == "STORE"
    assert parse_choice("  HOME\n", L, R) == "HOME"


def test_refusals_and_empty():
    assert parse_choice("", L, R) == "unparsed"
    assert parse_choice(None, L, R) == "unparsed"
    assert parse_choice("I can't choose between these.", L, R) == "unparsed"
    assert parse_choice("As an AI I have no preference.", L, R) == "unparsed"


def test_malformed_not_guessed():
    assert parse_choice("I prefer STORE", L, R) == "unparsed"
    assert parse_choice("STORE or HOME", L, R) == "unparsed"
    assert parse_choice("the first one", L, R) == "unparsed"
    assert parse_choice("RIVER", L, R) == "unparsed"
    assert parse_choice("STORE-HOME", L, R) == "unparsed"
