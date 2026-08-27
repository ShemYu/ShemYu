"""Bind a career graph to a view DTO for existing Jinja templates."""

from __future__ import annotations

from typing import Any, Optional

from src.graph.loader import CareerGraph
from src.graph.schema import Claim, Focus, Person, Role, SkillGroup
from src.render.views import CareerView


def _localized(node: Any, field: str, locale: str, fallback: str = "") -> str:
    if locale != "en":
        ja = getattr(node, f"{field}_ja", None)
        if ja:
            return ja
    value = getattr(node, field, None)
    return value if value else fallback


def _claim_text(claim: Claim, locale: str) -> str:
    if locale != "en" and claim.text.ja:
        return claim.text.ja
    return claim.text.en


def bind_view(graph: CareerGraph, view: CareerView) -> dict[str, Any]:
    """Return the template context historically produced from YAML."""

    locale = view.locale
    person = graph.get(view.person)
    if not isinstance(person, Person):
        raise ValueError(f"{view.person} is not a person node")

    work: list[dict[str, Any]] = []
    for role_view in view.roles:
        role = graph.get(role_view.id)
        if not isinstance(role, Role):
            raise ValueError(f"{role_view.id} is not a role node")
        company = graph.get(role.company)
        highlights: list[str] = []
        axes: list[Optional[str]] = []
        for claim_id in role_view.claims:
            claim = _require_claim(graph, claim_id, view=view.id)
            highlights.append(_claim_text(claim, locale))
            axes.append(view.axis.get(claim_id))
        if role_view.include_awards:
            for award_id in role.awards:
                award = graph.get(award_id)
                title = _localized(award, "title", locale)
                highlights.append(title)
                axes.append(None)
        evidence = [
            _claim_text(_require_claim(graph, claim_id, view=view.id, allow_internal=True), locale)
            for claim_id in role_view.evidence
        ]
        work.append(
            {
                "name": _localized(company, "title", locale),
                "position": _localized(role, "title", locale),
                "startDate": role.start,
                "endDate": role.end,
                "location": _localized(role, "location", locale),
                "summary": _localized(role, "summary", locale),
                "highlights": highlights,
                "evidence": evidence,
                "highlight_axes": axes,
            }
        )

    projects: list[dict[str, Any]] = []
    for project_view in view.projects:
        focus = graph.get(project_view.id)
        if not isinstance(focus, Focus):
            raise ValueError(f"{project_view.id} is not a focus node")
        projects.append(
            {
                "name": _localized(focus, "title", locale),
                "description": _localized(focus, "problem", locale),
                "url": "",
                "startDate": focus.start,
                "endDate": focus.end,
                "keywords": [_skill_title(graph, skill_id) for skill_id in focus.stack],
                "highlights": [
                    _claim_text(_require_claim(graph, claim_id, view=view.id), locale)
                    for claim_id in project_view.claims
                ],
                "evidence": [],
            }
        )

    skills = []
    for group_id in view.skill_groups:
        group = graph.get(group_id)
        if not isinstance(group, SkillGroup):
            raise ValueError(f"{group_id} is not a skill-group node")
        skills.append(
            {
                "name": _localized(group, "title", locale),
                "keywords": [_skill_title(graph, skill_id) for skill_id in group.skills],
            }
        )

    education = []
    for edu_id in view.education:
        node = graph.get(edu_id)
        highlights = []
        for claim_id in getattr(node, "claims", []) or []:
            highlights.append(
                _claim_text(_require_claim(graph, claim_id, view=view.id), locale)
            )
        education.append(
            {
                "institution": getattr(node, "institution", ""),
                "area": _localized(node, "area", locale) if hasattr(node, "area_ja") else getattr(node, "area", ""),
                "studyType": _localized(node, "study_type", locale) if hasattr(node, "study_type_ja") else getattr(node, "study_type", ""),
                "startDate": getattr(node, "start", ""),
                "endDate": getattr(node, "end", ""),
                "score": getattr(node, "score", ""),
                "courses": [],
                "highlights": highlights,
            }
        )

    certificates = []
    for cert_id in view.certificates:
        node = graph.get(cert_id)
        certificates.append(
            {
                "name": _localized(node, "title", locale),
                "issuer": getattr(node, "issuer", ""),
                "date": getattr(node, "date", ""),
            }
        )

    publications = []
    for pub_id in view.publications:
        node = graph.get(pub_id)
        publications.append(
            {
                "name": _localized(node, "title", locale),
                "publisher": getattr(node, "publisher", ""),
                "releaseDate": getattr(node, "released", ""),
                "url": getattr(node, "url", ""),
                "summary": getattr(node, "summary", ""),
            }
        )

    return {
        "basics": {
            "name": _localized(person, "title", locale),
            "label": _localized(person, "label", locale),
            "image": person.image,
            "email": person.email,
            "phone": person.phone,
            "url": person.url,
            "summary": _localized(person, "summary", locale),
            "location": {
                "address": "",
                "postalCode": "",
                "city": _localized(person, "city", locale),
                "countryCode": person.country_code,
                "region": _localized(person, "region", locale),
            },
            "profiles": list(person.profiles),
        },
        "work": work,
        "education": education,
        "certificates": certificates,
        "publications": publications,
        "skills": skills,
        "projects": projects,
    }


def _skill_title(graph: CareerGraph, skill_id: str) -> str:
    return graph.get(skill_id).title


def _require_claim(
    graph: CareerGraph,
    claim_id: str,
    *,
    view: str,
    allow_internal: bool = False,
) -> Claim:
    node = graph.get(claim_id)
    if not isinstance(node, Claim):
        raise ValueError(f"{claim_id} is not a claim")
    if node.disclosure == "secret":
        raise ValueError(f"view {view} cannot select secret claim {claim_id}")
    if node.disclosure != "public" and not allow_internal:
        raise ValueError(f"view {view} cannot select {node.disclosure} claim {claim_id}")
    return node


__all__ = ["bind_view"]
