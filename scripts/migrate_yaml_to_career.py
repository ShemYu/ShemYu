"""One-shot export of data/*.yaml into career/*.md. Do not invent facts."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CAREER = ROOT / "career"


def slugify(text: str) -> str:
    value = text.lower().replace("+", "-plus-").replace("/", "-")
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def dump_page(directory: str, node: dict, body: str = "") -> None:
    path = CAREER / directory / f"{node['id']}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    # Keep key order stable for diffs.
    dumped = yaml.safe_dump(node, sort_keys=False, allow_unicode=True, width=88)
    path.write_text(f"---\n{dumped}---\n\n{body.rstrip()}\n", encoding="utf-8")


def load_yaml(path: Path) -> dict:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"{path} must be a mapping")
    return value


def disclosure_for_layer(layer: str) -> str:
    if layer in {"public", "bible"}:
        return "public"
    return "internal"


def claim_title(text: str) -> str:
    compact = " ".join(text.split())
    if len(compact) <= 72:
        return compact
    return compact[:69].rstrip() + "..."


def skill_pages(titles: list[str]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for title in titles:
        skill_id = slugify(title)
        mapping[title] = skill_id
        dump_page("skills", {"id": skill_id, "type": "skill", "title": title, "disclosure": "public"})
    return mapping


def main() -> None:
    CAREER.mkdir(exist_ok=True)
    skill_titles: list[str] = []

    # --- person ---
    basics = load_yaml(DATA / "basics.yaml")
    dump_page(
        "people",
        {
            "id": "shem",
            "type": "person",
            "title": basics["name"],
            "title_ja": "余顯漁（Shem Yu）",
            "label": basics.get("label", ""),
            "label_ja": "シニアAIエンジニア @ Cookpad｜GenAI、AIエージェント、MLOps｜東京",
            "image": basics.get("image", ""),
            "email": basics.get("email", ""),
            "phone": basics.get("phone", ""),
            "url": basics.get("url", ""),
            "summary": basics.get("summary", "").strip(),
            "summary_ja": (
                "本番環境のエージェント、RAG基盤、共有GenAIインフラの構築に6年従事してきた"
                "Applied AIエンジニア。現在はCookpadにて、エージェント評価・推論アーキテクチャ・"
                "信頼性を軸にマルチモーダルなコーチングエージェントを開発。以前は金融サービス領域で、"
                "本番GenAIシステムを届けるMLEチームをリード。"
            ),
            "city": basics.get("location", {}).get("city", ""),
            "city_ja": "台北",
            "region": basics.get("location", {}).get("region", ""),
            "region_ja": "台湾",
            "country_code": basics.get("location", {}).get("countryCode", ""),
            "profiles": basics.get("profiles", []),
        },
        "Person node for Shem Yu. Contact and positioning live here; work lives on [[roles]].",
    )

    companies = {
        "Cookpad": ("cookpad", "Cookpad（クックパッド）"),
        "Cathay Financial Holdings": ("cathay-financial-holdings", "Cathay Financial Holdings"),
        "Wisers Information Limited": ("wisers-information-limited", "Wisers Information Limited"),
        "TripSaaS": ("tripsaas", "TripSaaS"),
        "Ming Chuan University - data science Lab.": ("ming-chuan-university", "銘傳大学"),
        "Institute for Information Industry, III": ("institute-for-information-industry", "III"),
        "Ming Chuan University": ("ming-chuan-university", "銘傳大学"),
    }
    for name, (company_id, title_ja) in companies.items():
        dump_page(
            "companies",
            {"id": company_id, "type": "company", "title": name.split(" - ")[0] if company_id == "ming-chuan-university" else name, "title_ja": title_ja},
        )

    # Fix MCU company title
    dump_page(
        "companies",
        {
            "id": "ming-chuan-university",
            "type": "company",
            "title": "Ming Chuan University",
            "title_ja": "銘傳大学",
        },
    )

    role_map = {
        "cookpad": "cookpad-senior-ai",
        "cathay": "cathay-mle-lead",
        "wisers": "wisers-platform-engineer",
        "tripsaas": "tripsaas-data-scientist",
        "mcu": "mcu-research-assistant",
        "iii": "iii-intern",
    }
    role_ja = {
        "Senior AI Engineer": "シニアAIエンジニア",
        "Machine Learning Engineer, team lead": "機械学習エンジニア、チームリード",
        "Senior AI Platform Engineer": "シニアAIプラットフォームエンジニア",
        "Data Scientist": "データサイエンティスト",
        "Research assistant": "リサーチアシスタント",
        "Intern": "インターン",
    }
    location_ja = {"Tokyo, Japan": "東京", "Taipei, Taiwan": "台北、台湾"}
    company_for_file = {
        "cookpad": "cookpad",
        "cathay": "cathay-financial-holdings",
        "wisers": "wisers-information-limited",
        "tripsaas": "tripsaas",
        "mcu": "ming-chuan-university",
        "iii": "institute-for-information-industry",
    }
    summary_ja = {
        "cookpad": "日常をより楽しくするAIを構築。",
        "cathay": "正社員4名（業務委託を含めると7名）をリードし、AIプロジェクトのデプロイと部門内エージェント開発を統括。",
        "wisers": "新旧プロジェクトを横断し、統一プラットフォームへの移行を可能にする、チーム横断のAIソリューション統合を支援。",
        "tripsaas": "ETLパイプラインとデータ収集の維持を支援し、変動する事業環境でも安定した分析を確保。",
        "mcu": "データベース理論のティーチングアシスタントとして授業運営を支援し、学部生を指導。",
        "iii": "大学とIIIチーム間のコミュニケーションとプロジェクト推進を支援し、成果物と期待のすり合わせを行う。",
    }

    extra_dogi_claim = {
        "id": "cathay-dogi-finops-agent",
        "layer": "public",
        "resume": False,
        "text": "Delivered FinOps agent for AWS cost insights and early anomaly detection.",
        "source": "legacy-project-yaml",
    }

    cookpad_wiki = """
