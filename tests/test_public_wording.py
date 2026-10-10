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


if __name__ == "__main__":
    unittest.main()
