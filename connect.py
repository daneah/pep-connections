#!/usr/bin/env python

"""A PEP connection parser for viewing PEP information in Obsidian

Use this by dropping it into a directory alongside the PEP files, such as in the root of the python/peps repo
"""

import re
import shutil
from collections import defaultdict
from pathlib import Path
from typing import Optional

from tqdm.rich import tqdm
from rst_to_myst import rst_to_myst


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
        mentioned_pep.rjust(4, "0")
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

    return re.findall(r"PEP:\s+(.*)", pep_content)[0].rjust(4, "0")


def get_title(pep_content: str) -> str:
    """Get the title of the PEP."""

    return re.findall(r"Title:\s+(.*)", pep_content)[0]


def get_status(pep_content: str) -> str:
    """Get the status of the PEP."""

    return slugify(re.findall(r"Status:\s+(.*)", pep_content)[0])


def get_type(pep_content: str) -> str:
    """Get the type of the PEP."""

    return slugify(re.findall(r"Type:\s+(.*)", pep_content)[0])


def get_topics(pep_content: str) -> set[str]:
    """Get assigned topics for the PEP. Most PEPs do not have a topic."""

    try:
        return {
            slugify(topic)
            for topic in re.findall(r"Topic: (.*)", pep_content)[0].split(", ")
        }
    except IndexError:
        return set()


def get_authors(pep_content: str) -> set[str]:
    """Get the authors of the PEP."""
    authors = re.findall(r"Author: (.*)", pep_content)
    if authors:
        return {author.split(" <")[0].strip() for author in authors[0].split(", ")}
    return set()


def get_delegate(pep_content: str) -> Optional[str]:
    """Get the delegate of the PEP."""
    bdfl_delegates = re.findall(r"BDFL-Delegate: (.*)", pep_content)
    pep_delegates = re.findall(r"PEP-Delegate: (.*)", pep_content)
    return (
        (bdfl_delegates or pep_delegates)[0].split(" <")[0].strip()
        if bdfl_delegates or pep_delegates
        else None
    )


def create_clean_output_dir() -> None:
    shutil.rmtree("output", ignore_errors=True)
    Path("output").mkdir()


def output_markdown(connects: dict[str, dict[str, str | set[str] | None]]) -> None:
    """Output PEP connections in a useful format for Obsidian, including status and topic tags

    Example:

    ---
    status: active
    ---

    # PEP 0000: Some title

    ## Mentioned

    - [[0391]]
    - [[0456]]

    ## Authors

    - [[Author Name]]

    ## Content

    This is the content of the PEP.
    """

    for pep, info in connects.items():
        output_path = Path(f"output/{pep}.md")
        output_path.touch()

        with output_path.open("a") as output_file:
            output_file.write("---\n")
            output_file.write(f"status: {info['status']}\n")
            output_file.write(f"type: {info['type']}\n")
            if info["topics"]:
                output_file.write("topics:\n")
                for topic in info["topics"]:
                    output_file.write(f"- {topic}\n")
            output_file.write("---\n")

            output_file.write(f"\n# PEP {pep}: {info['title']}\n\n")

            if info["mentions"]:
                output_file.write("## Mentions\n\n")

                for mention in info["mentions"]:
                    output_file.write(f"- [[{mention}]]\n")

            if info["authors"]:
                output_file.write("\n## Authors\n\n")
                for author in info["authors"]:
                    Path(f"output/{author}.md").touch()
                    output_file.write(f"- [[{author}]]\n")

            if info["delegate"]:
                Path(f"output/{info['delegate']}.md").touch()
                output_file.write("\n## Delegate\n\n")
                output_file.write(f"[[{info['delegate']}]]\n")

            output_file.write("\n## Content\n\n")
            for line in str(info["markdown"]).splitlines():
                output_file.write(re.sub(r"^#", "###", line))
                output_file.write("\n")


if __name__ == "__main__":
    connects: dict[str, dict[str, str | set[str] | None]] = defaultdict(lambda: dict())

    for pep_path in tqdm(sorted(Path(".").glob("pep-*"))):
        with pep_path.open() as pep_file:
            pep_content = pep_file.read()
            pep_identifier = get_identifier(pep_content)
            try:
                connects[pep_identifier]["markdown"] = rst_to_myst(pep_content).text
            except ValueError:
                connects[pep_identifier]["markdown"] = "Error converting to markdown."
            connects[pep_identifier]["mentions"] = get_mentioned_peps(pep_content)
            connects[pep_identifier]["status"] = get_status(pep_content)
            connects[pep_identifier]["topics"] = get_topics(pep_content)
            connects[pep_identifier]["title"] = get_title(pep_content)
            connects[pep_identifier]["type"] = get_type(pep_content)
            connects[pep_identifier]["authors"] = get_authors(pep_content)
            connects[pep_identifier]["delegate"] = get_delegate(pep_content)

    create_clean_output_dir()
    output_markdown(connects)
