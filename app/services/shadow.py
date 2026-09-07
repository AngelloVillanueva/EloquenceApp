"""Listen & Repeat — phrase bank, scoring, and articulation coaching (no GPU)."""

from __future__ import annotations

import re
from typing import Any

_WORD = re.compile(r"[a-z0-9']+", re.IGNORECASE)

GLOSS_SYSTEM = (
    "You translate short English phrases into natural Latin American Spanish. "
    "Reply with the translation only: no quotes, no notes, no English, one line."
)

DEFAULT_PROMPTS: list[dict[str, str]] = [
    {
        "id": "bank-walkthrough",
        "text": "Could you walk me through your thinking?",
        "tip": "Link walk me through — don't pause on each word.",
        "es": "¿Podrías explicarme tu razonamiento paso a paso?",
        "kind": "bank",
    },
    {
        "id": "bank-circle",
        "text": "I'd rather circle back after the review.",
        "tip": "Circle back as one phrase, not two ideas.",
        "es": "Preferiría retomarlo después de la revisión.",
        "kind": "bank",
    },
    {
        "id": "bank-tradeoffs",
        "text": "The trade-offs are defensible.",
        "tip": "Trade-offs: stress on trade.",
        "es": "Las concesiones se pueden defender.",
        "kind": "bank",
    },
    {
        "id": "bank-elaborate",
        "text": "Let me elaborate on that point.",
        "tip": "Elaborate: four syllables, stress on lab.",
        "es": "Permíteme profundizar en ese punto.",
        "kind": "bank",
    },
    {
        "id": "bank-pushback",
        "text": "We should push back on the timeline.",
        "tip": "Push back — two beats, not 'pushback' as one rush.",
        "es": "Deberíamos cuestionar el cronograma.",
        "kind": "bank",
    },
]

# Spanish-speaker articulation rules: what to *do* with the mouth, not just what failed.
# Ordered by how often a B2 hispanohablante trips on them.
_SOUND_RULES: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(r"^(th)"),
        "«th» inicial: la lengua asoma entre los dientes y el aire sale continuo. "
        "No es «d» ni «t» (think ≠ tink).",
    ),
    (
        re.compile(r"(th)"),
        "«th» interna: lengua entre los dientes sin cortar el aire (father, breathe).",
    ),
    (
        re.compile(r"^s[bcdfgklmnpqrtvwxz]"),
        "No agregues «e» al inicio: es /s/ + consonante directo (speak, no «espeak»).",
    ),
    (
        re.compile(r"v"),
        "«v»: dientes de arriba sobre el labio de abajo y vibra. En español dirías «b» — aquí no.",
    ),
    (
        re.compile(r"^h"),
        "«h» inglesa suena: sopla aire suave desde la garganta (have, no «af»).",
    ),
    (
        re.compile(r"^j|dg|ge$"),
        "«j»/«dge»: sonido /dʒ/ como «ll» rioplatense fuerte (judge), no la «j» española.",
    ),
    (
        re.compile(r"sh|ti(on)|ci(al)"),
        "«sh» /ʃ/: aire plano y sostenido, sin el toque de lengua de «ch».",
    ),
    (
        re.compile(r"ch"),
        "«ch» /tʃ/: empieza cortando el aire con la lengua y luego suéltalo.",
    ),
    (
        re.compile(r"ed$"),
        "«-ed» final: suena /t/, /d/ o /ɪd/ según la letra previa — no lo pronuncies «ed» siempre.",
    ),
    (
        re.compile(r"ing$"),
        "«-ing»: cierra en /ŋ/ nasal, sin «g» dura al final.",
    ),
    (
        re.compile(r"^r|rr"),
        "«r» inglesa: lengua atrás sin vibrar ni golpear el paladar. No es la «r» española.",
    ),
    (
        re.compile(r"z|s$"),
        "«z» y muchas «s» finales vibran (/z/): zoo, is, does. La «s» española es muda.",
    ),
    (
        re.compile(r"w"),
        "«w»: labios redondeados como «u» que arranca; no digas «gu» (work, no «guork»).",
    ),
    (
        re.compile(r"ee|ea"),
        "Vocal larga /iː/: mantenla (beach, need). Si la cortas suena a otra palabra.",
    ),
    (
        re.compile(r"^[aeiou]?i[bcdfgklmnprstvz]"),
        "«i» corta /ɪ/: relajada, entre «i» y «e» (live, bit) — no la estires.",
    ),
    (
        re.compile(r"ough|augh"),
        "«ough/augh» es irregular: escucha el modelo y copia, la escritura engaña.",
    ),
    (
        re.compile(r"(sts|ths|nds|cts)$"),
        "Grupo consonántico final: pronuncia todas, despacio primero (asks, months).",
    ),
    (
        re.compile(r"qu"),
        "«qu» suena /kw/ con labios redondeados (question), no «k» sola.",
    ),
    (
        re.compile(r"y$"),
        "«-y» final: /i/ corta y sin acento; el peso va en la sílaba fuerte.",
    ),
]

