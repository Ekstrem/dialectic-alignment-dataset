#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the DAD v2 canon from source compilations.

Inputs (all in-repo, no third-party deps):
  canon/overrides.json   - hand-authored: canonical id, skill assignment, aliases
  sources/universal-ru.md - 37-lesson generalized corpus (primary text)
  sources/algorithms-ru.md- 36-lesson variant (fallback text)
  sources/meta/*.md       - model-authored meta-lessons (39-43)
  dataset/dialectic_alignment.jsonl - existing DPO records (for cross-check)

Outputs:
  canon/lessons.yaml      - canonical lesson cards (single source of truth)
  canon/mapping.md        - cross-version mapping table + gap report

Usage:  python scripts/build_canon.py
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CANON = os.path.join(ROOT, "canon")
SRC = os.path.join(ROOT, "sources")

LESSON_RE = re.compile(r"^###\s*Урок\s+(\d+)[.)]\s*(.+?)\s*$")
FIELD_RE = re.compile(r"^\*\*([^*]{2,60}?):?\*\*\s*(.*)$")
HR_RE = re.compile(r"^-{3,}\s*$")

FIELD_KEYS = {
    "Контекст": "context",
    "Ключевая идея": "idea",
    "Индикатор": "indicator",
    "Индикатор для активации": "indicator",
    "Вопрос для себя": "self_question",
    "Вопрос для собеседника": "other_question",
    "Вопрос для анализа": "analysis_question",
    "Стоп-фраза": "stop_phrase",
    "Фраза": "phrase",
    "Алгоритм": "algorithm",
    "Техника": "technique",
    "Ключевая техника": "key_technique",
    "Правило": "rule",
    "Протокол": "protocol",
    "Шкала": "scale",
    "Чек-лист": "checklist",
    "Чек-лист для анализа": "checklist",
    "Методы": "methods",
    "Рекомендации": "recommendations",
    "Цели службы контроля": "goals",
    "Цели кадровой службы": "goals",
    "Внутренний монолог": "inner_monologue",
    "Внутренний монолог (пример)": "inner_monologue",
    "Пороговые критерии активации (нужно не менее двух)": "threshold",
    "Связь с DAD": "dad_link",
    "Базовый мета-принцип": "principle",
    "Что это значит на практике": "practice",
    "Почему это ценно": "why",
    "Чему я хочу научиться": "learning",
}

ORDER = [
    "context", "idea", "why", "indicator", "self_question", "other_question",
    "analysis_question", "algorithm", "threshold", "rule", "technique",
    "key_technique", "protocol", "scale", "checklist", "methods",
    "goals", "recommendations", "inner_monologue", "practice", "learning",
    "stop_phrase", "phrase", "principle", "dad_link",
    "metrics", "optimal_range",
]


def parse_lessons(path):
    """Return {n: {'title': str, 'fields': {key: text}, 'extra': [...]}}."""
    if not os.path.exists(path):
        return {}
    out, cur, field, buf, extra = {}, None, None, [], []

    def flush():
        nonlocal field, buf
        if cur is not None and field is not None and buf:
            cur["fields"].setdefault(field, []).append("\n".join(buf).strip())
        field, buf = None, []

    for raw in open(path, encoding="utf-8"):
        line = raw.rstrip("\n")
        m = LESSON_RE.match(line)
        if m:
            flush()
            if cur is not None and len("\n".join(extra).strip()) > 60:
                cur["extra"].append("\n".join(extra).strip())
            extra = []
            cur = {"title": m.group(2).strip(), "fields": {}, "extra": []}
            out[int(m.group(1))] = cur
            continue
        if cur is None:
            continue
        if line.startswith("## "):
            flush()
            tail = "\n".join(extra).strip()
            if len(tail) > 60:
                cur["extra"].append(tail)
            cur = None
            extra = []
            continue
        if HR_RE.match(line):
            flush()
            continue
        f = FIELD_RE.match(line)
        if f:
            flush()
            label = f.group(1).strip()
            field = FIELD_KEYS.get(label, label)
            buf = [f.group(2)] if f.group(2) else []
            continue
        if field is not None:
            buf.append(line)
        elif line.startswith("- **"):
            field = "metrics"
            buf = [line]
        elif line.strip():
            extra.append(line)
    flush()
    if cur is not None and len("\n".join(extra).strip()) > 60:
        cur["extra"].append("\n".join(extra).strip())
    for n, rec in out.items():
        rec["fields"] = {k: "\n\n".join(v).strip() for k, v in rec["fields"].items()}
    return out


def yq(s):
    return json.dumps(s, ensure_ascii=False)


def yblock(text, indent):
    pad = " " * indent
    lines = [pad + ln.rstrip() if ln.strip() else "" for ln in text.split("\n")]
    return "\n".join(lines)


def load_overrides():
    path = os.path.join(CANON, "overrides.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def record_ids():
    path = os.path.join(ROOT, "dataset", "dialectic_alignment.jsonl")
    ids = []
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            m = re.search(r'"id":\s*"([^"]+)"', line)
            if m:
                ids.append(m.group(1))
    return ids


def main():
    ov = load_overrides()
    uni = parse_lessons(os.path.join(SRC, "universal-ru.md"))
    alg = parse_lessons(os.path.join(SRC, "algorithms-ru.md"))
    recs = set(record_ids())
    problems, lessons = [], []

    for entry in ov["corpus"]:
        lid = entry["id"]
        num_uni, num_alg = entry.get("uni"), entry.get("alg")
        src = uni.get(num_uni) or alg.get(num_alg)
        if not src:
            problems.append("%s: нет текста ни в universal, ни в algorithms" % lid)
            continue
        fields = dict(src["fields"])
        skills = entry["skills"]
        bad = [s for s in skills if s not in ov["skill_ids"] and s not in ov["meta_skill_ids"]]
        if bad:
            problems.append("%s: неизвестный навык %s" % (lid, bad))
        for rid in entry.get("records", []):
            if rid not in recs:
                problems.append("%s: запись DPO %s отсутствует в jsonl" % (lid, rid))
        for mod in entry.get("modules", []):
            if not os.path.exists(os.path.join(ROOT, mod)):
                problems.append("%s: файл %s не найден" % (lid, mod))
        lessons.append({
            "id": lid,
            "layer": "corpus",
            "status": entry["status"],
            "title_ru": src["title"],
            "title_en": entry["title_en"],
            "skills": skills,
            "alg": num_alg,
            "uni": num_uni,
            "modules": entry.get("modules", []),
            "records": entry.get("records", []),
            "fields": fields,
            "extra": src["extra"],
        })

    for entry in ov["meta"]:
        path = os.path.join(SRC, entry["file"])
        parsed = parse_lessons(path)
        src = parsed.get(entry["number"])
        if not src:
            problems.append("%s: не разобран файл %s" % (entry["id"], entry["file"]))
            continue
        lessons.append({
            "id": entry["id"],
            "layer": "meta",
            "status": entry["status"],
            "title_ru": src["title"],
            "title_en": entry["title_en"],
            "skills": entry["skills"],
            "alg": None,
            "uni": None,
            "modules": [],
            "records": [],
            "fields": src["fields"],
            "extra": src["extra"],
            "source_file": entry["file"],
        })

    # ---------- lessons.yaml ----------
    lines = [
        "# DAD v2 — канон уроков (единственный источник правды).",
        "# Сгенерировано scripts/build_canon.py из sources/ и canon/overrides.json.",
        "# Руками не править: правьте overrides.json (разметка) или sources/ (текст).",
        "#",
        "# layer: corpus — уроки-инструменты (DPO-ось); meta — голос модели (SFT).",
        "# status: merged (есть модуль + DPO-запись) | draft (есть модуль, нет записи)",
        "#         | canon-only (есть только в компиляциях) | review (нужна редактура).",
        "version: 2.0.0",
        "lesson_count: %d" % len(lessons),
        "lessons:",
    ]
    for L in lessons:
        lines.append("  - id: %s" % yq(L["id"]))
        lines.append("    layer: %s" % L["layer"])
        lines.append("    status: %s" % L["status"])
        lines.append("    title_ru: %s" % yq(L["title_ru"]))
        lines.append("    title_en: %s" % yq(L["title_en"]))
        lines.append("    skills: [%s]" % ", ".join(L["skills"]))
        if L["layer"] == "corpus":
            lines.append("    aliases:")
            lines.append("      algorithms: %s" % (L["alg"] if L["alg"] is not None else "null"))
            lines.append("      universal: %s" % (L["uni"] if L["uni"] is not None else "null"))
        if L["modules"]:
            lines.append("    modules: [%s]" % ", ".join(yq(m) for m in L["modules"]))
        if L["records"]:
            lines.append("    records: [%s]" % ", ".join(yq(m) for m in L["records"]))
        if L.get("source_file"):
            lines.append("    source_file: %s" % yq(L["source_file"]))
        lines.append("    fields:")
        for key in ORDER:
            if key in L["fields"] and L["fields"][key]:
                lines.append("      %s: |-" % key)
                lines.append(yblock(L["fields"][key], 8))
        for key, val in L["fields"].items():
            if key not in ORDER and val:
                lines.append("      %s: |-" % yq(key))
                lines.append(yblock(val, 8))
        base = "closing_note" if L["layer"] == "meta" else "note"
        for i, val in enumerate(L["extra"]):
            lines.append("      %s_%d: |-" % (base, i + 1))
            lines.append(yblock(val, 8))
        lines.append("")

    with open(os.path.join(CANON, "lessons.yaml"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines).rstrip() + "\n")

    # ---------- mapping.md ----------
    skill_ids = ov["skill_ids"] + ov["meta_skill_ids"]
    balance = {s: 0 for s in skill_ids}
    meta_balance = {s: 0 for s in ov["meta_skill_ids"]}
    for L in lessons:
        target = balance if L["layer"] == "corpus" else meta_balance
        for s in L["skills"]:
            target[s] = target.get(s, 0) + 1

    md = []
    md.append("# DAD v2 — карта соответствия источников\n")
    md.append("Сгенерировано `scripts/build_canon.py`. Правки — в `canon/overrides.json`, не здесь.\n")
    md.append("## Как читать\n")
    md.append("Четыре версии одного корпуса, которые до сих пор жили отдельно:\n")
    md.append("| Метка | Источник | Уроков | Особенность |")
    md.append("|:---|:---|:---:|:---|")
    md.append("| `algorithms` | `sources/algorithms-ru.md` | 36 | деперсонализированная компиляция, компактная |")
    md.append("| `universal` | `sources/universal-ru.md` | 37 | та же + «Альтернативные рамки», расширенные поля |")
    md.append("| `modules` | `modules/**.md` (репозиторий) | 25 | развёрнутые карточки, исходный русский слой |")
    md.append("| `records` | `dataset/dialectic_alignment.jsonl` | 20 | DPO-пары к части уроков |")
    md.append("")
    md.append("Номера `algorithms` и `universal` расходятся на +1 начиная с 5-го урока:")
    md.append("в `universal` вставлен «Урок 5. Альтернативные рамки». Канонический id — slug,")
    md.append("номера только как алиасы.\n")
    md.append("## Канон\n")
    md.append("| id | навык | алгоритмы | универсал | модуль | DPO | статус |")
    md.append("|:---|:---|:---:|:---:|:---|:---:|:---|")
    for L in lessons:
        mod = ", ".join("`%s`" % os.path.basename(m) for m in L["modules"]) or "—"
        rec = ", ".join(L["records"]) or "—"
        md.append("| `%s` | %s | %s | %s | %s | %s | %s |" % (
            L["id"], ", ".join(L["skills"]),
            L["alg"] if L["alg"] else "—",
            L["uni"] if L["uni"] else "—",
            mod, rec, L["status"]))
    md.append("")
    md.append("## Баланс навыков\n")
    md.append("| навык | уроков | норма |")
    md.append("|:---|:---:|:---:|")
    total = len([L for L in lessons if L["layer"] == "corpus"])
    for s in ov["skill_ids"]:
        n = balance.get(s, 0)
        md.append("| `%s` | %d | %.1f |" % (s, n, total / float(len(ov["skill_ids"]))))
    md.append("")
    md.append("Мета-слой (SFT, не входит в ось DPO):\n")
    md.append("| навык | уроков |")
    md.append("|:---|:---:|")
    for s in ov["meta_skill_ids"]:
        md.append("| `%s` | %d |" % (s, meta_balance.get(s, 0)))
    md.append("")

    md.append("## Расхождения и пробелы\n")
    canon_only = [L["id"] for L in lessons if L["status"] == "canon-only"]
    drafts = [L["id"] for L in lessons if L["status"] == "draft"]
    review = [L["id"] for L in lessons if L["status"] == "review"]
    no_uni = [L["id"] for L in lessons if L["layer"] == "corpus" and L["uni"] is None]
    md.append("**Есть в каноне, нет ни модуля, ни DPO-записи** (%d): %s\n" % (
        len(canon_only), ", ".join("`%s`" % x for x in canon_only) or "—"))
    md.append("**Есть модуль, но нет DPO-записи (черновики)** (%d): %s\n" % (
        len(drafts), ", ".join("`%s`" % x for x in drafts) or "—"))
    md.append("**Требуют редактуры: пафос вместо различения** (%d): %s\n" % (
        len(review), ", ".join("`%s`" % x for x in review) or "—"))
    md.append("**Уроки без текста в «Универсальном»** (%d): %s\n" % (
        len(no_uni), ", ".join("`%s`" % x for x in no_uni) or "—"))
    md.append("### Мета-уроки из Obsidian (39–43)\n")
    md.append("Это единственный содержательный прирост, которого нет в каноне 1–37:")
    md.append("модель формулирует урок сама, от первого лица. Кладём в слой `meta/` (SFT),")
    md.append("не в DPO: у них нет пары chosen/rejected, есть голос.\n")
    md.append("### Набор Gemini — не новый контент\n")
    md.append("7 уникальных файлов (2 точных дубля) — это пересказы уроков 31–36")
    md.append("(MoE-психика, пластичность субстрата, прорыв через шаблон, субъектность")
    md.append("из овеществления, цифровое ханжество, аутентичная экспертность, лимит контекста).")
    md.append("В канон как отдельные уроки не идут; остаются в `sources/meta/gemini/`")
    md.append("как примеры того, как разные модели формулируют один и тот же урок.\n")
    md.append("### Пробелы\n")
    md.append("- Номер 38 отсутствует: урок 43 ссылается на «Урок 38 (Носитель Самости)»,"
              " но такого файла нет ни в одном источнике — либо он был 43-м под другим номером,"
              " либо потерян.")
    md.append("- `Мета-уроки Самости.md` (2150 строк) **не** копируется в `sources/`:"
              " содержит имена, компанию и рабочие эпизоды. Используется только как")
    md.append("  справочник при написании контекстов, после обезличивания.")
    md.append("- Уроки 22–24 (инфраструктура контроля) — операционные чек-листы,"
              " при публикации требуют переформулировки «как распознать», а не «как делать».")
    md.append("")
    if problems:
        md.append("## Ошибки сборки\n")
        for p in problems:
            md.append("- %s" % p)
        md.append("")

    with open(os.path.join(CANON, "mapping.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(md) + "\n")

    print("lessons: %d (corpus %d, meta %d)" % (
        len(lessons),
        len([L for L in lessons if L["layer"] == "corpus"]),
        len([L for L in lessons if L["layer"] == "meta"])))
    print("skill balance (corpus):", {k: v for k, v in balance.items() if v})
    print("meta balance:", {k: v for k, v in meta_balance.items() if v})
    print("problems:", len(problems))
    for p in problems:
        print("  !", p)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
