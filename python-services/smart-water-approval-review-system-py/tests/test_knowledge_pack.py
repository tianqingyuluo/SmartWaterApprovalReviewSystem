import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from knowledge_pack import load_knowledge_pack


class KnowledgePackTests(unittest.TestCase):
    def test_knowledge_pack_loads_and_has_mvp_materials(self):
        pack = load_knowledge_pack()

        material_types = {item["materialType"] for item in pack["materialChecklist"]}

        self.assertEqual(pack["version"], "water-permit-mvp-2026-04-27")
        self.assertEqual(material_types, {"APPLICATION_FORM", "BUSINESS_LICENSE", "ID_CARD"})

    def test_knowledge_pack_basis_refs_are_defined(self):
        pack = load_knowledge_pack()
        basis_ids = {item["id"] for item in pack["reviewBasis"]}

        for rule in pack["applicationFieldRules"]:
            self.assertLessEqual(set(rule.get("basisRefs", [])), basis_ids)

        for item in pack["materialChecklist"]:
            self.assertLessEqual(set(item.get("basisRefs", [])), basis_ids)

        for manual_rule in pack["manualReviewRules"]:
            self.assertLessEqual(set(manual_rule.get("basisRefs", [])), basis_ids)

    def test_knowledge_pack_json_is_utf8_and_parseable(self):
        path = ROOT / "knowledge_pack" / "water_permit_mvp.json"

        data = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual(data["language"], "zh-CN")
        self.assertTrue(data["citationFormat"]["basisRefRule"])


if __name__ == "__main__":
    unittest.main()
