#!/usr/bin/env python3
"""Name every place a contract's data and its document disagree.

Usage: compare_contract.py CONTRACT_JSON DOCUMENT

Prints one line per data text that is not verbatim in the document, and one
line per F, R or P id present in only one of the two, then exits 1. Prints
nothing and exits 0 when they agree. Exits 2 when an input cannot be read or
does not have the expected shape. The document is only searched; nothing is
built from it.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any, Sequence


ID_RE = re.compile(r"\b[FRP]\d+\b")
WHITESPACE_RE = re.compile(r"\s+")
SCALAR_KEYS = ("title", "approved", "intent")
# Each list key: the field holding its text (None when items are strings),
# the label prefix, and the field naming an item (None when items are numbered).
LIST_KEYS = (
    ("failures", "text", "failure", "id"),
    ("additions", "what", "addition", None),
    ("requirements", "text", "requirement", "id"),
    ("premises", "text", "premise", "id"),
    ("exclusions", None, "exclusion", None),
    ("alternatives", "alternative", "alternative", None),
    ("releaseSteps", "step", "release step", None),
)


class ContractError(Exception):
    """An input that cannot be read or does not have the expected shape."""


def collapse(text: str) -> str:
    return WHITESPACE_RE.sub(" ", text)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as error:
        raise ContractError(f"cannot read {path}: {error.strerror or error}") from error
    except UnicodeDecodeError as error:
        raise ContractError(f"cannot read {path}: not UTF-8 text") from error


def load_contract(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(read_text(path))
    except json.JSONDecodeError as error:
        raise ContractError(f"{path} is not valid JSON: {error.msg}") from error
    if not isinstance(data, dict):
        raise ContractError(f"{path} is not a JSON object")
    return data


def string_at(value: Any, key: str) -> str:
    if not isinstance(value, str):
        raise ContractError(f"{key} must be a string")
    return value


def data_texts(data: dict[str, Any]) -> list[tuple[str, str]]:
    """Return (label, text) for every data text the document must contain."""
    entries: list[tuple[str, str]] = []
    for key in SCALAR_KEYS:
        if key in data:
            entries.append((key, string_at(data[key], key)))
    for key, field, label, id_field in LIST_KEYS:
        if key not in data:
            continue
        items = data[key]
        if not isinstance(items, list):
            raise ContractError(f"{key} must be a list")
        for index, item in enumerate(items):
            where = f"{key}[{index}]"
            if field is None:
                entries.append((f"{label} {index + 1}", string_at(item, where)))
                continue
            if not isinstance(item, dict):
                raise ContractError(f"{where} must be an object")
            text = string_at(item.get(field), f"{where}.{field}")
            if id_field is None:
                name = str(index + 1)
            else:
                name = string_at(item.get(id_field), f"{where}.{id_field}")
            entries.append((f"{label} {name}", text))
    return entries


def strings_in(value: Any) -> Iterator[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for child in value.values():
            yield from strings_in(child)
    elif isinstance(value, list):
        for child in value:
            yield from strings_in(child)


def ids_in(texts: Iterable[str]) -> list[str]:
    """Return the distinct F, R or P ids in order of first appearance."""
    return list(dict.fromkeys(match for text in texts for match in ID_RE.findall(text)))


def differences(data: dict[str, Any], document: str) -> list[str]:
    searched = collapse(document)
    lines = [
        f"not in document: {label}: {collapse(text)}"
        for label, text in data_texts(data)
        if collapse(text) not in searched
    ]
    data_ids = ids_in(strings_in(data))
    document_ids = ids_in([document])
    lines += [f"only in data: {ident}" for ident in data_ids if ident not in document_ids]
    lines += [f"only in document: {ident}" for ident in document_ids if ident not in data_ids]
    return lines


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Name every place a contract's data and its document disagree."
    )
    parser.add_argument("contract_json", type=Path, help="the contract data file (JSON)")
    parser.add_argument("document", type=Path, help="the contract's markdown document")
    args = parser.parse_args(argv)
    try:
        lines = differences(load_contract(args.contract_json), read_text(args.document))
    except ContractError as error:
        print(f"compare_contract: {error}", file=sys.stderr)
        return 2
    for line in lines:
        print(line)
    return 1 if lines else 0


if __name__ == "__main__":
    raise SystemExit(main())
