#!/usr/bin/env python3
"""Validate a viral-reels markdown pack. Execute this script; do not treat it as prose."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

TIMING_RE = re.compile(
    r"\|\s*(\d+):(\d{2})\s*[–-]\s*(\d+):(\d{2})\s*\|"
)
SEO_LINE_RE = re.compile(
    r"SEO-запрос[^:\n]*:\s*`?([^`\n]+?)`?\s*$", re.IGNORECASE | re.M
)
DURATION_RE = re.compile(
    r"Длительность[^:\n]*:\s*`?(\d+)\s*с", re.IGNORECASE
)
HOOK_RE = re.compile(
    r"Модель хука[^:\n]*:\s*`?([^\n`]+?)`?\s*$", re.IGNORECASE | re.M
)
CAPTION_RE = re.compile(
    r"Caption:\s*`?(.+?)`?\s*$", re.IGNORECASE | re.M
)
TITLE_RE = re.compile(
    r"Заголовок(?: Shorts)?[^:\n]*:\s*`?([^`\n]+?)`?\s*$", re.IGNORECASE | re.M
)

ALLOWED_HOOKS = {"ценность", "разрыв шаблона", "кинетика"}
FORBIDDEN = [
    "всем привет",
    "сегодня мы поговорим",
    "в этом видео",
    "подпишись",
    "подписывайтесь",
    "ставь лайк",
    "не забудьте подписаться",
]
TRASH_TAGS = ["#fyp", "#viral", "#длятебя", "#рекомендации", "#xyzbca"]
JARGON = [
    "конверсия",
    "креатив",
    "хайп",
    "фильтр",
    "ctr",
    "выше рынка",
    "из показа",
    "залип",
    "вразброс",
    "баннерн",
    "когнитив",
]


def to_sec(m: int, s: int) -> int:
    return m * 60 + s


def extract_seo(text: str) -> str | None:
    m = SEO_LINE_RE.search(text)
    if not m:
        return None
    return re.sub(r"\s+", " ", m.group(1)).strip().strip("*").strip()


def viewer_facing(text: str) -> str:
    """ASR + OCR + caption + subtitles + title. Not director jargon columns."""
    chunks: list[str] = []
    for rx in (CAPTION_RE, TITLE_RE):
        m = rx.search(text)
        if m:
            chunks.append(m.group(1))
    sub = re.search(r"Субтитры:\s*(.+)$", text, re.M)
    if sub:
        chunks.append(sub.group(1))
    for line in text.splitlines():
        raw = line.strip()
        if not raw.startswith("|"):
            continue
        cells = [c.strip() for c in raw.strip("|").split("|")]
        if len(cells) >= 4 and TIMING_RE.match("| " + cells[0] + " |"):
            chunks.append(cells[2])
            chunks.append(cells[3])
    asr_lines = re.findall(r"ASR:\s*(.+)$", text, re.M | re.I)
    ocr_lines = re.findall(r"OCR:\s*(.+)$", text, re.M | re.I)
    chunks.extend(asr_lines)
    chunks.extend(ocr_lines)
    return "\n".join(chunks)


def parse_timings(text: str) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    for m in TIMING_RE.finditer(text):
        a = to_sec(int(m.group(1)), int(m.group(2)))
        b = to_sec(int(m.group(3)), int(m.group(4)))
        out.append((a, b))
    return out


def speech_text(text: str) -> str:
    """Drop quoted bans and checklist lines so «подпишись» in meta is not a hit."""
    cleaned = re.sub(r"«[^»]*»", " ", text)
    cleaned = re.sub(r'"[^"]*"', " ", cleaned)
    cleaned = re.sub(r"`[^`]*`", " ", cleaned)
    lines = []
    for line in cleaned.splitlines():
        if re.match(r"\s*[-*]\s*\[[xX ]\]", line):
            continue
        low = line.lower()
        if "запрещен" in low or "запрещён" in low:
            continue
        lines.append(line)
    return "\n".join(lines)


def check(text: str) -> list[str]:
    errors: list[str] = []
    lower = speech_text(text).lower()

    seo = extract_seo(text)
    if not seo:
        errors.append("нет строки «SEO-запрос:»")
        seo = ""
    elif not (1 <= len(seo) <= 40):
        errors.append(f"SEO-запрос {len(seo)} символов, нужно 1–40: {seo!r}")

    dur_m = DURATION_RE.search(text)
    duration = int(dur_m.group(1)) if dur_m else None
    if duration is None:
        errors.append("нет «Длительность: N с»")
    elif not (15 <= duration <= 30):
        errors.append(f"длительность {duration} с вне диапазона 15–30")

    hook_m = HOOK_RE.search(text)
    if not hook_m:
        errors.append("нет строки «Модель хука:»")
    else:
        hook = re.sub(r"\s+", " ", hook_m.group(1)).strip().lower()
        hook = hook.split("(")[0].strip()
        if "+" in hook or "," in hook or " и " in hook:
            errors.append(f"модель хука должна быть одна, не смесь: {hook!r}")
        elif hook not in ALLOWED_HOOKS:
            errors.append(
                f"модель хука {hook!r} не из {sorted(ALLOWED_HOOKS)}"
            )

    for phrase in FORBIDDEN:
        if phrase in lower:
            errors.append(f"запрещённая фраза: {phrase!r}")

    viewer = viewer_facing(text).lower()
    for word in JARGON:
        if word in viewer:
            errors.append(f"сложное/рекламное слово в речи или на экране: {word!r}")

    seo_l = (seo or "").lower()
    if re.search(r"авито|объявлен", seo_l) and re.search(
        r"\bролики\b|\bчужие ролики\b", viewer
    ):
        errors.append(
            "смешение объекта: тема про объявления, в голосе «ролики»"
        )

    for line in text.splitlines():
        raw = line.strip()
        if not raw.startswith("|"):
            continue
        cells = [c.strip() for c in raw.strip("|").split("|")]
        if len(cells) < 4 or not TIMING_RE.match("| " + cells[0] + " |"):
            continue
        asr = cells[2].strip()
        low = asr.lower()
        if re.match(r"^не [^.!?]{1,40}[.!?]?$", low) and "шаг" not in low:
            errors.append(
                f"обрубок контраста в ASR: {asr!r} — закрой в той же фразе "
                "(«конкретные шаги, не просто …»)"
            )

    for tag in TRASH_TAGS:
        if tag in lower:
            errors.append(f"мусорный хештег: {tag}")

    timings = parse_timings(text)
    if not timings:
        errors.append("нет строк тайминга вида | 0:00–0:03 |")
    else:
        if timings[0][0] != 0:
            errors.append("первая строка таблицы должна начинаться с 0:00")
        if timings[0] != (0, 3):
            errors.append("первая строка должна быть 0:00–0:03")
        for i, (a, b) in enumerate(timings):
            span = b - a
            if span < 3 or span > 5:
                errors.append(
                    f"отрезок {i + 1}: {a//60}:{a%60:02d}–{b//60}:{b%60:02d} "
                    f"= {span} с, нужно 3–5"
                )
            if i > 0 and a != timings[i - 1][1]:
                errors.append(
                    f"разрыв тайминга между строками {i} и {i + 1}: "
                    f"{timings[i - 1][1]} → {a}"
                )
        end = timings[-1][1]
        if not (15 <= end <= 30):
            errors.append(f"финал таблицы {end} с вне 15–30")
        if duration is not None and end != duration:
            errors.append(
                f"длительность карточки {duration} с ≠ конец таблицы {end} с"
            )

    if seo:
        seo_l = seo.lower()
        asr_hits = lower.count(seo_l)
        if asr_hits < 3:
            errors.append(
                f"SEO {seo!r} встречается {asr_hits} раз, нужно ≥3 "
                "(ASR + OCR + caption/заголовок)"
            )
        cap_m = CAPTION_RE.search(text)
        if cap_m:
            first100 = cap_m.group(1).strip().lower()[:100]
            if seo_l not in first100:
                errors.append("SEO нет в первых 100 символах Caption")
        title_m = TITLE_RE.search(text)
        if title_m and seo_l not in title_m.group(1).strip().lower():
            errors.append("SEO нет в заголовке Shorts")

    # last 5s should mention save/share language
    if "подпишись" not in lower and "подписывайтесь" not in lower:
        if not any(x in lower for x in ("сохрани", "перешли", "save", "share")):
            errors.append("нет CTA Save/Share (сохрани / перешли)")

    return errors


def main() -> int:
    p = argparse.ArgumentParser(description="Validate viral-reels scenario markdown")
    p.add_argument("pack", nargs="+", type=Path, help="Markdown pack file(s)")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()
    any_fail = False
    reports = []
    for path in args.pack:
        if not path.is_file():
            any_fail = True
            reports.append({"file": str(path), "ok": False, "errors": ["файл не найден"]})
            print(f"FAIL {path}: файл не найден", file=sys.stderr)
            continue
        text = path.read_text(encoding="utf-8")
        errors = check(text)
        ok = not errors
        reports.append({"file": str(path), "ok": ok, "errors": errors})
        if ok:
            print(f"OK {path}")
        else:
            any_fail = True
            print(f"FAIL {path}", file=sys.stderr)
            for e in errors:
                print(f"  - {e}", file=sys.stderr)
    if args.json:
        import json

        print(json.dumps(reports, ensure_ascii=False, indent=2))
    return 1 if any_fail else 0


if __name__ == "__main__":
    sys.exit(main())
