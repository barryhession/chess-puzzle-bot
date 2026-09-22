import unittest
from unittest.mock import patch

from src import instagram


class _FakeResponse:
    def __init__(self, *, ok: bool, status_code: int, data: dict, text: str | None = None):
        self.ok = ok
        self.status_code = status_code
        self._data = data
        self.text = text or str(data)

    def json(self) -> dict:
        return self._data


class InstagramPostRetryTests(unittest.TestCase):
    @patch("src.instagram.time.sleep")
    @patch("src.instagram.requests.post")
    def test_retries_meta_request_limit_before_success(self, mock_post, mock_sleep):
        mock_post.side_effect = [
            _FakeResponse(
                ok=False,
                status_code=403,
                data={
                    "error": {
                        "message": "Application request limit reached",
                        "code": 4,
                        "error_subcode": 2207051,
                        "is_transient": False,
                    }
                },
            ),
            _FakeResponse(
                ok=False,
                status_code=403,
                data={
                    "error": {
                        "message": "Application request limit reached",
                        "code": 4,
                        "error_subcode": 2207051,
                        "is_transient": False,
                    }
                },
            ),
            _FakeResponse(ok=True, status_code=200, data={"id": "123"}),
        ]

        result = instagram._post("account/media_publish", {"creation_id": "abc"})

        self.assertEqual(result, {"id": "123"})
        self.assertEqual(mock_post.call_count, 3)
        mock_sleep.assert_any_call(20)
        mock_sleep.assert_any_call(40)

    @patch("src.instagram.time.sleep")
    @patch("src.instagram.requests.post")
    def test_non_retryable_error_raises_immediately(self, mock_post, mock_sleep):
        mock_post.return_value = _FakeResponse(
            ok=False,
            status_code=403,
            data={
                "error": {
                    "message": "Invalid OAuth access token.",
                    "code": 190,
                    "is_transient": False,
                }
            },
        )

        with self.assertRaises(RuntimeError):
            instagram._post("account/media_publish", {"creation_id": "abc"})

        self.assertEqual(mock_post.call_count, 1)
        mock_sleep.assert_not_called()

    @patch("src.instagram.time.sleep")
    @patch("src.instagram.requests.post")
    def test_invalid_success_payload_raises_runtime_error(self, mock_post, mock_sleep):
        mock_post.return_value = _FakeResponse(
            ok=True,
            status_code=200,
            data=["unexpected", "payload"],
            text='["unexpected", "payload"]',
        )

        with self.assertRaises(RuntimeError):
            instagram._post("account/media_publish", {"creation_id": "abc"})

        self.assertEqual(mock_post.call_count, 1)
        mock_sleep.assert_not_called()

    @patch("src.instagram.time.sleep")
    @patch("src.instagram.requests.post")
    def test_retries_server_error_with_non_json_body(self, mock_post, mock_sleep):
        mock_post.side_effect = [
            _FakeResponse(
                ok=False,
                status_code=500,
                data="server exploded",
                text="server exploded",
            ),
            _FakeResponse(ok=True, status_code=200, data={"id": "123"}),
        ]

        result = instagram._post("account/media_publish", {"creation_id": "abc"})

        self.assertEqual(result, {"id": "123"})
        self.assertEqual(mock_post.call_count, 2)
        mock_sleep.assert_called_once_with(20)


if __name__ == "__main__":
    unittest.main()
