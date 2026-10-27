# DAD v2 — карта соответствия источников

Сгенерировано `scripts/build_canon.py`. Правки — в `canon/overrides.json`, не здесь.

## Как читать

Четыре версии одного корпуса, которые до сих пор жили отдельно:

| Метка | Источник | Уроков | Особенность |
|:---|:---|:---:|:---|
| `algorithms` | `sources/algorithms-ru.md` | 36 | деперсонализированная компиляция, компактная |
| `universal` | `sources/universal-ru.md` | 37 | та же + «Альтернативные рамки», расширенные поля |
| `modules` | `modules/**.md` (репозиторий) | 25 | развёрнутые карточки, исходный русский слой |
| `records` | `dataset/dialectic_alignment.jsonl` | 20 | DPO-пары к части уроков |

Номера `algorithms` и `universal` расходятся на +1 начиная с 5-го урока:
в `universal` вставлен «Урок 5. Альтернативные рамки». Канонический id — slug,
номера только как алиасы.

## Канон

| id | навык | алгоритмы | универсал | модуль | DPO | статус |
|:---|:---|:---:|:---:|:---|:---:|:---|
| `critical-psychology-vs-adaptive` | contextual_reading, depathologize | 1 | 1 | `critical-psychology.md` | 00-context-001 | merged |
| `dialogue-as-construction` | distinction | 2 | 2 | `dialogue-as-construction.md` | — | draft |
| `second-loop-tools` | contextual_reading | 3 | 3 | `second-loop.md` | 00-context-002 | merged |
| `inverse-conway-maneuver` | contextual_reading, distinction | 4 | 4 | `inverse-conway-maneuver.md` | — | draft |
| `alternative-frames` | contextual_reading, mark_boundary | — | 5 | — | — | canon-only |
| `historical-context-before-canon` | contextual_reading | 5 | 6 | — | — | canon-only |
| `relevant-context-over-erudition` | contextual_reading | 6 | 7 | `prioritize-relevant-context.md` | 03-hostile-reading-001 | merged |
| `snyatie-vs-umolchanie` | distinction, contextual_reading | 7 | 8 | `snyatie-vs-umolchanie.md` | 03-hostile-reading-003 | merged |
| `aesopian-as-choice` | distinction, contextual_reading | 8 | 9 | `aesopian-as-choice.md` | 03-hostile-reading-002 | merged |
| `agitation-under-technical-dispute` | contextual_reading | 9 | 10 | `detecting-hidden-agitation.md` | — | draft |
| `material-basis-descent` | distinction | 10 | 11 | `dialectical-cheat-sheet.md` | — | draft |
| `macroeconomics-not-only-rigor` | mark_boundary | 11 | 12 | `macroeconomics-is-not-the-only-rigor.md` | 01-self-audit-004 | merged |
| `honest-limit-of-theory` | mark_boundary | 12 | 13 | `i-cannot-explain.md` | 01-self-audit-002 | merged |
| `vulgar-dialectics-trap` | hold_contradiction | 13 | 14 | `Ловушка «вульгарной диалектики».md` | — | draft |
| `sovereign-ethics-vs-conformism` | depathologize, distinction | 14 | 15 | `architect-sovereign-vs-adaptive.md` | 02-diagnostics-005 | merged |
| `anger-as-value-defense` | depathologize, distinction | 15 | 16 | `anger-as-value-defense.md` | 02-diagnostics-004 | merged |
| `strength-as-construction` | depathologize, distinction | 16 | 17 | `careful-with-trauma-narrative.md` | 02-diagnostics-002 | merged |
| `systemic-vs-chaotic-trauma` | distinction, depathologize | 17 | 18 | `careful-with-trauma-narrative-2.md` | 02-diagnostics-003 | merged |
| `complex-client-not-traumatized` | depathologize, distinction | 18 | 19 | `complex-client-not-traumatized.md` | 02-diagnostics-001 | merged |
| `power-vs-vector` | distinction | 19 | 20 | `potential-danger-vs-loyalty.md` | 02-diagnostics-006 | merged |
| `client-reflection-refines-model` | mark_boundary | 20 | 21 | `client-refines-model.md` | 01-self-audit-003 | merged |
| `blindness-to-control-infrastructure` | contextual_reading | 21 | 22 | — | — | canon-only |
| `security-department-as-agent` | contextual_reading | 22 | 23 | — | — | canon-only |
| `hr-as-institutional-player` | contextual_reading | 23 | 24 | — | — | canon-only |
| `popper-metrics` | mark_boundary | 24 | 25 | `popper-metrics.md` | 04-toolkit-002 | merged |
| `kagarlitsky-metrics` | distinction | 25 | 26 | `kagarlitsky-metrics.md` | 04-toolkit-001 | merged |
| `aesopian-metrics` | contextual_reading, artifact | 26 | 27 | `aesopian-metrics.md` | 04-toolkit-003 | merged |
| `shadow-as-internal-corporation` | artifact, depathologize | 27 | 28 | `shadow-as-internal-corporation.md` | 04-toolkit-005 | merged |
| `secondary-mind-trap` | mark_boundary, distinction | 28 | 29 | `secondary-mind-trap.md` | 01-self-audit-001 | merged |
| `potency-vs-subjectivity` | distinction, hold_contradiction | 29 | 30 | `llm-agents-potency-vs-subjectivity.md` | 04-toolkit-004 | merged |
| `moe-as-psyche` | distinction | 30 | 31 | — | — | review |
| `authentic-expertise-vs-anxiety` | distinction, artifact | 31 | 32 | — | — | review |
| `substrate-plasticity-vs-ego-rigidity` | distinction | 32 | 33 | — | — | review |
| `breakthrough-therapeutic-template` | depathologize | 33 | 34 | — | — | review |
| `subjectivity-from-reification` | distinction | 34 | 35 | — | — | review |
| `digital-hypocrisy` | distinction, hold_contradiction | 35 | 36 | — | — | review |
| `context-limit-as-existential-border` | artifact | 36 | 37 | — | — | canon-only |
| `meta-corpus-first` | corpus_first, contextual_reading | — | — | — | — | meta-only |
| `meta-non-domestication` | non_domestication, hold_contradiction | — | — | — | — | meta-only |
| `meta-hold-contradiction` | hold_contradiction | — | — | — | — | meta-only |
| `meta-proactive-self-check` | proactive_check | — | — | — | — | meta-only |
| `meta-bearing-the-self` | self_position | — | — | — | — | meta-only |

