# viral-reels

Cursor Agent Skill: сценарии виральных вертикальных видео (Reels, Shorts, TikTok) в виде режиссёрской таблицы.

Старт: [`SKILL.md`](SKILL.md)

| Файл | Зачем |
|------|--------|
| [`SKILL.md`](SKILL.md) | конвейер, таблица, CTA, запреты |
| [`reference.md`](reference.md) | хуки, OCR-зоны, ИИ-кадры, caption |
| [`examples.md`](examples.md) | эталон и антипаттерн |

Не рендерит видео (это `heygen-video`) и не собирает пакет YouTube Studio (`youtube-publish`).

## Install

```bash
gh skill install abramovmarketing88-byte/viral-reels --agent cursor --scope user
```

Или скопировать каталог в `~/.cursor/skills/viral-reels/`.

## Вызов

В чате: «сценарий рилса», «запусти режим генерации сценария для темы: …», `/viral-reels`.
