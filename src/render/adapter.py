"""Bind a career graph to a view DTO for existing Jinja templates."""

from __future__ import annotations

from typing import Any, Optional

from src.graph.loader import CareerGraph
from src.graph.schema import (
    Award,
    Certificate,
    Claim,
    Company,
    Education,
    Focus,
    Person,
    Publication,
    Role,
    Skill,
    SkillGroup,
)
from src.render.editorial import validate_bullet
from src.render.views import CareerView, ClaimView, EducationView


# The graph also contains conceptual skills (for example, Distributed Systems).
# Keep this list to concrete technologies so the heuristic does not reject a
# legitimate system-first opening merely because it resembles a skill title.
_TOOL_SKILL_IDS = frozenset(
    {
        "ai-gateway",
        "aws",
        "ci-cd-azure-devops",
        "databricks",
        "docker",
        "fastapi",
        "googleadk",
        "guardrails",
        "kubernetes",
        "langgraph",
        "mlflow",
        "postgres",
        "python-expert",
        "redis",
        "sql",
    }
)


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


def _editorial(en: str, ja: str, locale: str, fallback: str) -> str:
    """Use a view rewrite for its locale, otherwise preserve canonical text."""

    if locale != "en" and ja.strip():
        return ja.strip()
    if locale == "en" and en.strip():
        return en.strip()
    return fallback


def _claim_ids(item: str | ClaimView) -> list[str]:
    claim_ids = item.claim_ids if isinstance(item, ClaimView) else [item]
    if len(claim_ids) != len(set(claim_ids)):
        raise ValueError("a bullet cannot cite the same claim more than once")
    return claim_ids


def _bullet_text(item: str | ClaimView, claims: list[Claim], locale: str) -> str:
    """Resolve one rendered bullet from one or more validated source claims."""

    primary = claims[0]
    if not isinstance(item, ClaimView):
        return _claim_text(primary, locale)

    if len(claims) > 1:
        rewrite = item.text if locale == "en" else item.text_ja
        if not rewrite.strip():
            raise ValueError(
                f"multi-claim bullet {item.id} requires an editorial rewrite for locale {locale}"
            )
        return rewrite.strip()
    return _editorial(item.text, item.text_ja, locale, _claim_text(primary, locale))


