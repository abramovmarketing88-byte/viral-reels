# viral-reels

Cursor Agent Skill: сценарии виральных вертикальных видео (Reels, Shorts, TikTok) в виде режиссёрской таблицы.

Старт: [`SKILL.md`](SKILL.md)

| Файл | Зачем |
|------|--------|
| [`SKILL.md`](SKILL.md) | конвейер, таблица, CTA, запреты |
| [`reference.md`](reference.md) | хуки, OCR-зоны, воронка, ИИ-кадры |
| [`examples.md`](examples.md) | эталон, воронка, антипаттерн |
| [`scripts/validate.py`](scripts/validate.py) | проверка пакета (execute) |
| [`fixtures/good.md`](fixtures/good.md) | пакет, который обязан пройти валидатор |
| [`fixtures/bad.md`](fixtures/bad.md) | брак, который обязан упасть |

Не рендерит видео (`heygen-video`). Не пакет YouTube Studio (`youtube-publish`). Не воронка лендинга (`selling-landing`).

## Install

```bash
gh skill install abramovmarketing88-byte/viral-reels --agent cursor --scope user
```

Или скопировать каталог в `~/.cursor/skills/viral-reels/`.

## Вызов

«сценарий рилса», «запусти режим генерации сценария для темы: …», «воронка рилсов», `/viral-reels`.

## Проверка пакета

```bash
python3 scripts/validate.py fixtures/good.md   # OK
python3 scripts/validate.py fixtures/bad.md    # FAIL
```
