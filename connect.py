#!/usr/bin/env python

"""A PEP connection parser for viewing PEP information in Obsidian

Use this by dropping it into a directory alongside the PEP files, such as in the root of the python/peps repo
"""

import re
import shutil
from collections import defaultdict
from pathlib import Path


PEP_FILENAME_PATTERN = re.compile(r"pep-([0-9]{3,4}).(txt|rst)")


def slugify(string: str) -> str:
    """Convert multiple words with special characters into a parseable format"""

    return string.lower().replace(" ", "-").replace("!", "")


def get_mentioned_peps(pep_content: str) -> set[str]:
    """Extract mentions of other PEPs from the current PEP.

    These might be hard references such as :pep:`457`, casual references such as "PEP 457",
    or metadata references such as Superseded-By or Requires.
    """

    return {
        mentioned_pep.rjust(4, '0')
        for pattern in {
            r"PEP ([0-9]{3,4})",
            r":pep:`([0-9]{3,4})`",
            r"Replaces: ([0-9]{3,4})",
            r"Requires: ([0-9]{3,4})",
            r"Superseded-By: ([0-9]{3,4})",
        }
        for mentioned_pep in re.findall(pattern, pep_content)
    }

def get_identifier(pep_content: str) -> str:
    """Get the identifier of the PEP."""

    return re.findall(r"PEP: (.*)", pep_content)[0]


def get_title(pep_content: str) -> str:
    """Get the title of the PEP."""

    return re.findall(r"Title: (.*)", pep_content)[0]


def get_status(pep_content: str) -> str:
    """Get the status of the PEP."""

    return slugify(re.findall(r"Status: (.*)", pep_content)[0])


def get_topics(pep_content: str) -> set[str]:
    """Get assigned topics for the PEP. Most PEPs do not have a topic."""

    try:
        return {slugify(topic) for topic in re.findall(r"^Topic: (.*)", pep_content)[0].split(', ')}
    except IndexError:
        return set()


def create_clean_output_dir() -> None:
    shutil.rmtree("output", ignore_errors=True)
    Path("output").mkdir()


def output_markdown(connects: dict[str, dict[str, str | set[str]]]) -> None:
    """Output PEP connections in a useful format for Obsidian, including status and topic tags

    Example:

    #status--active
    # PEP 0000: Some title

    ## Mentioned

    - [[0391]]
    - [[0456]]
    """

    for pep, info in connects.items():
        output_path = Path(f"output/{pep}.md")
        output_path.touch()

        with output_path.open("a") as output_file:
            output_file.write(f"#status--{info['status']}\n")

            for topic in info['topics']:
                output_file.write(f"#topic--{topic}\n")

            output_file.write(f"\n# PEP {pep}: {info['title']}\n\n")
            output_file.write("## Mentions\n\n")

            for mention in info['mentions']:
                output_file.write(f"- [[{mention}]]\n")


if __name__ == "__main__":
    connects: dict[str, dict[str, str | set[str]]] = defaultdict(lambda: dict())

    for pep_path in Path(".").glob("pep-*"):
        with pep_path.open() as pep_file:
            pep_content = pep_file.read()
            pep_identifier = get_identifier(pep_content)
            connects[pep_identifier]['mentions'] = get_mentioned_peps(pep_content)
            connects[pep_identifier]['status'] = get_status(pep_content)
            connects[pep_identifier]['topics'] = get_topics(pep_content)
            connects[pep_identifier]['title'] = get_title(pep_content)

    create_clean_output_dir()
    output_markdown(connects)
