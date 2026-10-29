"""Offline regressions for the report's JSON-as-source contract."""

import copy
import importlib.util
import json
import re
import sys
import unittest
from pathlib import Path


sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("render_progress", ROOT / "scripts/render-progress.py")
REPORT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REPORT)


def section(document, name):
    return document.split(f'<section aria-labelledby="{name}">', 1)[1].split('</section>', 1)[0]


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / "consolidation-status.json").read_text(encoding="utf-8"))

    def test_generated_report_matches_source(self):
        self.assertEqual((ROOT / "progress-summary.html").read_text(encoding="utf-8"), REPORT.render(self.data))

    def test_baseline_mutations_change_the_narrative(self):
        data = copy.deepcopy(self.data)
        baseline = data["baseline"]
        baseline.update(run_id="different-run", environment="fabrikam", verdict="PASS", deployed_builds="build-123")
        baseline["smoke"] = {"passed": 3, "total": 4}
        baseline["verification"] = {"passed": 7, "failed": 8, "unexecuted": 9, "executed": 15, "total": 24}
        baseline["grid_observation_is_test_pass"] = True
        baseline["final_acceptance"] = True
        evidence = section(REPORT.render(data), "evidence")
        for expected in ["Fabrikam baseline different-run", "overall verification PASS", "Smoke: 3 of 4 passed", "7 passed, 8 failed and 9 unexecuted (15 of 24 executed)", "Deployed builds: build-123", "standalone passed test: yes", "Final acceptance: yes"]:
            self.assertIn(expected, evidence)

    def test_pr_status_mutations_change_the_narrative(self):
        data = copy.deepcopy(self.data)
        data["sources"]["report_manager"].update(pr_state="MERGED", smoke="PASS: new check")
        data["sources"]["verification"].update(pr_state="CLOSED", review_decision="APPROVED")
        data["sources"]["merged_documentation_pr"]["merged_at"] = None
        evidence = section(REPORT.render(data), "evidence")
        for expected in ["MERGED", "PASS: new check", "CLOSED", "APPROVED", "NOT RECORDED AS MERGED"]:
            self.assertIn(expected, evidence)
        self.assertNotIn('still needs re-review', evidence)

    def test_header_and_spec_status_follow_source(self):
        data = copy.deepcopy(self.data)
        next(p for p in data["planned_points"] if p["id"] == "C0")["status"] = "todo"
        data["sources"]["spec"]["status"] = "approved"
        rendered = REPORT.render(data)
        self.assertIn('Consolidation status: <strong>To do</strong>', rendered)
        self.assertIn('status: <strong>approved</strong>', section(rendered, "agreed"))

    def test_validation_exposes_supporting_evidence(self):
        rendered = section(REPORT.render(self.data), "validation")
        for item in self.data["validation"]:
            if item["status"] == "PASS":
                self.assertTrue(item.get("evidence"), item["name"])
                for target in item["evidence"]:
                    self.assertIn(REPORT.esc(target), rendered)

    def test_historical_labels_are_readable_paraphrases(self):
        for finding in self.data["review_findings"]:
            label = finding["issue"]
            self.assertGreater(len(label), 20)
            self.assertTrue(label.endswith('.'))
            self.assertNotRegex(label, r'(?i)[A-Z]:[\\/]Users[\\/]')
            self.assertNotIn('`', label)
            self.assertTrue(finding["url"].endswith(str(finding["id"])))

    def test_source_text_is_escaped(self):
        self.data["title"] = '<script>not executable</script>'
        self.assertIn('&lt;script&gt;not executable&lt;/script&gt;', REPORT.render(self.data))

    def test_agreed_document_shapes_and_plan_ids(self):
        points = self.data["planned_points"]
        self.assertEqual(len(points), len({point["id"] for point in points}))
        for path, count in [("journeys/campaign-lifecycle.md", 6), ("maps/report-manager/daily-outbound-interval.md", 4)]:
            self.assertEqual(len(re.findall(r'^## ', (ROOT / path).read_text(encoding="utf-8"), re.M)), count)


if __name__ == "__main__":
    unittest.main()
