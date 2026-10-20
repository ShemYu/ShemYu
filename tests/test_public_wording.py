"""Public resume wording must not leak banned phrases."""

import unittest

from src.graph.loader import load_graph
from src.graph.schema import Claim, Skill
from src.render.adapter import bind_view
from src.render.views import load_view


BANNED_PUBLIC_PHRASES = (
    "53/56",
    "67.6",
    "83.0",
    "DS built",
    "DS-built",
    "data scientist's PoC",
    "coordinated 10",
    "10 cross-functional",
    "LiteLLM",
    "distributed AI Gateway",
    "7+ years",
    "Limited Working",
    "dish coverage",
    "40% → 95%",
    "40% to 95%",
    "ensuring scalable and secure operations",
)

PUBLIC_VIEWS = ("one-pager", "detailed", "full", "github-readme")


def _public_surface(profile: dict) -> str:
    parts = [
        profile.get("basics", {}).get("summary", ""),
        profile.get("basics", {}).get("label", ""),
    ]
    for item in [*(profile.get("work") or []), *(profile.get("projects") or [])]:
        parts.append(item.get("summary") or "")
        parts.append(item.get("position") or "")
        parts.extend(item.get("highlights") or [])
    for row in profile.get("skills") or []:
        parts.append(row.get("name") or "")
        parts.extend(row.get("keywords") or [])
    return "\n".join(parts)


class PublicWordingTest(unittest.TestCase):
    def test_public_claims_and_views_omit_banned_phrases(self):
        graph = load_graph("career")
        blobs = []
        for node in graph.of_type("claim"):
            if isinstance(node, Claim) and node.disclosure == "public":
                blobs.append(f"{node.id}\n{node.text.en}\n{node.text.ja}")
        for node in graph.of_type("skill"):
            if isinstance(node, Skill) and node.disclosure == "public":
                blobs.append(node.title)
        for view_id in PUBLIC_VIEWS:
            profile = bind_view(graph, load_view(f"views/{view_id}.yaml"))
            blobs.append(_public_surface(profile))

        surface = "\n".join(blobs)
        for phrase in BANNED_PUBLIC_PHRASES:
            self.assertNotIn(phrase, surface, phrase)

        self.assertIn("English (Professional Working)", surface)
        self.assertIn("issue recall from 50% to 95%", surface)
        self.assertNotIn("Moment Coach", _public_surface(bind_view(graph, load_view("views/one-pager.yaml"))))

    def test_owner_confirmed_2026_10_20_facts_stay_in_scope(self):
        graph = load_graph("career")
        claim = graph.get("cookpad-vu-limited-beta")
        self.assertIsInstance(claim, Claim)
        self.assertEqual(claim.status, "confirmed")
        self.assertEqual(claim.disclosure, "public")
        self.assertEqual(claim.focus, "cookpad-vu")
        self.assertEqual(claim.source, "user-confirmed:2026-10-20")
        self.assertEqual(
            claim.text.en,
            "Building a consumer-facing multimodal cooking coach, launched to a limited beta of end users, that uses video and learner voice to identify where a cook is stuck and guide the next step.",
        )
        self.assertEqual(claim.text.ja, "")
        self.assertIn("cookpad-vu-limited-beta", graph.get("cookpad-vu").claims)
        self.assertEqual(
            claim.do_not_claim,
            ["user counts", "GA status", "launch plans"],
        )
        self.assertNotIn("20", claim.text.en)
        self.assertNotRegex(claim.text.en, r"\bGA\b|general availability|launch plan")

        skill = graph.get("ai-assisted-development")
        self.assertIsInstance(skill, Skill)
        self.assertEqual(skill.disclosure, "public")
        self.assertEqual(
            skill.title,
            "AI-assisted development (Claude Code, Cursor, Orca)",
        )
        self.assertNotIsInstance(skill, Claim)
        for focus in graph.of_type("focus"):
            self.assertNotIn("ai-assisted-development", focus.stack)
            self.assertNotIn("ai-assisted-development", focus.claims)
        self.assertIn(
            "ai-assisted-development",
            graph.get("skill-group-programming").skills,
        )


if __name__ == "__main__":
    unittest.main()
