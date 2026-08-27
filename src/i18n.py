"""Local rendering helpers for tailored resumes.

The tailor composes English or Japanese bullets, then this module translates
remaining assembled strings. Exact source-string maps keep numbers and facts
unchanged. Unmapped composed sentences are left as written.

Display alias: the Chinese characters 「余顯漁」 are not stored in
``data/basics.yaml``. Japanese headers may show ``余顯漁（Shem Yu）`` as a
presentation-only alias of the YAML name ``Shem Yu``.
"""

from __future__ import annotations

import copy
import re
from datetime import date
from typing import Any, Mapping

SUPPORTED_LANGUAGES = ("en", "ja")
DEFAULT_LANGUAGE = "en"

# Presentation-only alias. Not a career fact and not written to basics.yaml.
JA_DISPLAY_NAME_ALIAS = "余顯漁（Shem Yu）"

UI_LABELS: dict[str, dict[str, str]] = {
    "en": {
        "doc_title": "Resume",
        "as_of_suffix": "",
        "summary": "Professional Summary",
        "skills": "Technical Skills",
        "languages": "Languages",
        "experience": "Professional Experience",
        "education": "Education",
        "certificates": "Certifications",
        "present": "Present",
        "in": " in ",
        "gpa": "GPA",
    },
    "ja": {
        "doc_title": "職務経歴書",
        "as_of_suffix": "現在",
        "summary": "職務要約",
        "skills": "活かせる経験・スキル",
        "languages": "語学",
        "experience": "職務経歴",
        "education": "学歴",
        "certificates": "資格",
        "present": "現在",
        "in": "（",
        "gpa": "GPA",
    },
}

