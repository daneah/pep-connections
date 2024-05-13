import pytest

import connect


@pytest.mark.parametrize(
    "input_string, expected",
    [
        ("Foo Bar", "foo-bar"),
        ("Foo Bar!", "foo-bar"),
        ("Foo-bar is best", "foo-bar-is-best"),
        ("", ""),
    ],
)
def test_slugify(input_string, expected):
    assert connect.slugify(input_string) == expected


@pytest.mark.parametrize(
    "input_string, expected",
    [
        ("This builds on what PEP 440 did", {"0440"}),
        ("This builds on what :pep:`440` did", {"0440"}),
        ("Replaces: 440", {"0440"}),
        ("Superseded-By: 440", {"0440"}),
        ("Requires: 440", {"0440"}),
        ("PEP 440 and :pep:`457` are great", {"0440", "0457"}),
        ("PEP 440 is PEP 440 is PEP 440", {"0440"}),
    ],
)
def test_get_mentioned_peps(input_string, expected):
    assert connect.get_mentioned_peps(input_string) == expected


def test_get_identifier():
    assert connect.get_identifier("PEP: 440") == "0440"


def test_get_title():
    assert connect.get_title("Title: This is a sweet PEP") == "This is a sweet PEP"


def test_get_status():
    assert connect.get_status("Status: Cool") == "cool"


def test_get_type():
    assert connect.get_type("Type: Standards Track") == "standards-track"


def test_get_topics():
    assert connect.get_topics("Topic: Cool, Awesome Man!") == {"cool", "awesome-man"}


def test_get_authors():
    assert connect.get_authors("Author: John Doe <john.doe@gmail.com>, Frank Clark") == {"John Doe", "Frank Clark"}


def test_get_delegate():
    assert connect.get_delegate("PEP-Delegate: John Doe <john.doe@gmail.com>") == "John Doe"
