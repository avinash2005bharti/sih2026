import unittest

from orchestrator.task_classifier import task_classifier


class TaskClassifierTests(unittest.TestCase):
    def test_routes_maintenance(self):
        result = task_classifier.classify("Analyze this maintenance failure scenario")
        self.assertEqual(result.agent, "maintenance_agent")

    def test_routes_safety(self):
        result = task_classifier.classify("Identify safety hazards in this scenario")
        self.assertEqual(result.agent, "safety_agent")

    def test_routes_document(self):
        result = task_classifier.classify("Summarize this inspection report")
        self.assertEqual(result.agent, "document_agent")
        self.assertTrue(result.requires_rag)

    def test_routes_tool(self):
        result = task_classifier.classify("Create a folder called test_reports")
        self.assertEqual(result.agent, "filesystem_agent")
        self.assertTrue(result.requires_tools)

    def test_routes_reporting(self):
        result = task_classifier.classify("Generate report with spreadsheet and excel")
        self.assertEqual(result.agent, "reporting_agent")
        self.assertTrue(result.requires_tools)


if __name__ == "__main__":
    unittest.main()
