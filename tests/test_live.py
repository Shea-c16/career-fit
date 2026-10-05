import json
import unittest
from io import BytesIO
from unittest.mock import patch
from urllib.error import HTTPError
from live_analysis import analyze
from examples import RESUME, JD


class LiveTests(unittest.TestCase):
    def fixture(self):
        return dict(
            basic_info={},
            education=[],
            internships=[],
            projects=[],
            campus_experience=[],
            awards=[],
            skills={},
            application_answers=[],
            questions=[],
        )

    def test_single_request(self):
        response = dict(
            choices=[dict(finish_reason='stop', message=dict(content=json.dumps(self.fixture())))],
            usage={'prompt_tokens': 10},
        )
        with patch('live_analysis.urlopen', return_value=BytesIO(json.dumps(response).encode())) as call:
            result, usage = analyze(RESUME, JD, 'fake-test-key')
            self.assertEqual(usage['prompt_tokens'], 10)
            self.assertEqual(call.call_count, 1)
            self.assertEqual(json.loads(call.call_args[0][0].data)['thinking']['type'], 'disabled')

    def test_no_retry_or_secret_in_error(self):
        with patch('live_analysis.urlopen', side_effect=HTTPError('url', 402, 'secret', {}, None)) as call:
            with self.assertRaisesRegex(ValueError, '余额不足'):
                analyze(RESUME, JD, 'fake-test-key')
            self.assertEqual(call.call_count, 1)

    def test_empty_input_never_calls(self):
        with patch('live_analysis.urlopen') as call:
            with self.assertRaises(ValueError):
                analyze('', JD, 'fake-test-key')
            call.assert_not_called()


if __name__ == "__main__":
    unittest.main()