# Exact source-string translations. Keys must match YAML / assembled profile
# values character-for-character. Do not add fluency, tools, or metrics that
# are not in the source string.
JA_STRINGS: dict[str, str] = {
    "Shem Yu": JA_DISPLAY_NAME_ALIAS,
    "Senior AI Engineer @ Cookpad | GenAI, AI Agents & MLOps | Tokyo": (
        "シニアAIエンジニア @ Cookpad｜GenAI、AIエージェント、MLOps｜東京"
    ),
    (
        "Applied AI engineer with 6 years building production agents, RAG platforms, "
        "and shared GenAI infrastructure. Now at Cookpad developing multimodal coaching "
        "agents, with a focus on agent evaluation, reasoning architecture, and reliability. "
        "Previously led an MLE team delivering production GenAI systems in financial services."
    ): (
        "本番環境のエージェント、RAG基盤、共有GenAIインフラの構築に6年従事してきた"
        "Applied AIエンジニア。現在はCookpadにて、エージェント評価・推論アーキテクチャ・"
        "信頼性を軸にマルチモーダルなコーチングエージェントを開発。以前は金融サービス領域で、"
        "本番GenAIシステムを届けるMLEチームをリード。"
    ),
    "Taipei": "台北",
    "Taiwan": "台湾",
    "Tokyo, Japan": "東京",
    "Taipei, Taiwan": "台北、台湾",
    "Senior AI Engineer": "シニアAIエンジニア",
    "Machine Learning Engineer, team lead": "機械学習エンジニア、チームリード",
    "Senior AI Platform Engineer": "シニアAIプラットフォームエンジニア",
    "Data Scientist": "データサイエンティスト",
    "Research assistant": "リサーチアシスタント",
    "Intern": "インターン",
    "Cookpad": "Cookpad（クックパッド）",
    "Building AI that makes everyday life more joyful.": "日常をより楽しくするAIを構築。",
    (
        "Built a multimodal coaching agent that reasons over cooking video and learner "
        "voice to decide whether to reteach, narrow, or advance; raised expert-grounded "
        "coverage from 40% to 95%."
    ): (
        "料理動画と学習者の音声を踏まえて再説明・絞り込み・先へ進むかを判断する"
        "マルチモーダル・コーチングエージェントを構築。"
        "エキスパート根拠のカバレッジを40%から95%へ向上。"
    ),
    (
        "Designed versioned, capability-based agent evaluations and automated scoring "
        "for coverage, truth, coherence, and per-turn quality."
    ): (
        "カバレッジ、真実性、一貫性、ターンごとの品質を対象に、バージョン管理された"
        "能力ベースのエージェント評価と自動スコアリングを設計。"
    ),
    (
        "Architected a staged multimodal reasoning pipeline separating observation, "
        "gap inference, and coaching decisions, improving debuggability and reducing "
        "failure propagation across agent stages."
    ): (
        "観察、ギャップ推論、コーチング判断を分離した段階的マルチモーダル推論"
        "パイプラインを設計し、デバッグ容易性を高め、エージェント各段階への障害伝播を抑制。"
    ),
    (
        "Built and iterated the video-understanding system as a staged pipeline: "
        "observable facts → recipe-specific ingredient definitions → ingredient "
        "state → cooking issues."
    ): (
        "観察可能な事実 → レシピ固有の材料定義 → 材料の状態 → 調理上の課題、という"
        "段階的パイプラインとして動画理解システムを構築し反復。"
    ),
    (
        "Coverage 40% → 95% on a versioned eval set; isolate failures to observation "
        "/ ingredient-state / issue-detection."
    ): (
        "バージョン管理された評価セットでカバレッジを40%から95%へ。"
        "失敗を観察 / 材料状態 / 課題検出に切り分ける。"
    ),
    (
        "Capability-based evals and automated scoring for observation accuracy, "
        "issue coverage, factuality, coherence, and turn-level coaching quality."
    ): (
        "観察精度、課題カバレッジ、事実性、一貫性、ターン単位のコーチング品質に対する"
        "能力ベース評価と自動スコアリング。"
    ),
    (
        "Led 4 full-time reports (7 including contractors), overseeing AI project "
        "deployment and departmental internal agent development."
    ): (
        "正社員4名（業務委託を含めると7名）をリードし、AIプロジェクトのデプロイと"
        "部門内エージェント開発を統括。"
    ),
    (
        "Led a 4-person MLE team, overseeing AI project deployment and departmental "
        "internal agent development."
    ): "4名のMLEチームをリードし、AIプロジェクトのデプロイと部門内エージェント開発を統括。",
    (
        "Improved regulatory Agent F1 from 0.67 to 0.89; adopted by 2 of 5 subsidiaries."
    ): "規制対応エージェントのF1を0.67から0.89へ改善。5社中2社で採用。",
    (
        "Developed Departmental Internal AI Agents with Google ADK, automating deep "
        "research tasks, reducing analysis time from 2 hours to 15 minutes."
    ): (
        "Google ADKで部門内AIエージェントを開発し、ディープリサーチ業務を自動化。"
        "分析時間を2時間から15分へ短縮。"
    ),
    (
        "Designed and built GenAI infrastructure (AI Gateway, Guardrails, MLflow), "
        "optimizing internal AI service latency by 60%."
    ): (
        "GenAIインフラ（AI Gateway、Guardrails、MLflow）を設計・構築し、"
        "社内AIサービスのレイテンシを60%改善。"
    ),
    "Implemented FinOps agent, achieving 30% GPU cost reduction.": (
        "FinOpsエージェントを実装し、GPUコストを30%削減。"
    ),
    "Reduced overall cloud spend by 40% through FinOps practices.": (
        "FinOpsの実践により、クラウド支出を全体で40%削減。"
    ),
    "Improved regulatory Agent F1 from 0.67 to 0.89.": (
        "規制対応エージェントのF1を0.67から0.89へ改善。"
    ),
    "Won CFH Cloud Creative Award 2024 (1st place).": (
        "CFH Cloud Creative Award 2024（1位）を受賞。"
    ),
    "Named departmental MVP, Q1 2025.": "2025年第1四半期、部門MVPに選出。",
    (
        "Solutions deployed using Databricks workflows and AWS infrastructure, "
        "ensuring scalable and secure operations."
    ): (
        "DatabricksワークフローとAWSインフラでソリューションをデプロイし、"
        "スケーラブルでセキュアな運用を確保。"
    ),
    (
        "Support cross-team AI solution integration, enabling seamless transition to "
        "unified platforms across new and legacy projects."
    ): (
        "新旧プロジェクトを横断し、統一プラットフォームへの移行を可能にする、"
        "チーム横断のAIソリューション統合を支援。"
    ),
    (
        "Develop standardized ML project templates (AI Cloud Platform template; "
        "FastAPI, CI/CD, Kubernetes), reducing deployment time from 2 weeks to 3 days, "
        "adopted by 30+ projects."
    ): (
        "標準MLプロジェクトテンプレート（AI Cloud Platformテンプレート：FastAPI、"
        "CI/CD、Kubernetes）を整備。デプロイ期間を2週間から3日へ短縮し、"
        "30+のプロジェクトで採用。"
    ),
    (
        "Implement NLP-focused Python library (UAP Common Library) with 70% internal "
        "adoption and 90%+ code coverage, improving productivity and reliability for "
        "AI developers."
    ): (
        "NLP向けPythonライブラリ（UAP Common Library）を実装。"
        "社内採用率70%、コードカバレッジ90%+で、AI開発者の生産性と信頼性を向上。"
    ),
    (
        "Lead automation of documentation pipelines via Sphinx and CI, enhancing "
        "onboarding efficiency and platform usability."
    ): (
        "SphinxとCIによるドキュメントパイプライン自動化を主導し、"
        "オンボーディング効率とプラットフォームの使いやすさを向上。"
    ),
    (
        "Assist in maintaining ETL pipelines and data collection, ensuring stable "
        "analytics during dynamic business environments."
    ): (
        "ETLパイプラインとデータ収集の維持を支援し、変動する事業環境でも安定した分析を確保。"
    ),
    (
        "Analyze customer order data using statistical modeling (FP-Growth, K-means, "
        "4 clusters) to support marketing and segmentation strategies."
    ): (
        "統計モデリング（FP-Growth、K-means、4クラスタ）で顧客注文データを分析し、"
        "マーケティングとセグメンテーションを支援。"
    ),
    (
        "Extract and optimize feature patterns from travel itineraries with CKIP NLP "
        "and frequent pattern mining, improving search relevance and user experience."
    ): (
        "CKIP NLPと頻出パターンマイニングで旅行行程から特徴パターンを抽出し最適化。"
        "検索関連性とユーザー体験を改善。"
    ),
    (
        "Assist teaching as a Teaching Assistant for Database Theory, supporting "
        "curriculum delivery and mentoring undergraduate students."
    ): (
        "データベース理論のティーチングアシスタントとして授業運営を支援し、学部生を指導。"
    ),
    (
        "Lead student research teams in multiple industry-university collaboration "
        "projects, coordinating with external partners and delivering actionable data "
        "science solutions."
    ): (
        "複数の産学連携プロジェクトで学生研究チームを率い、学外パートナーと連携して"
        "実行可能なデータサイエンス成果を提供。"
    ),
    (
        "Facilitate communication and project delivery between university and III "
        "teams, ensuring alignment on deliverables and expectations."
    ): (
        "大学とIIIチーム間のコミュニケーションとプロジェクト推進を支援し、"
        "成果物と期待のすり合わせを行う。"
    ),
    (
        "Develop full-stack web applications from end to end for social data analysis, "
        "supporting the transformation of raw posts into interactive word clouds and "
        "buzzword visualizations."
    ): (
        "ソーシャルデータ分析向けのフルスタックWebアプリケーションを端から端まで開発し、"
        "投稿をインタラクティブなワードクラウドとバズワード可視化へ変換。"
    ),
    (
        "Analyze and extract insights from social media data, applying NLP and "
        "visualization tools to generate actionable reports for industry partners."
    ): (
        "ソーシャルメディアデータから知見を抽出し、NLPと可視化で産業パートナー向けの"
        "実行可能なレポートを作成。"
    ),
    "Master": "修士",
    "Bachelor": "学士",
    "Computer Science & Information Engineering": "コンピュータサイエンス・情報工学",
    "Ming Chuan University": "銘傳大学",
    "Programming & ML Frameworks": "プログラミング / MLフレームワーク",
    "Generative AI & NLP": "生成AI / NLP",
    "MLOps & Deployment": "MLOps / デプロイ",
    "Data Engineering": "データエンジニアリング",
    "Cloud & Infra": "クラウド / インフラ",
    "Language": "語学",
    "Leadership & Communication": "リーダーシップ / コミュニケーション",
    "Chinese (Native)": "中国語（母語）",
    "English (Limited Working)": "英語（限定的な実務）",
    "Python (expert)": "Python（エキスパート）",
}

