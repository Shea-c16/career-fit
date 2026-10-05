import unittest
from core import input_id, validate_evidence
from examples import RESUME, MATCHES, REWRITES, ANSWER

class EvidenceTests(unittest.TestCase):
    def test_demo_quotes_are_real(self):
        self.assertEqual(validate_evidence(RESUME, MATCHES, REWRITES), [])

    def test_fabricated_source_rejected(self):
        self.assertTrue(validate_evidence(RESUME, [{"evidence":"独立开发推荐算法，收入提升50%"}], []))

    def test_changed_resume_invalidates_result(self):
        self.assertNotEqual(input_id("原简历", "JD"), input_id("新增项目", "JD"))

    def test_answer_length(self):
        self.assertLessEqual(len(ANSWER), 200)

if __name__ == "__main__":
    unittest.main()
