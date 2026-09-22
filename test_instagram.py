import unittest
from unittest.mock import Mock, patch

from src import instagram


def _response(status_code: int, json_data: dict) -> Mock:
    response = Mock()
    response.status_code = status_code
    response.ok = status_code < 400
    response.json.return_value = json_data
    response.text = str(json_data)
    return response


class InstagramPostRetryTests(unittest.TestCase):
    @patch("src.instagram.time.sleep")
    @patch("src.instagram.requests.post")
    def test_retries_meta_rate_limit_errors(self, mock_post: Mock, mock_sleep: Mock) -> None:
        mock_post.side_effect = [
            _response(
                403,
                {
                    "error": {
                        "message": "Application request limit reached",
                        "code": 4,
                        "error_subcode": 2207051,
                    }
                },
            ),
            _response(200, {"id": "123"}),
        ]

        data = instagram._post("123/media_publish", {"creation_id": "abc"})

        self.assertEqual(data, {"id": "123"})
        self.assertEqual(mock_post.call_count, 2)
        mock_sleep.assert_called_once_with(20)

    @patch("src.instagram.time.sleep")
    @patch("src.instagram.requests.post")
    def test_does_not_retry_non_retryable_errors(self, mock_post: Mock, mock_sleep: Mock) -> None:
        mock_post.return_value = _response(
            400,
            {"error": {"message": "Invalid parameter", "code": 100}},
        )

        with self.assertRaisesRegex(RuntimeError, "Meta API HTTP 400"):
            instagram._post("123/media", {"image_url": "https://example.com/image.png"})

        self.assertEqual(mock_post.call_count, 1)
        mock_sleep.assert_not_called()

    @patch("src.instagram.requests.post")
    def test_raises_runtime_error_for_invalid_success_json(self, mock_post: Mock) -> None:
        response = Mock()
        response.status_code = 200
        response.ok = True
        response.text = "not-json"
        response.json.side_effect = ValueError("bad json")
        mock_post.return_value = response

        with self.assertRaisesRegex(RuntimeError, "invalid JSON"):
            instagram._post("123/media", {"image_url": "https://example.com/image.png"})

    @patch("src.instagram.requests.post")
    def test_raises_runtime_error_for_non_object_success_json(self, mock_post: Mock) -> None:
        response = Mock()
        response.status_code = 200
        response.ok = True
        response.text = '["ok"]'
        response.json.return_value = ["ok"]
        mock_post.return_value = response

        with self.assertRaisesRegex(RuntimeError, "unexpected JSON payload"):
            instagram._post("123/media", {"image_url": "https://example.com/image.png"})


if __name__ == "__main__":
    unittest.main()