Inputs: cooking video and learner voice. Infer where the learner is stuck; older wording was decide reteach, narrow, or advance so the next prompt targets that gap. Public architecture is the staged pipeline: observable facts → recipe-specific ingredient definitions → ingredient state → cooking issues.

## Eval history (one measurement story)

An earlier public sentence said Coverage 40% → 95% on a versioned eval set. That was a shorthand, not two competing truths. Source: `daily/history.json` (23 reports, always 15 cases).

- 2026-07-06: dish 30/74 = 40.5%. This is the reading behind the earlier 40%.
- Same-rubric 56-item window 2026-07-08 → 2026-07-27: 28/56 → 53/56 (50% → 94.6%). Owner locked the public sentence to 50% → 95% (53/56) because this is the same denominator. 53/56 is 94.6%; owner accepted writing 95% (53/56). So 40% and 95% were both real readings, but not the same ruler.
- Same-rubric series 2026-07-08 to 2026-08-04: dish_total 56. Peak dish 53/56 on 2026-07-27 and 2026-08-02. Knowledge peaked 38/48 = 79.2% on 2026-08-02. Knowledge coverage remains remaining work; do not put a knowledge number on a public view.
- Later, different ruler: after 2026-08-11 the set is 61 dish items; 2026-08-12 onward `v3_canonical_claim` (stricter). Latest 2026-08-19 is 23/61 dish / 27/48 knowledge. That is a different ruler, not a product regression and not an arrow from 53/56. Parent DR units later decomposed into VU / DU / LVO children (109-contract family); 2026-08-18 dish 19/61 is that later metric.

## Architecture journey

Name lock: Guideline grounder (not Guideline grounding, not Galactic Rounder). Propose / influence only — not a clean Shem-owned shipped lineage.