# Axis tags are labels for already-selected source bullets. They do not add facts.
# Lookup is against the English source highlight.
JA_AXIS_TAGS: dict[str, str] = {
    (
        "Built and iterated the video-understanding system as a staged pipeline: "
        "observable facts → recipe-specific ingredient definitions → ingredient "
        "state → cooking issues."
    ): "パイプライン",
    (
        "Coverage 40% → 95% on a versioned eval set; isolate failures to observation "
        "/ ingredient-state / issue-detection."
    ): "エージェント",
    (
        "Capability-based evals and automated scoring for observation accuracy, "
        "issue coverage, factuality, coherence, and turn-level coaching quality."
    ): "評価",
    (
        "Built a multimodal coaching agent that reasons over cooking video and learner "
        "voice to decide whether to reteach, narrow, or advance; raised expert-grounded "
        "coverage from 40% to 95%."
    ): "エージェント",
    (
        "Architected a staged multimodal reasoning pipeline separating observation, "
        "gap inference, and coaching decisions, improving debuggability and reducing "
        "failure propagation across agent stages."
    ): "パイプライン",
    (
        "Designed versioned, capability-based agent evaluations and automated scoring "
        "for coverage, truth, coherence, and per-turn quality."
    ): "評価",
    (
        "Designed and built GenAI infrastructure (AI Gateway, Guardrails, MLflow), "
        "optimizing internal AI service latency by 60%."
    ): "AI Gateway",
    "Reduced overall cloud spend by 40% through FinOps practices.": "FinOps",
    (
        "Developed Departmental Internal AI Agents with Google ADK, automating deep "
        "research tasks, reducing analysis time from 2 hours to 15 minutes."
    ): "社内エージェント",
    "Improved regulatory Agent F1 from 0.67 to 0.89.": "規制エージェント",
    (
        "Improved regulatory Agent F1 from 0.67 to 0.89; adopted by 2 of 5 subsidiaries."
    ): "規制エージェント",
    (
        "Develop standardized ML project templates (AI Cloud Platform template; "
        "FastAPI, CI/CD, Kubernetes), reducing deployment time from 2 weeks to 3 days, "
        "adopted by 30+ projects."
    ): "テンプレート",
    (
        "Implement NLP-focused Python library (UAP Common Library) with 70% internal "
        "adoption and 90%+ code coverage, improving productivity and reliability for "
        "AI developers."
    ): "ライブラリ",
}

