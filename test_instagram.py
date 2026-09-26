import unittest
from unittest.mock import Mock, patch

from src import instagram


def _mock_response(*, status_code: int, ok: bool, body: dict, text: str = ""):
    resp = Mock()
    resp.status_code = status_code
    resp.ok = ok
    resp.text = text or str(body)
    resp.json.return_value = body
    return resp


class InstagramPostTests(unittest.TestCase):
    def test_post_retries_retryable_meta_403_then_succeeds(self):
        retryable_error = {
            "error": {
                "message": "Application request limit reached",
                "type": "OAuthException",
                "code": 4,
                "error_subcode": 2207051,
            }
        }
        success = {"id": "123"}

        with patch("src.instagram.requests.post") as post, patch("src.instagram.time.sleep") as sleep:
            post.side_effect = [
                _mock_response(status_code=403, ok=False, body=retryable_error, text="retryable"),
                _mock_response(status_code=200, ok=True, body=success),
            ]

            result = instagram._post("endpoint", {"k": "v"})

        self.assertEqual(result, success)
        self.assertEqual(post.call_count, 2)
        sleep.assert_called_once_with(20)

    def test_post_retries_retryable_meta_internal_error_then_succeeds(self):
        retryable_error = {
            "error": {
                "message": "Fatal",
                "type": "OAuthException",
                "code": -1,
                "error_subcode": 2207085,
            }
        }
        success = {"id": "123"}

        with patch("src.instagram.requests.post") as post, patch("src.instagram.time.sleep") as sleep:
            post.side_effect = [
                _mock_response(status_code=400, ok=False, body=retryable_error, text="retryable"),
                _mock_response(status_code=200, ok=True, body=success),
            ]

            result = instagram._post("endpoint", {"k": "v"})

        self.assertEqual(result, success)
        self.assertEqual(post.call_count, 2)
        sleep.assert_called_once_with(20)

    def test_post_retries_generic_internal_error_without_known_subcode(self):
        retryable_error = {
            "error": {
                "message": "Fatal",
                "type": "OAuthException",
                "code": -1,
                "error_user_title": "Generic Internal Error",
                "error_user_msg": "An internal server error occurred. Please try again later.",
            }
        }
        success = {"id": "123"}

        with patch("src.instagram.requests.post") as post, patch("src.instagram.time.sleep") as sleep:
            post.side_effect = [
                _mock_response(status_code=400, ok=False, body=retryable_error, text="retryable"),
                _mock_response(status_code=200, ok=True, body=success),
            ]

            result = instagram._post("endpoint", {"k": "v"})

        self.assertEqual(result, success)
        self.assertEqual(post.call_count, 2)
        sleep.assert_called_once_with(20)

    def test_post_retries_oauth_exception_code_minus_one_without_metadata(self):
        retryable_error = {
            "error": {
                "message": "Fatal",
                "type": "OAuthException",
                "code": -1,
            }
        }
        success = {"id": "123"}

        with patch("src.instagram.requests.post") as post, patch("src.instagram.time.sleep") as sleep:
            post.side_effect = [
                _mock_response(status_code=400, ok=False, body=retryable_error, text="retryable"),
                _mock_response(status_code=200, ok=True, body=success),
            ]

            result = instagram._post("endpoint", {"k": "v"})

        self.assertEqual(result, success)
        self.assertEqual(post.call_count, 2)
        sleep.assert_called_once_with(20)

    def test_post_exhausts_all_retries_then_raises(self):
        retryable_error = {
            "error": {
                "message": "Fatal",
                "type": "OAuthException",
                "code": -1,
                "error_subcode": 2207085,
            }
        }

        with patch("src.instagram.requests.post") as post, patch("src.instagram.time.sleep") as sleep:
            post.return_value = _mock_response(
                status_code=400,
                ok=False,
                body=retryable_error,
                text="still failing",
            )

            with self.assertRaises(RuntimeError) as ctx:
                instagram._post("endpoint", {"k": "v"})

        self.assertIn("Meta API HTTP 400", str(ctx.exception))
        self.assertEqual(post.call_count, len(instagram._BACKOFF_SECONDS) + 1)
        self.assertEqual(
            [call.args[0] for call in sleep.call_args_list],
            list(instagram._BACKOFF_SECONDS),
        )


    def test_post_raises_immediately_on_non_retryable_meta_error(self):
        non_retryable_error = {
            "error": {
                "message": "Invalid OAuth access token.",
                "type": "OAuthException",
                "code": 190,
            }
        }

        with patch("src.instagram.requests.post") as post, patch("src.instagram.time.sleep") as sleep:
            post.return_value = _mock_response(
                status_code=400,
                ok=False,
                body=non_retryable_error,
                text="bad token",
            )

            with self.assertRaises(RuntimeError) as ctx:
                instagram._post("endpoint", {"k": "v"})

        self.assertIn("Meta API HTTP 400", str(ctx.exception))
        sleep.assert_not_called()


if __name__ == "__main__":
    unittest.main()