1. **Video Description v1** — very detailed Video Description, then agents to verify. Needed near-100% precision on the transcript-like description; even a small hallucination damages the rest. Cost is wall-clock: typical source videos about 20–50 minutes; processing about 30–45 minutes. That path did not succeed and is not a public highlight. No SLA, dollar cost, or GPU type recorded.
2. **Proposed split** — Shem proposed (not implemented / not shipped as current production): Recall-first Candidate Generator, and Debater Investigator for video grounding. Diagnosis: mixing recall and precision in one agent hurt performance. Proposed split: Recall first → Ranker → Precision via Investigator. Speech typos: Recode = Recall, Debezter = Debater. Do not write that production is currently this stack.
3. **Guideline grounder v1** — Shem only. No Sonan. Staged ground-then-assess: Detect → Plan → Select → Observe → Correct. Source: `20260424_feat_guideline-grounding-action.md` (#299). ~2–4s latency is not a win to write.
4. **Guideline grounder v2** — Collaboration with Sonan (do not invent title or ownership beyond this). ObservationAgent loop, skill-routed observation. Attempted / possibly not online — do not claim v2 is in production. Source: `20260608_feat_guideline-grounding-v2-observation-agent.md`.
5. **Influence on v5** — Guideline grounder design later influenced the final v5 investigator. Influence only. Do not write that Shem or Sonan implemented, shipped, or owned v5 investigator.
6. **Iteration** — Company iterations often unplanned-refactored the whole architecture. Shem's pieces mostly remained as concepts that later rewrites absorbed. After a version was replaced it was no longer online. Culture commentary stays off public views.
7. **Other systems** — Video embeddings + semantic search + Visual Explorer (internal tool). Shem PRs #213/#217/#220/#222/#202/#239. Gemini Embedding 2 migration to 3072-d with model-scoped cache; no retrieval-accuracy lift sourced. Same-dish / multi-video selection: Shem #606. Observed cooking audit: Shem 15b56449 (#666); contract incomplete, no metric.

Canonical hash-locked 15-case `make eval` pipeline + viewer; README example 77/103 (74.8%) is run-varying / unpublished. Assessment v5 + frozen-input LLM-as-judge suite + failure taxonomy stay unpublished unless a view explicitly selects an internal claim.
""".strip()

    for yaml_name, role_id in role_map.items():
        work = load_yaml(DATA / "work" / f"{yaml_name}.yaml")
        awards = []
        for award in work.get("awards") or []:
            award_id = slugify(award["name"])
            awards.append(award_id)
            dump_page(
                "awards",
                {
                    "id": award_id,
                    "type": "award",
                    "title": award["name"],
                    "title_ja": {
                        "Won CFH Cloud Creative Award 2024 (1st place).": "CFH Cloud Creative Award 2024（1位）を受賞。",
                        "Named departmental MVP, Q1 2025.": "2025年第1四半期、部門MVPに選出。",
                    }.get(award["name"], ""),
                    "role": role_id,
                    "date": award.get("date", ""),
                    "disclosure": "public",
                },
            )
        dump_page(
            "roles",
            {
                "id": role_id,
                "type": "role",
                "title": work["position"],
                "title_ja": role_ja.get(work["position"], ""),
                "person": "shem",
                "company": company_for_file[yaml_name],
                "start": str(work["startDate"]),
                "end": str(work.get("endDate") or ""),
                "location": work.get("location") or "",
                "location_ja": location_ja.get(work.get("location") or "", ""),
                "summary": work.get("summary") or "",
                "summary_ja": summary_ja.get(yaml_name, ""),
                "awards": awards,
                "disclosure": "public",
            },
        )
        foci = list(work.get("foci") or [])
        if yaml_name == "cathay":
            for focus in foci:
                if focus["id"] == "cathay-dogi":
                    ids = {claim["id"] for claim in focus["claims"]}
                    if extra_dogi_claim["id"] not in ids:
                        focus["claims"].append(extra_dogi_claim)
        for focus in foci:
            stack_ids = []
            for item in focus.get("stack") or []:
                skill_titles.append(item)
                stack_ids.append(slugify(item))
            claim_ids = []
            for claim in focus.get("claims") or []:
                claim_ids.append(claim["id"])
                metric_id = ""
                metric = claim.get("metric")
                if metric:
                    metric_id = claim["id"] + "-metric"
                    dump_page(
                        "metrics",
                        {
                            "id": metric_id,
                            "type": "metric",
                            "title": metric.get("display") or metric.get("name"),
                            "name": metric["name"],
                            "display": metric.get("display") or "",
                            "from": metric.get("from") or metric.get("from_value") or "",
                            "to": metric.get("to") or metric.get("to_value") or "",
                            "window": metric.get("window") or "",
                            "cohort": metric.get("cohort") or "",
                            "n_cases": metric.get("n_cases"),
                            "n_items": metric.get("n_items"),
                            "source": metric.get("source") or "",
                            "disclosure": disclosure_for_layer(claim.get("layer", "public")),
                        },
                    )
                text = claim["text"]
                dump_page(
                    "claims",
                    {
                        "id": claim["id"],
                        "type": "claim",
                        "title": claim_title(text),
                        "focus": focus["id"],
                        "status": "confirmed",
                        "disclosure": disclosure_for_layer(claim.get("layer", "public")),
                        "source": claim.get("source") or "",
                        "metric": metric_id,
                        "text": {"en": text, "ja": claim.get("text_ja") or ""},
                        "do_not_claim": claim.get("do_not_claim") or [],
                    },
                    body="",
                )
            dump_page(
                "foci",
                {
                    "id": focus["id"],
                    "type": "focus",
                    "title": focus["name"],
                    "kind": focus.get("kind", "product"),
                    "role": role_id,
                    "start": str(focus.get("startDate") or ""),
                    "end": str(focus.get("endDate") or ""),
                    "problem": focus.get("problem") or "",
                    "ownership": focus.get("ownership", "implemented"),
                    "release": focus.get("release", "production"),
                    "stack": stack_ids,
                    "claims": claim_ids,
                    "do_not_claim": focus.get("do_not_claim") or [],
                    "disclosure": "public",
                },
                body=cookpad_wiki if focus["id"] == "cookpad-vu" else (focus.get("problem") or ""),
            )

    # Education
    master = load_yaml(DATA / "education" / "master.yaml")
    bachelor = load_yaml(DATA / "education" / "bachelor.yaml")
    edu_claim_ids = []
    for index, line in enumerate(master.get("highlights") or [], start=1):
        claim_id = f"mcu-master-h{index}"
        edu_claim_ids.append(claim_id)
        dump_page(
            "claims",
            {
                "id": claim_id,
                "type": "claim",
                "title": claim_title(line),
                "focus": "mcu-lab",
                "status": "confirmed",
                "disclosure": "public",
                "text": {
                    "en": line,
                    "ja": "",
                },
            },
        )
    dump_page(
        "education",
        {
            "id": "mcu-master",
            "type": "education",
            "title": "Master in Computer Science & Information Engineering",
            "institution": master["institution"],
            "institution_id": "ming-chuan-university",
            "area": master["area"],
            "area_ja": "コンピュータサイエンス・情報工学",
            "study_type": master["studyType"],
            "study_type_ja": "修士",
            "start": str(master["startDate"]),
            "end": str(master["endDate"]),
            "score": master.get("score") or "",
            "claims": edu_claim_ids,
            "disclosure": "public",
        },
        "Graduate work at the data science lab. Thesis and presentation claims are linked.",
    )
    dump_page(
        "education",
        {
            "id": "mcu-bachelor",
            "type": "education",
            "title": "Bachelor in Computer Science & Information Engineering",
            "institution": bachelor["institution"],
            "institution_id": "ming-chuan-university",
            "area": bachelor["area"],
            "area_ja": "コンピュータサイエンス・情報工学",
            "study_type": bachelor["studyType"],
            "study_type_ja": "学士",
            "start": str(bachelor["startDate"]),
            "end": str(bachelor["endDate"]),
            "score": bachelor.get("score") or "",
            "claims": [],
            "disclosure": "public",
        },
        "No additional highlights recorded. Interview if coursework or awards should be captured.",
    )

    # Certificates
    for filename, cert_id in [
        ("aws_cloud_practitioner.yaml", "aws-certified-cloud-practitioner"),
        ("aws_cloud_quest.yaml", "aws-cloud-quest-cloud-practitioner"),
        ("aws_mls.yaml", "aws-certified-machine-learning-specialty"),
    ]:
        cert = load_yaml(DATA / "certificates" / filename)
        dump_page(
            "certificates",
            {
                "id": cert_id,
                "type": "certificate",
                "title": cert["name"],
                "issuer": cert.get("issuer") or "",
                "date": str(cert.get("date") or ""),
                "disclosure": "public",
            },
        )

    # Publications
    for filename, pub_id in [
        ("ai_agent.yaml", "publication-ai-agent-architecture"),
        ("podman.yaml", "publication-podman"),
    ]:
        pub = load_yaml(DATA / "publications" / filename)
        dump_page(
            "publications",
            {
                "id": pub_id,
                "type": "publication",
                "title": pub["name"],
                "publisher": pub.get("publisher") or "",
                "released": str(pub.get("releaseDate") or ""),
                "url": pub.get("url") or "",
                "summary": pub.get("summary") or "",
                "disclosure": "public",
            },
        )

    # Skill groups from YAML
    group_files = {
        "cloud_infra.yaml": "skill-group-cloud-infra",
        "data_engineering.yaml": "skill-group-data-engineering",
        "genai_nlp.yaml": "skill-group-genai-nlp",
        "language.yaml": "skill-group-language",
        "leadership.yaml": "skill-group-leadership",
        "mlops.yaml": "skill-group-mlops",
        "programming.yaml": "skill-group-programming",
    }
    group_ja = {
        "Cloud & Infra": "クラウド / インフラ",
        "Data Engineering": "データエンジニアリング",
        "Generative AI & NLP": "生成AI / NLP",
        "Language": "語学",
        "Leadership & Communication": "リーダーシップ / コミュニケーション",
        "MLOps & Deployment": "MLOps / デプロイ",
        "Programming & ML Frameworks": "プログラミング / MLフレームワーク",
    }
    for filename, group_id in group_files.items():
        group = load_yaml(DATA / "skills" / filename)
        keywords = list(group.get("keywords") or [])
        skill_titles.extend(keywords)
        dump_page(
            "skill-groups",
            {
                "id": group_id,
                "type": "skill-group",
                "title": group["name"],
                "title_ja": group_ja.get(group["name"], ""),
                "skills": [slugify(item) for item in keywords],
                "disclosure": "public",
            },
        )

    skill_pages(skill_titles)
    print(f"wrote career pages under {CAREER}", file=sys.stderr)


if __name__ == "__main__":
    main()