# Concise HTML highlight caps: English stays 3/3/2; Japanese uses the GT 3/4/2 shape.
HIGHLIGHT_CAPS = {
    "en": (3, 3, 2),
    "ja": (3, 4, 2),
}

_FORBIDDEN_JA_CLAIMS = (
    "日本語（Fluent）",
    "日本語 (Fluent)",
    "日本語 Fluent",
    "ビジネス日本語",
    "JLPT",
    "N1",
    "LiteLLM",
)


def normalize_language(language: str | None) -> str:
    text = (language or DEFAULT_LANGUAGE).strip().lower()
    if text not in SUPPORTED_LANGUAGES:
        raise ValueError(f"Unsupported language {language!r}; expected one of {SUPPORTED_LANGUAGES}")
    return text


def ui_labels(language: str) -> dict[str, str]:
    return dict(UI_LABELS[normalize_language(language)])


def translate_text(value: Any, language: str) -> Any:
    if not isinstance(value, str):
        return value
    if normalize_language(language) != "ja":
        return value
    stripped = value.strip()
    return JA_STRINGS.get(stripped, value)


def format_date(value: Any, language: str = DEFAULT_LANGUAGE) -> str:
    """Format resume dates; Japanese uses 年月 / 現在."""

    if value is None or value == "":
        return ""
    text = str(value)
    language = normalize_language(language)
    if text.lower() == "present":
        return UI_LABELS[language]["present"]
    from datetime import datetime

    if language == "ja":
        for date_format in ("%Y-%m-%d", "%Y-%m"):
            try:
                parsed = datetime.strptime(text, date_format)
                return f"{parsed.year}年{parsed.month}月"
            except ValueError:
                continue
        return text
    for date_format in ("%Y-%m-%d", "%Y-%m"):
        try:
            return datetime.strptime(text, date_format).strftime("%b %Y")
        except ValueError:
            continue
    return text