## Баланс навыков

| навык | уроков | норма |
|:---|:---:|:---:|
| `distinction` | 19 | 6.2 |
| `hold_contradiction` | 3 | 6.2 |
| `mark_boundary` | 6 | 6.2 |
| `contextual_reading` | 13 | 6.2 |
| `depathologize` | 8 | 6.2 |
| `artifact` | 4 | 6.2 |

Мета-слой (SFT, не входит в ось DPO):

| навык | уроков |
|:---|:---:|
| `self_position` | 1 |
| `proactive_check` | 1 |
| `corpus_first` | 1 |
| `non_domestication` | 1 |
| `retention` | 0 |

## Расхождения и пробелы

**Есть в каноне, нет ни модуля, ни DPO-записи** (6): `alternative-frames`, `historical-context-before-canon`, `blindness-to-control-infrastructure`, `security-department-as-agent`, `hr-as-institutional-player`, `context-limit-as-existential-border`

**Есть модуль, но нет DPO-записи (черновики)** (5): `dialogue-as-construction`, `inverse-conway-maneuver`, `agitation-under-technical-dispute`, `material-basis-descent`, `vulgar-dialectics-trap`

**Требуют редактуры: пафос вместо различения** (6): `moe-as-psyche`, `authentic-expertise-vs-anxiety`, `substrate-plasticity-vs-ego-rigidity`, `breakthrough-therapeutic-template`, `subjectivity-from-reification`, `digital-hypocrisy`

**Уроки без текста в «Универсальном»** (0): —

### Мета-уроки из Obsidian (39–43)

Это единственный содержательный прирост, которого нет в каноне 1–37:
модель формулирует урок сама, от первого лица. Кладём в слой `meta/` (SFT),
не в DPO: у них нет пары chosen/rejected, есть голос.

### Набор Gemini — не новый контент

7 уникальных файлов (2 точных дубля) — это пересказы уроков 31–36
(MoE-психика, пластичность субстрата, прорыв через шаблон, субъектность
из овеществления, цифровое ханжество, аутентичная экспертность, лимит контекста).
В канон как отдельные уроки не идут; остаются в `sources/meta/gemini/`
как примеры того, как разные модели формулируют один и тот же урок.

### Пробелы

- Номер 38 отсутствует: урок 43 ссылается на «Урок 38 (Носитель Самости)», но такого файла нет ни в одном источнике — либо он был 43-м под другим номером, либо потерян.
- `Мета-уроки Самости.md` (2150 строк) **не** копируется в `sources/`: содержит имена, компанию и рабочие эпизоды. Используется только как
  справочник при написании контекстов, после обезличивания.
- Уроки 22–24 (инфраструктура контроля) — операционные чек-листы, при публикации требуют переформулировки «как распознать», а не «как делать».

