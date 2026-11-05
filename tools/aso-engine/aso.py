#!/usr/bin/env python3
"""App Store Optimization — deterministic analysis of a listing, no invented data.

This tool does not pretend to know search volume, competitor rankings or Apple's
internal signals. It works from the only thing it can see: the copy the developer
wrote. Everything it reports is arithmetic or a rule that App Store Connect
enforces.

What it does:

* measures the budget of every field against App Store Connect's limits
* finds keywords that are duplicated, too short, or never echoed in the name or
  description (discoverability hints, not predictions)
* flags superlatives and claims Apple's reviewers push back on
* proposes keyword candidates **extracted from the developer's own description**
  that still fit the remaining budget, with the character arithmetic shown

Usage::

    python3 tools/aso-engine/aso.py metadata.json
    python3 tools/aso-engine/aso.py metadata.json --locale tr-TR --json
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))

from apple_native import __version__
from apple_native.cli import build_parser, emit
from apple_native.report import Report

LIMITS = {"name": 30, "subtitle": 30, "keywords": 100, "promotional_text": 170, "description": 4000}

ALIASES = {
    "privacyPolicyUrl": "privacy_url",
    "supportUrl": "support_url",
    "marketingUrl": "marketing_url",
    "promotionalText": "promotional_text",
    "whatsNew": "whats_new",
}

STOPWORDS = {
    "the", "and", "for", "with", "your", "you", "that", "this", "from", "are", "was", "were", "will",
    "can", "all", "our", "their", "they", "them", "has", "have", "had", "but", "not", "any", "its",
    "into", "out", "more", "most", "when", "what", "how", "who", "why", "use", "using", "used",
    "app", "apps", "ios", "ipados", "macos", "watchos", "visionos", "new", "one", "get",
}

#: Phrases Apple's reviewers treat as unverifiable or misleading in listing copy.
RISKY_CLAIMS = [
    (r"\bbest\b", "“best” is unverifiable — App Store Review Guideline 2.3.1 asks for accurate claims"),
    (r"#\s?1\b", "“#1” ranking claims need evidence you cannot submit"),
    (r"\bworld'?s\b", "superlatives such as “world's” read as marketing inflation"),
    (r"\bguarantee[ds]?\b", "“guaranteed” promises outcomes the app cannot control"),
    (r"\b100%\s*(free|secure|accurate)\b", "absolute claims invite reviewer scrutiny"),
    (r"\bfree\b(?!\s*(trial|account|tier|version))", "“free” must describe the actual pricing model"),
]


def _text(value: object) -> str:
    return value if isinstance(value, str) else ("" if value is None else str(value))


def _tokens(copy: str) -> List[str]:
    return [token for token in re.split(r"[^a-z0-9]+", copy.lower()) if token]


def _apply_aliases(fields: Dict[str, object]) -> Dict[str, object]:
    out = dict(fields)
    for alias, canonical in ALIASES.items():
        if alias in out and canonical not in out:
            out[canonical] = out.pop(alias)
    return out


def _locales(payload: Dict[str, object]) -> Dict[str, Dict[str, object]]:
    localisations = payload.get("localizations")
    if isinstance(localisations, dict) and localisations:
        return {locale: _apply_aliases(fields) for locale, fields in localisations.items()}
    return {"default": _apply_aliases(payload)}


def analyse_locale(report: Report, locale: str, fields: Dict[str, object]) -> Dict[str, object]:
    prefix = f"[{locale}] " if locale != "default" else ""
    name = _text(fields.get("name"))
    subtitle = _text(fields.get("subtitle"))
    keywords = _text(fields.get("keywords"))
    description = _text(fields.get("description"))

    budget = {}
    for field, limit in LIMITS.items():
        value = _text(fields.get(field))
        if not value:
            continue
        used = len(value)
        remaining = limit - used
        budget[field] = {"used": used, "limit": limit, "remaining": remaining}
        if remaining < 0:
            report.error("ASO001", f"{prefix}{field} is {used} characters; the ceiling is {limit}.",
                         hint=f"Cut {abs(remaining)} characters.")
        elif field in ("name", "subtitle", "keywords") and remaining >= 15:
            report.info("ASO002", f"{prefix}{field} leaves {remaining} of {limit} characters unused.",
                        hint="Unused budget is free discoverability; add a real feature or synonym.")

    return {"budget": budget, "name": name, "subtitle": subtitle, "keywords": keywords,
            "description": description, "fields": fields}


def keyword_findings(report: Report, prefix: str, keywords: str, name: str, subtitle: str,
                     description: str) -> Dict[str, object]:
    raw_tokens = [t.strip() for t in keywords.split(",") if t.strip()]
    lowered = [t.lower() for t in raw_tokens]
    duplicates = sorted({t for t in lowered if lowered.count(t) > 1})
    if duplicates:
        report.warn("ASO010", f"{prefix}duplicate keywords: {', '.join(duplicates)}",
                    hint="Duplicates consume the 100-character budget without adding reach.")

    singles = [t for t in raw_tokens if len(t) < 2]
    if singles:
        report.info("ASO011", f"{prefix}single-character keywords: {', '.join(singles)}",
                    hint="They rarely match a search query and still cost characters.")

    copy_tokens = set(_tokens(name + " " + subtitle + " " + description))
    unseen = [t for t in lowered if t and t not in copy_tokens]
    if unseen:
        report.info("ASO012", f"{prefix}{len(unseen)} keyword(s) never appear in the name, subtitle or description.",
                    hint="Apple indexes all three; echoing a keyword in visible copy reinforces it. "
                         f"Examples: {', '.join(unseen[:6])}")

    overlap = [t for t in lowered if t in _tokens(name)]
    if overlap:
        report.warn("ASO013", f"{prefix}keywords repeat words already in the app name: {', '.join(overlap[:5])}",
                    hint="The name is already indexed; spend the budget on different terms.")
    return {"declared": len(raw_tokens), "unseen": unseen}


def claim_findings(report: Report, prefix: str, copy: str) -> None:
    for pattern, reason in RISKY_CLAIMS:
        match = re.search(pattern, copy, re.IGNORECASE)
        if match:
            report.warn("ASO020", f"{prefix}listing says “{match.group(0)}” — {reason}.",
                        hint="Rewrite as a concrete, demonstrable statement.")


def description_findings(report: Report, prefix: str, description: str) -> None:
    if not description:
        return
    first_block = description.strip().split("\n\n")[0]
    if len(first_block) > 170:
        report.info("ASO021", f"{prefix}the first paragraph is {len(first_block)} characters.",
                    hint="App Store shows roughly three lines before “more”; lead with the benefit.")
    bullets = len(re.findall(r"^\s*[-•*]\s+", description, re.MULTILINE))
    if bullets == 0 and len(description) > 600:
        report.info("ASO022", f"{prefix}description has no bullet list.",
                    hint="Scannable features outperform paragraphs on the product page.")
    if not re.search(r"https://", description):
        report.info("ASO023", f"{prefix}description contains no link.",
                    hint="Only https:// links are tappable; a support or privacy link is expected.")


def suggest_keywords(report: Report, prefix: str, analysed: Dict[str, object]) -> List[str]:
    """Propose candidates from the developer's own copy that fit the remaining budget."""

    keywords = str(analysed["keywords"])
    used = {t.lower() for t in keywords.split(",") if t.strip()}
    budget = LIMITS["keywords"] - len(keywords) - (1 if keywords else 0)
    available = budget
    if budget <= 4:
        report.info("ASO030", f"{prefix}no keyword budget left to suggest into.",
                    hint="Remove a duplicate or a keyword already in the name to make room.")
        return []

    counts: Dict[str, int] = {}
    for token in _tokens(str(analysed["description"]) + " " + str(analysed["subtitle"])):
        if len(token) < 4 or token in STOPWORDS or token in used:
            continue
        counts[token] = counts.get(token, 0) + 1

    ranked = sorted(counts.items(), key=lambda item: (-item[1], -len(item[0])))
    suggestions: List[str] = []
    for token, _ in ranked:
        if len(token) + 1 > budget:
            continue
        suggestions.append(token)
        budget -= len(token) + 1
        if len(suggestions) >= 8:
            break

    if suggestions:
        report.info("ASO031", f"{prefix}{len(suggestions)} candidate keyword(s) fit the {available} remaining characters.",
                    hint="Extracted from your own description by frequency — no search-volume data is used. "
                         f"Candidates: {', '.join(suggestions)}")
    return suggestions


