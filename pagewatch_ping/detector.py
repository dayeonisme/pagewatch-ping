from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from html.parser import HTMLParser


@dataclass(frozen=True)
class ChangeResult:
    changed: bool
    change_type: str
    summary: str


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._ignored_depth = 0
        self._chunks: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in {"script", "style", "noscript", "svg"}:
            self._ignored_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style", "noscript", "svg"} and self._ignored_depth:
            self._ignored_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._ignored_depth:
            return
        normalized = normalize_text(data)
        if normalized:
            self._chunks.append(normalized)


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def text_blocks(html: str) -> list[str]:
    parser = _TextExtractor()
    parser.feed(html)
    return parser._chunks


def fingerprint(html: str) -> str:
    normalized = "\n".join(text_blocks(html))
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def detect_change(previous_html: str | None, current_html: str) -> ChangeResult:
    if not previous_html:
        return ChangeResult(False, "초기 확인", "비교 기준을 저장했습니다.")

    previous_blocks = text_blocks(previous_html)
    current_blocks = text_blocks(current_html)
    if previous_blocks == current_blocks:
        return ChangeResult(False, "변경 없음", "이전 확인 내용과 같습니다.")

    added = _added_blocks(previous_blocks, current_blocks)
    if len(current_blocks) > len(previous_blocks) and added:
        return ChangeResult(True, "신규 게시글 등록", f"추가: {_join_preview(added)}")

    changed = _changed_blocks(previous_blocks, current_blocks)
    if changed:
        return ChangeResult(True, "페이지 내 구성 요소 변경", f"변경: {_join_preview(changed)}")

    return ChangeResult(True, "페이지 내 구성 요소 변경", "텍스트 순서 또는 페이지 구성이 변경되었습니다.")


def _added_blocks(previous: list[str], current: list[str]) -> list[str]:
    remaining = previous.copy()
    added: list[str] = []
    for block in current:
        if block in remaining:
            remaining.remove(block)
        else:
            added.append(block)
    return added[:3]


def _changed_blocks(previous: list[str], current: list[str]) -> list[str]:
    changed: list[str] = []
    for previous_block, current_block in zip(previous, current):
        if previous_block != current_block:
            changed.append(current_block)
        if len(changed) == 3:
            break
    if not changed and len(previous) != len(current):
        changed.extend(current[min(len(previous), len(current)) : min(len(previous), len(current)) + 3])
    return changed


def _join_preview(blocks: list[str]) -> str:
    preview = " / ".join(block[:120] for block in blocks if block)
    return preview if len(preview) <= 300 else f"{preview[:297]}..."
