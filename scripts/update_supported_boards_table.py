#!/usr/bin/env python3
"""Append newly discovered boards to the manually maintained README tables."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml


BEGIN_MARKER = "<!-- BEGIN SUPPORTED_BOARDS -->"
END_MARKER = "<!-- END SUPPORTED_BOARDS -->"
MAX_BOARD_DIRECTORY_DEPTH = 3
TABLE_HEADERS = {
    "cn": ["板卡图片", "开发板", "芯片", "设备能力"],
    "en": ["Photo", "Board", "Chip", "Device capabilities"],
}


def _format_chip(chip: str) -> str:
    normalized = chip.lower().replace("-", "")
    if normalized == "esp32":
        return "ESP32"
    if normalized.startswith("esp32") and len(normalized) > len("esp32"):
        return f"ESP32-{normalized[len('esp32'):].upper()}"
    return chip.upper()


def _discover_boards(repo_root: Path) -> list[tuple[str, str]]:
    boards = []
    for info_path in sorted(repo_root.rglob("board_info.yaml")):
        board_dir = info_path.parent.relative_to(repo_root)
        if (
            len(board_dir.parts) > MAX_BOARD_DIRECTORY_DEPTH
            or any(part.startswith(".") for part in board_dir.parts)
        ):
            continue
        with info_path.open(encoding="utf-8") as file:
            info = yaml.safe_load(file) or {}
        if not isinstance(info, dict):
            raise SystemExit(f"invalid board definition: {info_path}")
        board = str(info.get("board") or info_path.parent.name)
        chip = str(info.get("chip") or "")
        if not chip:
            raise SystemExit(f"{info_path} is missing chip")
        if board != info_path.parent.name:
            raise SystemExit(
                f"board name {board!r} must match directory {info_path.parent.name!r}"
            )
        boards.append((board, _format_chip(chip)))
    if not boards:
        raise SystemExit("no board_info.yaml found; add at least one board directory")
    return boards


def _table_cells(line: str) -> list[str]:
    return [cell.strip() for cell in re.split(r"(?<!\\)\|", line.strip().strip("|"))]


def _existing_boards(table: str) -> set[str]:
    names = set()
    for line in table.splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = _table_cells(line)
        # Four-column tables start with a photo; legacy tables start with a board.
        board_cell = cells[1] if len(cells) == 4 else cells[0]
        match = re.search(r"<code>\s*([^<]+?)\s*</code>|`([^`]+)`", board_cell)
        if match:
            names.add(match.group(1) or match.group(2))
        elif board_cell and all(board_cell not in headers for headers in TABLE_HEADERS.values()):
            names.add(board_cell)
    return names


def _render_rows(boards: list[tuple[str, str]], language: str) -> str:
    alt = "板卡图片" if language == "cn" else "Board photo"
    photo = f'<img src="docs/images/example_board.svg" alt="{alt}" width="120">'
    return "".join(f"| {photo} | `{board}` | {chip} | |\n" for board, chip in boards)


def _append_rows(section: str, boards: list[tuple[str, str]], language: str) -> str:
    rows = _render_rows(boards, language)
    table_lines = list(re.finditer(r"(?m)^[ \t]*\|[^\n]*(?:\n|$)", section))
    if table_lines:
        end = table_lines[-1].end()
        separator = "" if section[:end].endswith("\n") else "\n"
        return section[:end] + separator + rows + section[end:]
    header = "| " + " | ".join(TABLE_HEADERS[language]) + " |\n| --- | --- | --- | --- |\n"
    return section + ("" if section.endswith("\n\n") else "\n") + header + rows


def update_readme(readme_path: Path, repo_root: Path, language: str) -> None:
    content = readme_path.read_text(encoding="utf-8")
    start = content.find(BEGIN_MARKER)
    end = content.find(END_MARKER, start + len(BEGIN_MARKER))
    if start == -1 or end == -1:
        raise SystemExit(
            f"{readme_path} must contain {BEGIN_MARKER} and {END_MARKER} markers"
        )
    table_start = start + len(BEGIN_MARKER)
    table = content[table_start:end]
    existing = _existing_boards(table)
    new_boards = [entry for entry in _discover_boards(repo_root) if entry[0] not in existing]
    if not new_boards:
        return
    groups = list(re.finditer(r"(?m)^###[ \t]+([^\n]+)$", table))
    if not groups and any(line.lstrip().startswith("|") for line in table.splitlines()):
        table = _append_rows(table, new_boards, language)
    else:
        pending = {}
        for board, chip in new_boards:
            pending.setdefault(chip, []).append((board, chip))
        for index in range(len(groups) - 1, -1, -1):
            group = groups[index]
            chip = _format_chip(group.group(1).strip())
            boards = pending.pop(chip, [])
            if boards:
                finish = groups[index + 1].start() if index + 1 < len(groups) else len(table)
                section = _append_rows(table[group.start():finish], boards, language)
                table = table[:group.start()] + section + table[finish:]
        for chip, boards in pending.items():
            if not table.endswith("\n"):
                table += "\n"
            if not table.endswith("\n\n"):
                table += "\n"
            table += _append_rows(f"### {chip}\n\n", boards, language)
    readme_path.write_text(content[:table_start] + table + content[end:], encoding="utf-8")


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    update_readme(repo_root / "README.md", repo_root, "en")
    update_readme(repo_root / "README_CN.md", repo_root, "cn")
    return 0


if __name__ == "__main__":
    sys.exit(main())