def analyse(payload: Dict[str, object], source: str) -> Report:
    report = Report(tool="aso-engine", target=source, version=__version__)
    locales = _locales(payload)
    results: Dict[str, object] = {"locales": sorted(locales.keys()), "analysis": {}}

    for locale, fields in locales.items():
        prefix = f"[{locale}] " if locale != "default" else ""
        analysed = analyse_locale(report, locale, fields)
        keyword_findings(report, prefix, str(analysed["keywords"]), str(analysed["name"]),
                         str(analysed["subtitle"]), str(analysed["description"]))
        claim_findings(report, prefix, " ".join(str(analysed[k]) for k in ("name", "subtitle",
                                                                          "description", "keywords")))
        description_findings(report, prefix, str(analysed["description"]))
        suggestions = suggest_keywords(report, prefix, analysed)
        results["analysis"][locale] = {  # type: ignore[index]
            "budget": analysed["budget"],
            "keyword_suggestions": suggestions,
        }

    results["method"] = ("Deterministic: character budgets, token analysis of your own copy, and Apple's written "
                         "rules. No search-volume, ranking or competitor data is used or invented.")
    report.data = results
    return report


def main(argv=None) -> int:
    parser = build_parser(
        "aso-engine",
        "Analyse App Store listing copy: budgets, keyword waste, risky claims, and coverage suggestions.",
        epilog="Exit codes: 0 pass, 1 warnings with --strict, 2 failure.",
    )
    parser.add_argument("--locale", help="Analyse only this locale")
    args = parser.parse_args(argv)

    candidate = Path(args.path).expanduser()
    if not candidate.is_file():
        report = Report(tool="aso-engine", target=str(candidate), version=__version__)
        report.error("ASO000", f"Metadata file not found: {candidate}",
                     hint="Pass the listing JSON as the positional argument.")
        return emit(report, args)

    try:
        payload = json.loads(candidate.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        report = Report(tool="aso-engine", target=str(candidate), version=__version__)
        report.error("ASO000", f"Metadata is not valid JSON: {exc}")
        return emit(report, args)

    if args.locale:
        localisations = payload.get("localizations")
        if isinstance(localisations, dict) and args.locale in localisations:
            payload = {"localizations": {args.locale: localisations[args.locale]}}

    return emit(analyse(payload, str(candidate)), args, title="Apple Native Engineer — App Store Optimization")


if __name__ == "__main__":
    raise SystemExit(main())