def bind_view(graph: CareerGraph, view: CareerView) -> dict[str, Any]:
    """Return the template context historically produced from YAML."""

    locale = view.locale
    skill_titles = [
        node.title
        for node in graph.of_type("skill")
        if isinstance(node, Skill) and node.id in _TOOL_SKILL_IDS
    ]
    person = graph.get(view.person)
    if not isinstance(person, Person):
        raise ValueError(f"{view.person} is not a person node")

    work: list[dict[str, Any]] = []
    for role_view in view.roles:
        role = graph.get(role_view.id)
        if not isinstance(role, Role):
            raise ValueError(f"{role_view.id} is not a role node")
        if role.person != person.id:
            raise ValueError(
                f"view {view.id} cannot attach role {role.id} to person {person.id}"
            )
        company = graph.get(role.company)
        if not isinstance(company, Company):
            raise ValueError(f"{role.company} is not a company node")
        role_foci = {
            focus.id
            for focus in graph.of_type("focus")
            if isinstance(focus, Focus) and focus.role == role.id
        }
        highlights: list[str] = []
        axes: list[Optional[str]] = []
        highlight_claim_ids: list[list[str]] = []
        for claim_view in role_view.claims:
            claim_ids = _claim_ids(claim_view)
            claims = [
                _require_claim(graph, claim_id, view=view.id) for claim_id in claim_ids
            ]
            for claim in claims:
                if claim.focus not in role_foci:
                    raise ValueError(
                        f"view {view.id} cannot attach claim {claim.id} to role {role.id}"
                    )
            text = _bullet_text(claim_view, claims, locale)
            validate_bullet(
                text,
                standard=view.editorial_standard,
                locale=locale,
                skill_titles=skill_titles,
            )
            highlights.append(text)
            axes.append(view.axis.get(claim_ids[0]))
            highlight_claim_ids.append(claim_ids)
        if role_view.include_awards:
            for award_id in role.awards:
                award = graph.get(award_id)
                title = _localized(award, "title", locale)
                highlights.append(title)
                axes.append(None)
                highlight_claim_ids.append([])
        evidence = [
            _claim_text(_require_claim(graph, claim_id, view=view.id, allow_internal=True), locale)
            for claim_id in role_view.evidence
        ]
        work.append(
            {
                "name": _localized(company, "title", locale),
                "position": _editorial(
                    role_view.title,
                    role_view.title_ja,
                    locale,
                    _localized(role, "title", locale),
                ),
                "startDate": role.start,
                "endDate": role.end,
                "location": _localized(role, "location", locale),
                "summary": (
                    _editorial(
                        role_view.summary,
                        role_view.summary_ja,
                        locale,
                        _localized(role, "summary", locale),
                    )
                    if role_view.include_summary
                    else ""
                ),
                "highlights": highlights,
                "evidence": evidence,
                "highlight_axes": axes,
                "highlight_claim_ids": highlight_claim_ids,
            }
        )

    projects: list[dict[str, Any]] = []
    for project_view in view.projects:
        focus = graph.get(project_view.id)
        if not isinstance(focus, Focus):
            raise ValueError(f"{project_view.id} is not a focus node")
        project_role = graph.get(focus.role)
        if not isinstance(project_role, Role):
            raise ValueError(f"{focus.role} is not a role node")
        if project_role.person != person.id:
            raise ValueError(
                f"view {view.id} cannot attach project {focus.id} to person {person.id}"
            )
        project_company = graph.get(project_role.company)
        if not isinstance(project_company, Company):
            raise ValueError(f"{project_role.company} is not a company node")
        project_claims: list[str] = []
        project_claim_ids: list[list[str]] = []
        for claim_view in project_view.claims:
            claim_ids = _claim_ids(claim_view)
            claims = [
                _require_claim(graph, claim_id, view=view.id) for claim_id in claim_ids
            ]
            for claim in claims:
                if claim.focus != focus.id:
                    raise ValueError(
                        f"view {view.id} cannot attach claim {claim.id} to project {focus.id}"
                    )
            text = _bullet_text(claim_view, claims, locale)
            validate_bullet(
                text,
                standard=view.editorial_standard,
                locale=locale,
                skill_titles=skill_titles,
            )
            project_claims.append(text)
            project_claim_ids.append(claim_ids)
        projects.append(
            {
                "name": _localized(focus, "title", locale),
                "company": _localized(project_company, "title", locale),
                "role": _localized(project_role, "title", locale),
                "description": _localized(focus, "problem", locale),
                "url": "",
                "startDate": focus.start,
                "endDate": focus.end,
                "ownership": focus.ownership,
                "release": focus.release,
                "keywords": [_skill_title(graph, skill_id) for skill_id in focus.stack],
                "highlights": project_claims,
                "highlight_claim_ids": project_claim_ids,
                "evidence": [],
            }
        )

    skills = []
    if view.skill_rows:
        for row in view.skill_rows:
            keywords = []
            for skill_id in row.skills:
                skill = graph.get(skill_id)
                if not isinstance(skill, Skill):
                    raise ValueError(f"{skill_id} is not a skill node")
                keywords.append(_localized(skill, "title", locale))
            skills.append(
                {
                    "name": row.title_ja if locale != "en" and row.title_ja else row.title,
                    "keywords": keywords,
                }
            )
    else:
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
    for education_view in view.education:
        if isinstance(education_view, EducationView):
            edu_id = education_view.id
            include_score = education_view.include_score
        else:
            edu_id = education_view
            include_score = True
        node = graph.get(edu_id)
        if not isinstance(node, Education):
            raise ValueError(f"{edu_id} is not an education node")
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
                "score": getattr(node, "score", "") if include_score else "",
                "courses": [],
                "highlights": highlights,
            }
        )

    certificates = []
    for cert_id in view.certificates:
        node = graph.get(cert_id)
        if not isinstance(node, Certificate):
            raise ValueError(f"{cert_id} is not a certificate node")
        certificates.append(
            {
                "name": _localized(node, "title", locale),
                "issuer": getattr(node, "issuer", ""),
                "date": getattr(node, "date", ""),
            }
        )

    awards = []
    for award_id in view.awards:
        node = graph.get(award_id)
        if not isinstance(node, Award):
            raise ValueError(f"{award_id} is not an award node")
        awards.append(
            {
                "name": _localized(node, "title", locale),
                "date": node.date,
            }
        )

    publications = []
    for pub_id in view.publications:
        node = graph.get(pub_id)
        if not isinstance(node, Publication):
            raise ValueError(f"{pub_id} is not a publication node")
        publications.append(
            {
                "name": _localized(node, "title", locale),
                "publisher": getattr(node, "publisher", ""),
                "releaseDate": getattr(node, "released", ""),
                "url": getattr(node, "url", ""),
                "summary": getattr(node, "summary", ""),
            }
        )

    contacts: list[dict[str, str]] = []
    if view.contact.email and person.email:
        contacts.append({"label": person.email, "url": "", "kind": "email"})
    if view.contact.phone and person.phone:
        contacts.append({"label": person.phone, "url": "", "kind": "phone"})
    if view.contact.location and person.city:
        location = _localized(person, "city", locale)
        region = _localized(person, "region", locale)
        if region:
            location = f"{location}, {region}" if locale == "en" else f"{location}、{region}"
        contacts.append({"label": location, "url": "", "kind": "location"})
    profiles_by_network = {
        profile.get("network", ""): profile for profile in person.profiles
    }
    for network in view.contact.profiles:
        profile = profiles_by_network.get(network)
        if not profile or not profile.get("url"):
            raise ValueError(f"profile {network!r} is unavailable for view {view.id}")
        label = profile["url"]
        for prefix in ("https://www.", "http://www.", "https://", "http://"):
            if label.startswith(prefix):
                label = label[len(prefix):]
                break
        label = label.rstrip("/")
        contacts.append(
            {"label": label, "url": profile["url"], "kind": "profile"}
        )

    return {
        "basics": {
            "name": _localized(person, "title", locale),
            "label": _editorial(
                view.headline,
                view.headline_ja,
                locale,
                _localized(person, "label", locale),
            ),
            "image": person.image,
            "email": person.email,
            "phone": person.phone,
            "url": person.url,
            "summary": _editorial(
                view.summary,
                view.summary_ja,
                locale,
                _localized(person, "summary", locale),
            ),
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
        "awards": awards,
        "publications": publications,
        "skills": skills,
        "projects": projects,
        "contacts": contacts,
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
    if node.status in {"interview-needed", "do-not-claim"}:
        raise ValueError(f"view {view} cannot select {node.status} claim {claim_id}")
    return node


__all__ = ["bind_view"]