def as_of_label(language: str, today: date | None = None) -> str:
    language = normalize_language(language)
    day = today or date.today()
    if language != "ja":
        return day.isoformat()
    return f"{day.year}年{day.month}月{day.day}日 {UI_LABELS['ja']['as_of_suffix']}"


def highlight_cap(language: str, role_index: int) -> int:
    caps = HIGHLIGHT_CAPS[normalize_language(language)]
    if role_index < len(caps):
        return caps[role_index]
    return caps[-1]


def axis_tag(source_highlight: str) -> str | None:
    return JA_AXIS_TAGS.get(source_highlight.strip())


def _translate_mapping(item: Mapping[str, Any], language: str, keys: tuple[str, ...]) -> dict[str, Any]:
    result = dict(item)
    for key in keys:
        if key in result:
            result[key] = translate_text(result[key], language)
    return result


def _translate_list_field(item: dict[str, Any], field: str, language: str) -> None:
    values = item.get(field)
    if not isinstance(values, list):
        return
    item[field] = [translate_text(value, language) for value in values]


def localize_profile(profile: Mapping[str, Any], language: str) -> dict[str, Any]:
    """Translate assembled public strings. Does not add or drop career facts."""

    language = normalize_language(language)
    result = copy.deepcopy(dict(profile))
    if language == "en":
        return result

    basics = dict(result.get("basics") or {})
    basics = _translate_mapping(
        basics, language, ("name", "label", "summary")
    )
    location = dict(basics.get("location") or {})
    location = _translate_mapping(location, language, ("city", "region", "address"))
    basics["location"] = location
    result["basics"] = basics

    work_items = []
    for item in result.get("work") or []:
        source_highlights = list(item.get("highlights") or [])
        localized = _translate_mapping(
            item, language, ("name", "position", "summary", "location")
        )
        localized["highlights"] = [translate_text(text, language) for text in source_highlights]
        localized["highlight_axes"] = [axis_tag(text) for text in source_highlights]
        work_items.append(localized)
    result["work"] = work_items

    projects = []
    for item in result.get("projects") or []:
        localized = _translate_mapping(
            item, language, ("name", "description", "summary")
        )
        _translate_list_field(localized, "highlights", language)
        projects.append(localized)
    result["projects"] = projects

    education = []
    for item in result.get("education") or []:
        localized = _translate_mapping(
            item, language, ("institution", "area", "studyType")
        )
        _translate_list_field(localized, "highlights", language)
        education.append(localized)
    result["education"] = education

    skills = []
    for item in result.get("skills") or []:
        localized = _translate_mapping(item, language, ("name",))
        _translate_list_field(localized, "keywords", language)
        skills.append(localized)
    result["skills"] = skills

    _assert_no_invented_claims(result)
    return result


def _assert_no_invented_claims(profile: Mapping[str, Any]) -> None:
    blob = _profile_blob(profile)
    for token in _FORBIDDEN_JA_CLAIMS:
        if token in blob:
            raise ValueError(f"Japanese render must not claim {token!r}")
    if re.search(r"日本語.{0,12}(Fluent|N1|ビジネス)", blob):
        raise ValueError("Japanese render must not claim Japanese fluency")


def _profile_blob(profile: Mapping[str, Any]) -> str:
    parts: list[str] = []

    def walk(value: Any) -> None:
        if isinstance(value, str):
            parts.append(value)
        elif isinstance(value, Mapping):
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(profile)
    return "\n".join(parts)


__all__ = [
    "DEFAULT_LANGUAGE",
    "HIGHLIGHT_CAPS",
    "JA_DISPLAY_NAME_ALIAS",
    "SUPPORTED_LANGUAGES",
    "as_of_label",
    "axis_tag",
    "format_date",
    "highlight_cap",
    "localize_profile",
    "normalize_language",
    "translate_text",
    "ui_labels",
]
