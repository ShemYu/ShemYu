"""Hard-fail grounding for composed resume bullets.

The old tailor only copied highlight indices so the page could not invent
facts. Compose is allowed to rewrite, so this checker is the replacement
guarantee: every number and proper noun must already appear in that role's
publishable source, and tagged internal / invented claims must not leak.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any
import re


# Constraint evidence is the archive of what must not be published or invented.
_UNPUBLISHED_LINE = re.compile(
    r"not outbound|evidence only|do not claim|do not invent|do not write|"
    r"do not put|do not name|do not use",
    re.IGNORECASE,
)
_DO_NOT_PREFIX = re.compile(r"^\s*\[do not", re.IGNORECASE)

# Latin numbers and percent forms used on this resume.
_NUMBER = re.compile(
    r"(?<![A-Za-z])(?:\d+(?:\.\d+)?%|\d+\.\d+|\d+\+|\d+)(?![A-Za-z])"
)

# Title-case / CamelCase spans and all-caps product acronyms (F1, AWS, QPS).
_PROPER_SPAN = re.compile(
    r"\b(?:[A-Z][a-zA-Z0-9]+(?:[ -][A-Z][a-zA-Z0-9]+)*)\b"
)
_ACRONYM = re.compile(r"\b[A-Z]{2,}[A-Z0-9]*\b|\bF1\b")

# Sentence-initial verbs and generic English that are not product names.
_NAME_STOP = frozenset(
    {
        "A",
        "After",
        "All",
        "An",
        "And",
        "Architected",
        "Assisted",
        "Built",
        "Capability",
        "Coordinated",
        "Coverage",
        "Created",
        "Decoupled",
        "Delivered",
        "Designed",
        "Developed",
        "Do",
        "Extracted",
        "Facilitated",
        "For",
        "From",
        "I",
        "Implemented",
        "Improved",
        "In",
        "Integrated",
        "Internal",
        "Isolated",
        "Iterated",
        "Led",
        "Maintained",
        "Mapped",
        "Max",
        "My",
        "Named",
        "Not",
        "Operated",
        "Or",
        "Our",
        "Owned",
        "Per",
        "Previous",
        "Prior",
        "Public",
        "Raised",
        "Reduced",
        "Regulatory",
        "Role",
        "Same",
        "Selected",
        "Solutions",
        "Stored",
        "Supported",
        "The",
        "This",
        "That",
        "Using",
        "User",
        "With",
        "Won",
    }
)

# Product / metric names that models commonly invent for this profile.
INVENTED_PRODUCTS = (
    "Unity Catalog",
    "Delta Lake",
    "LiteLLM",
    "TypeScript",
    "English Professional",
)
INVENTED_PRODUCT_PATTERNS = (
    re.compile(r"\bUnity Catalog\b", re.IGNORECASE),
    re.compile(r"\bDelta(?:\s+Lake)?\b"),
    re.compile(r"\b(?:Apache\s+)?Spark\b"),
    re.compile(r"\bQPS\b"),
    re.compile(r"\b\d+\s*TB\b|\bTB-scale\b|\bterabytes?\b", re.IGNORECASE),
    re.compile(r"\bLiteLLM\b", re.IGNORECASE),
    re.compile(r"\bTypeScript\b", re.IGNORECASE),
    re.compile(r"\bEnglish Professional\b", re.IGNORECASE),
    re.compile(r"\b7 years\b", re.IGNORECASE),
)

# Internal Cookpad / DOGI launch numbers that must never reach the page.
UNPUBLISHED_TOKENS = (
    "67.6",
    "83.0",
    "15.4 pp",
    "15-case",
    "103-unit",
    "56-case",
    "flaky",
    "Moment team",
    "20 users",
    "20 active users",
    "chef-grounded",
    "10 cross-functional",
)

_CAUSAL = re.compile(
    r"led to|leading to|resulting in|which caused|thereby|therefore|"
    r"because of|thanks to|drove adoption|caused adoption|as a result|"
    r"により採用|の結果.*採用|につなが|おかげで|を受けて採用",
    re.IGNORECASE,
)
_F1 = re.compile(r"\bF1\b|0\.67|0\.89")
_ADOPTION = re.compile(r"adopted|adoption|採用")
_POC_OWNERSHIP = re.compile(
    r"(?:\bI\b|\bShem\b)\s+(?:built|developed|created|wrote)\s+"
    r"(?:the\s+)?(?:DS[-\s])?PoC"
    r"|(?:built|developed)\s+the\s+(?:Cathay\s+)?(?:DS\s+)?PoC",
    re.IGNORECASE,
)
_DS_BUILT_POC = re.compile(r"\bDS\b.{0,24}built.{0,12}PoC", re.IGNORECASE)


@dataclass(frozen=True)
class GroundingError:
    code: str
    message: str
    role: str
    bullet: str


@dataclass(frozen=True)
class RoleSource:
    name: str
    publishable: str
    archive: str


def is_constraint_evidence(line: str) -> bool:
    """Return True when an evidence line is a do-not-publish / do-not-invent note."""

    text = str(line).strip()
    if not text:
        return False
    if _DO_NOT_PREFIX.search(text):
        return True
    return bool(_UNPUBLISHED_LINE.search(text))


def role_source(item: Mapping[str, Any]) -> RoleSource:
    """Split a work/project item into publishable text vs the full archive."""

    highlights = [str(part) for part in item.get("highlights") or [] if part]
    evidence = [str(part) for part in item.get("evidence") or [] if part]
    publishable_evidence = [line for line in evidence if not is_constraint_evidence(line)]
    extras = [
        str(item.get("name") or ""),
        str(item.get("position") or ""),
        str(item.get("summary") or ""),
        str(item.get("description") or ""),
        str(item.get("location") or ""),
    ]
    extras = [part for part in extras if part]
    publishable = "\n".join([*extras, *highlights, *publishable_evidence])
    archive = "\n".join([*extras, *highlights, *evidence])
    return RoleSource(
        name=str(item.get("name") or ""),
        publishable=publishable,
        archive=archive,
    )


def extract_numbers(text: str) -> list[str]:
    return _NUMBER.findall(text or "")


def extract_proper_nouns(text: str) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()
    for match in (*_PROPER_SPAN.findall(text or ""), *_ACRONYM.findall(text or "")):
        token = match.strip()
        if not token or token in _NAME_STOP:
            continue
        key = token.lower()
        if key in seen:
            continue
        seen.add(key)
        found.append(token)
    return found


def _contains_token(haystack: str, token: str) -> bool:
    if not token:
        return False
    if token in haystack:
        return True
    # Allow "40%" to match a source that only writes "40" next to a percent sign
    # in a different Unicode form, and "30+" to match "30+".
    stripped = token.rstrip("%+").strip()
    if stripped and stripped != token and stripped in haystack:
        return True
    return False


def _unpublished_in_bullet(bullet: str) -> list[str]:
    hits = []
    lower = bullet
    for token in UNPUBLISHED_TOKENS:
        if token.lower() in lower.lower() or token in bullet:
            hits.append(token)
    return hits


def _invented_products(bullet: str, publishable: str) -> list[str]:
    hits: list[str] = []
    for pattern in INVENTED_PRODUCT_PATTERNS:
        match = pattern.search(bullet)
        if not match:
            continue
        fragment = match.group(0)
        if not _contains_token(publishable, fragment):
            hits.append(fragment)
    for name in INVENTED_PRODUCTS:
        if re.search(re.escape(name), bullet, re.IGNORECASE) and not _contains_token(
            publishable, name
        ):
            if name not in hits:
                hits.append(name)
    return hits


def check_bullet(bullet: str, source: RoleSource) -> list[GroundingError]:
    """Return grounding failures for one composed bullet against one role."""

    errors: list[GroundingError] = []
    text = str(bullet or "").strip()
    if not text:
        errors.append(
            GroundingError(
                code="empty_bullet",
                message="composed bullet is empty",
                role=source.name,
                bullet=text,
            )
        )
        return errors

    for token in extract_numbers(text):
        if not _contains_token(source.publishable, token):
            errors.append(
                GroundingError(
                    code="ungrounded_number",
                    message=f"number {token!r} is not in the role's publishable source",
                    role=source.name,
                    bullet=text,
                )
            )

    for name in extract_proper_nouns(text):
        if not _contains_token(source.publishable, name):
            errors.append(
                GroundingError(
                    code="ungrounded_name",
                    message=f"proper name {name!r} is not in the role's publishable source",
                    role=source.name,
                    bullet=text,
                )
            )

    for token in _unpublished_in_bullet(text):
        errors.append(
            GroundingError(
                code="unpublished_token",
                message=f"internal or do-not-claim token {token!r} must not appear on the page",
                role=source.name,
                bullet=text,
            )
        )

    for product in _invented_products(text, source.publishable):
        errors.append(
            GroundingError(
                code="invented_product",
                message=f"invented product or layer name {product!r}",
                role=source.name,
                bullet=text,
            )
        )

    if _F1.search(text) and _ADOPTION.search(text) and _CAUSAL.search(text):
        errors.append(
            GroundingError(
                code="invented_causality",
                message="do not invent causality between F1 and RKB adoption",
                role=source.name,
                bullet=text,
            )
        )

    if _POC_OWNERSHIP.search(text) and not _DS_BUILT_POC.search(text):
        errors.append(
            GroundingError(
                code="invented_claim",
                message="do not write that Shem built the Cathay DS PoC",
                role=source.name,
                bullet=text,
            )
        )

    return errors


def check_role_bullets(
    item: Mapping[str, Any], bullets: Sequence[str]
) -> list[GroundingError]:
    source = role_source(item)
    errors: list[GroundingError] = []
    if len(bullets) > 3:
        errors.append(
            GroundingError(
                code="too_many_bullets",
                message=f"{source.name}: composed more than 3 bullets",
                role=source.name,
                bullet="",
            )
        )
    for bullet in bullets:
        errors.extend(check_bullet(str(bullet), source))
    return errors


def check_profile(source: Mapping[str, Any], tailored: Mapping[str, Any]) -> list[GroundingError]:
    """Ground each tailored work/project highlight against its source item."""

    errors: list[GroundingError] = []
    for section in ("work", "projects"):
        source_by_name = {
            item.get("name"): item for item in source.get(section) or [] if item.get("name")
        }
        for item in tailored.get(section) or []:
            name = item.get("name")
            source_item = source_by_name.get(name)
            if source_item is None:
                errors.append(
                    GroundingError(
                        code="unknown_role",
                        message=f"{section} identity {name!r} is not in the source profile",
                        role=str(name or ""),
                        bullet="",
                    )
                )
                continue
            errors.extend(check_role_bullets(source_item, list(item.get("highlights") or [])))
    return errors


class GroundingErrorList(ValueError):
    """Raised when composed output fails the hard grounding check."""

    def __init__(self, errors: Sequence[GroundingError]):
        self.errors = list(errors)
        details = "; ".join(f"{item.code}: {item.message}" for item in self.errors)
        super().__init__(f"Grounding check failed ({len(self.errors)}): {details}")


def assert_grounded(source: Mapping[str, Any], tailored: Mapping[str, Any]) -> None:
    """Hard-fail a tailor run when composed bullets are not grounded."""

    errors = check_profile(source, tailored)
    if errors:
        raise GroundingErrorList(errors)


__all__ = [
    "GroundingError",
    "GroundingErrorList",
    "INVENTED_PRODUCTS",
    "RoleSource",
    "UNPUBLISHED_TOKENS",
    "assert_grounded",
    "check_bullet",
    "check_profile",
    "check_role_bullets",
    "extract_numbers",
    "extract_proper_nouns",
    "is_constraint_evidence",
    "role_source",
]
