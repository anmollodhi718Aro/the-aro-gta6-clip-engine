"""Tests for the local OAuth destination-profile bootstrap."""
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from scripts.setup_youtube_destination import _atomic_private_json, setup_destination


class YouTubeDestinationSetupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.client = self.root / "client-secret.json"
        self.client.write_text('{"installed": {"client_id": "test-client"}}', encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def _mocks(self, channel_ids=("UC1234567890abcdef",)):
        credentials = SimpleNamespace(
            scopes=["openid", "https://www.googleapis.com/auth/youtube.readonly",
                    "https://www.googleapis.com/auth/youtube.upload"],
            has_scopes=lambda scopes: True,
        )
        youtube = Mock()
        youtube.channels.return_value.list.return_value.execute.return_value = {
            "items": [{"id": channel_id} for channel_id in channel_ids]
        }
        google_api = Mock(return_value=youtube)
        return credentials, youtube, google_api

    def test_creates_profile_from_verified_google_identity_and_channel(self):
        credentials, youtube, google_api = self._mocks()
        with (
            patch("backend.app.youtube_upload._authorize_google", return_value=credentials),
            patch("backend.app.youtube_upload._oauth_client_id", return_value="test-client"),
            patch("backend.app.youtube_owner_approval._verify_google_id_token", return_value={
                "sub": "verified-google-subject",
                "iss": "https://accounts.google.com",
                "azp": "test-client",
            }),
            patch.dict("sys.modules", {
                "googleapiclient": SimpleNamespace(discovery=SimpleNamespace(build=google_api)),
                "googleapiclient.discovery": SimpleNamespace(build=google_api),
            }),
        ):
            result = setup_destination(
                repository_root=self.root, client_secrets=self.client,
                profile_name="aroanmol7",
            )
        config = json.loads(Path(result["config_path"]).read_text(encoding="utf-8"))
        self.assertEqual(config["profiles"]["aroanmol7"], {
            "google_subject": "verified-google-subject",
            "channel_id": "UC1234567890abcdef",
        })
        self.assertEqual(result["channel_id"], "UC1234567890abcdef")
        youtube.channels.return_value.list.assert_called_once_with(part="id", mine=True)

    def test_requires_explicit_channel_when_account_has_multiple_channels(self):
        credentials, _, google_api = self._mocks(("UC1234567890abcdef", "UCabcdef1234567890"))
        with (
            patch("backend.app.youtube_upload._authorize_google", return_value=credentials),
            patch("backend.app.youtube_upload._oauth_client_id", return_value="test-client"),
            patch("backend.app.youtube_owner_approval._verify_google_id_token", return_value={
                "sub": "verified-google-subject", "iss": "accounts.google.com",
            }),
            patch.dict("sys.modules", {
                "googleapiclient": SimpleNamespace(discovery=SimpleNamespace(build=google_api)),
                "googleapiclient.discovery": SimpleNamespace(build=google_api),
            }),
        ):
            with self.assertRaisesRegex(PermissionError, "multiple channels"):
                setup_destination(
                    repository_root=self.root, client_secrets=self.client,
                    profile_name="aroanmol7",
                )

    def test_private_json_writer_refuses_to_overwrite_existing_profile_map(self):
        path = self.root / ".secrets" / "destination_profiles.json"
        path.parent.mkdir()
        path.write_text('{"profiles": {}}', encoding="utf-8")
        with self.assertRaises(FileExistsError):
            _atomic_private_json(path, {"profiles": {"other": {}}})
        self.assertEqual(json.loads(path.read_text(encoding="utf-8")), {"profiles": {}})

    def test_invalid_profile_name_is_rejected_before_oauth(self):
        with patch("backend.app.youtube_upload._authorize_google") as authorize:
            with self.assertRaisesRegex(ValueError, "profile name"):
                setup_destination(
                    repository_root=self.root, client_secrets=self.client,
                    profile_name="../outside",
                )
        authorize.assert_not_called()


if __name__ == "__main__":
    unittest.main()