_GENERIC_FIX = (
    "Escucha el modelo, dilo sílaba por sílaba y luego a velocidad normal. "
    "Si sigue distinto, alarga la vocal acentuada."
)


def words(text: str) -> list[str]:
    return [m.group(0).lower() for m in _WORD.finditer(text or "")]


def coach_word(word: str, *, limit: int = 2) -> list[str]:
    """Concrete, Spanish-language articulation cues for one English word."""
    w = (word or "").strip().lower()
    if not w:
        return []
    fixes: list[str] = []
    for pattern, hint in _SOUND_RULES:
        if pattern.search(w) and hint not in fixes:
            fixes.append(hint)
            if len(fixes) >= limit:
                break
    if not fixes:
        fixes.append(_GENERIC_FIX)
    return fixes


def clean_gloss(raw: str) -> str:
    """First line of an LLM translation, without quotes or labels."""
    text = (raw or "").strip()
    if not text:
        return ""
    line = text.splitlines()[0].strip()
    line = re.sub(r'^(spanish|traducci[oó]n|es)\s*[:\-]\s*', "", line, flags=re.IGNORECASE)
    return line.strip().strip('"').strip("'").strip()


def score_repeat(target: str, heard: str) -> dict[str, Any]:
    """Word-level overlap plus how to fix the misses. Not a game score."""
    target_words = words(target)
    heard_set = set(words(heard))
    marked: list[dict[str, Any]] = []
    hits = 0
    for w in target_words:
        ok = w in heard_set
        if ok:
            hits += 1
        marked.append({"word": w, "ok": ok})
    total = len(target_words)
    ratio = hits / total if total else 0.0
    coach = [
        {"word": w, "fixes": coach_word(w)}
        for w in dict.fromkeys(m["word"] for m in marked if not m["ok"])
    ][:3]
    return {
        "heard": (heard or "").strip(),
        "target": (target or "").strip(),
        "hits": hits,
        "total": total,
        "ratio": round(ratio, 3),
        "close": ratio >= 0.7,
        "words": marked,
        "coach": coach,
    }


def coach_phrase(text: str, *, limit: int = 3) -> list[dict[str, Any]]:
    """Articulation cues for the trickiest words in a phrase."""
    out: list[dict[str, Any]] = []
    for w in dict.fromkeys(words(text)):
        if len(w) < 3:
            continue
        fixes = [
            hint for pattern, hint in _SOUND_RULES if pattern.search(w)
        ][:2]
        if fixes:
            out.append({"word": w, "fixes": fixes})
        if len(out) >= limit:
            break
    return out


def merge_prompts(
    pronunciation: list[dict[str, Any]],
    *,
    limit: int = 8,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in pronunciation:
        text = str(item.get("original") or item.get("word") or "").strip()
        if not text:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append({
            "id": f"slip-{len(out)}",
            "text": text,
            "tip": str(item.get("note") or item.get("tip") or "Listen once, then repeat."),
            "es": "",
            "kind": "pronunciation",
            "coach": coach_phrase(text),
        })
        if len(out) >= limit:
            return out
    for bank in DEFAULT_PROMPTS:
        key = bank["text"].lower()
        if key in seen:
            continue
        seen.add(key)
        entry: dict[str, Any] = dict(bank)
        entry["coach"] = coach_phrase(bank["text"])
        out.append(entry)
        if len(out) >= limit:
            break
    return out
