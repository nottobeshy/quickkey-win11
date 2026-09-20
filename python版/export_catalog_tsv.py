# -*- coding: utf-8 -*-
"""把 Python 官方目录导出为 WPF 版可直接读取的 UTF-8 TSV 文件。"""

from pathlib import Path

from shortcuts_catalog import SHORTCUTS


def clean(value: str | None) -> str:
    return (value or "").replace("\t", " ").replace("\r", " ").replace("\n", " ")


root = Path(__file__).resolve().parents[1]
target = root / "data" / "windows_shortcuts.tsv"
target.parent.mkdir(parents=True, exist_ok=True)

lines = ["category\tkeys\taction\trisk\tlesson_id"]
for item in SHORTCUTS:
    lines.append(
        "\t".join(
            clean(value)
            for value in (item.category, item.keys, item.action, item.risk, item.lesson_id)
        )
    )

target.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"Exported {len(SHORTCUTS)} shortcuts to {target}")
