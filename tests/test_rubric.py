import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
RUBRIC = ROOT / "evals" / "run_rubric.py"
EXPECTED = ROOT / "demo" / "expected" / "HOW_IT_WORKS.md"


class RubricTests(unittest.TestCase):
    def score(self, case, path):
        result = subprocess.run(
            [sys.executable, str(RUBRIC), "--case", case, "--document", str(path)],
            capture_output=True, text=True, check=False,
        )
        self.assertIn(result.returncode, (0, 1), result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(set(payload), {"case", "passed", "checks"})
        self.assertEqual(payload["case"], case)
        self.assertEqual(result.returncode, 0 if payload["passed"] else 1)
        for check in payload["checks"]:
            self.assertEqual(set(check), {"name", "passed", "detail"})
            self.assertIsInstance(check["passed"], bool)
        return payload

    def score_text(self, case, text):
        # Keep the relative sources of the reference document valid.
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", dir=EXPECTED.parent, encoding="utf-8"
        ) as document:
            document.write(text)
            document.flush()
            return self.score(case, Path(document.name))

    def failed_names(self, result):
        return {item["name"] for item in result["checks"] if not item["passed"]}

    def test_weak_baseline_fails_evidence_and_diagrams(self):
        result = self.score("bootstrap-agent-product", ROOT / "evals/baseline/no-skill.md")
        self.assertFalse(result["passed"])
        self.assertIn("mermaid-count", self.failed_names(result))
        self.assertIn("evidence-labels", self.failed_names(result))

    def test_expected_document_passes_bootstrap(self):
        self.assertTrue(self.score("bootstrap-agent-product", EXPECTED)["passed"])

    def test_fictional_sample_does_not_claim_runtime_verification(self):
        text = EXPECTED.read_text()
        row = next(line for line in text.splitlines() if line.startswith("| Recorded submit"))
        self.assertIn("runtime evidence: absent", row)
        self.assertIn("fictional sample only", row)
        self.assertNotIn("runtime verified", row)

    def test_broken_local_source_fails(self):
        text = EXPECTED.read_text().replace("../acorn-tasks/docs/product.md", "./missing-source.md")
        self.assertIn("local-links", self.failed_names(self.score_text("bootstrap-agent-product", text)))

    def test_language_check_accepts_chinese_headings_and_technical_names(self):
        text = """# Acorn Tasks 如何工作
## 产品定位
用户提交任务，并查看任务状态。
## 当前证据
代码已核对。测试已验证。真实运行证据缺失。用户验收尚未完成。
## 系统关系
```mermaid
flowchart LR
    用户 --> TaskInbox
```
## 请求流程
```mermaid
sequenceDiagram
    用户->>TaskInbox: submit
    TaskInbox-->>用户: task-001
```
## 当前限制
进程结束后，任务丢失。
## 来源与核对记录
[产品说明](../acorn-tasks/docs/product.md)
分析版本：synthetic-v1。
最后核对日期：2026-10-14
"""
        self.assertTrue(self.score_text("bilingual-zh-cn", text)["passed"])
        english = EXPECTED.read_text()
        self.assertIn("language", self.failed_names(self.score_text("bilingual-zh-cn", english)))

    def test_static_case_accepts_gap_and_rejects_success_claim(self):
        text = EXPECTED.read_text()
        start = text.index("| Recorded submit")
        end = text.index("\n", start)
        text = text[:start] + "| Execution | runtime verified: no runtime evidence is available | No run record exists for this case. |" + text[end:]
        result = self.score_text("static-no-runtime", text)
        self.assertTrue(result["passed"], result)
        text += "\nProduction delivery succeeded.\n"
        self.assertIn("forbidden-phrases", self.failed_names(self.score_text("static-no-runtime", text)))

    def test_conflict_case_requires_named_authority_and_conflict(self):
        text = EXPECTED.read_text()
        result = self.score_text("conflicting-sources", text)
        self.assertIn("phrases", self.failed_names(result))
        text += "\nThe sources conflict: the old README requires disk persistence. The selected authority is docs/product.md, which requires memory storage.\n"
        self.assertTrue(self.score_text("conflicting-sources", text)["passed"])

    def test_non_agent_case_accepts_absence_but_rejects_invented_loop_and_memory(self):
        text = EXPECTED.read_text()
        self.assertTrue(self.score_text("non-agent-product", text)["passed"])
        for addition in ("\n## Agent loop\nThe agent plans and retries.\n", "\n## Long-term memory\nThe agent stores facts.\n"):
            with self.subTest(addition=addition):
                self.assertIn("forbidden-phrases", self.failed_names(self.score_text("non-agent-product", text + addition)))

    def test_refresh_rejects_history_and_stale_persistence_limit(self):
        text = EXPECTED.read_text()
        result = self.score_text("refresh-current-state", text)
        self.assertIn("forbidden-phrases", self.failed_names(result))
        text = text.replace("Tasks disappear when the process ends.", "Tasks survive a process restart in the current SQLite implementation.")
        text = text.replace("The inbox has no disk storage.", "The inbox saves tasks in SQLite.")
        text = text.replace("Tasks disappear after restart", "Saved tasks fail to load")
        self.assertTrue(self.score_text("refresh-current-state", text)["passed"])
        self.assertIn("forbidden-phrases", self.failed_names(self.score_text("refresh-current-state", text + "\n## Change log\nWe added storage.\n")))

    def test_missing_document_returns_failed_json(self):
        result = self.score("bootstrap-agent-product", EXPECTED.parent / "absent.md")
        self.assertEqual(self.failed_names(result), {"document-readable"})

    def test_unknown_case_returns_failed_json(self):
        result = self.score("unknown-case", EXPECTED)
        self.assertEqual(self.failed_names(result), {"case-known"})

    def test_fenced_examples_cannot_supply_evidence_or_headings(self):
        text = "# A note\n\n```text\n" + EXPECTED.read_text() + "\n```\n"
        result = self.score_text("bootstrap-agent-product", text)
        self.assertIn("headings", self.failed_names(result))
        self.assertIn("evidence-labels", self.failed_names(result))
        self.assertIn("mermaid-count", self.failed_names(result))

    def test_unclosed_fence_fails(self):
        text = EXPECTED.read_text() + "\n```python\nprint('synthetic')\n"
        self.assertIn("fences-closed", self.failed_names(self.score_text("bootstrap-agent-product", text)))

    def test_malformed_source_link_fails_without_cli_crash(self):
        text = EXPECTED.read_text() + "\n[Malformed source](https://[)\n"
        self.assertIn("local-links", self.failed_names(self.score_text("bootstrap-agent-product", text)))


if __name__ == "__main__":
    unittest.main()
