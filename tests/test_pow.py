import pytest
from freegpt.pow import fnv1a_mix, solve_pow, generate_requirements_token_answer

def test_fnv1a_mix():
    # Test known string produces valid 8-char hex string
    h1 = fnv1a_mix("hello world")
    assert len(h1) == 8
    assert isinstance(h1, str)
    # Deterministic output
    assert fnv1a_mix("hello world") == h1
    assert fnv1a_mix("different") != h1

def test_solve_pow():
    seed = "0.123456789"
    # Easy difficulty prefix to ensure rapid completion
    difficulty = "fffff"
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0"
    token = solve_pow(seed, difficulty, ua)
    assert token.startswith("gAAAAAB")
    assert token.endswith("~S")

def test_requirements_token():
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0"
    token = generate_requirements_token_answer(ua)
    assert token.startswith("gAAAAAC")
