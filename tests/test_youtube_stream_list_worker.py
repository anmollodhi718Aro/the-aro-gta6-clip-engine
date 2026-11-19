"""Tests for bounded official streamList worker."""
import tempfile, threading, unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
from backend.app.consent_registry import ConsentRegistry
from backend.app.models import PermissionRecord
from backend.app.polling_checkpoint_store import PollingCheckpointStore
from backend.app.youtube_stream_list_worker import StreamListError, run_bounded_stream_list

class RpcError(Exception):
    def __init__(self, name): self.name = name
    def code(self): return SimpleNamespace(name=self.name)

class StreamListWorkerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.registry = ConsentRegistry(root / "consent.sqlite3")
        now = datetime.now(timezone.utc)
        self.registry.grant(PermissionRecord(source_id="video-1", granted_by="creator",
            scopes=frozenset({"analyze_chat"}), granted_at=now-timedelta(minutes=1)))
        self.checkpoints = PollingCheckpointStore(root / "cursor.sqlite3")
    def tearDown(self): self.temp.cleanup()
    def run_worker(self, **kwargs):
        args = dict(registry=self.registry, video_id="video-1", live_chat_id="chat-1",
            stream_factory=Mock(return_value=iter([])), on_response=Mock(),
            stop_event=threading.Event(), max_responses=5, max_runtime_seconds=30,
            wait=lambda _: False, checkpoint_store=self.checkpoints)
        args.update(kwargs)
        return run_bounded_stream_list(**args)
    def test_persists_response_cursor(self):
        response=SimpleNamespace(next_page_token="cursor-2", offline_at=None)
        callback=Mock()
        result=self.run_worker(stream_factory=lambda *_: iter([response]),
            on_response=callback, max_responses=1)
        self.assertEqual(result.responses_received, 1)
        self.assertEqual(self.checkpoints.load("video-1").page_token, "cursor-2")
        callback.assert_called_once_with(response)
    def test_reconnect_resumes_cursor(self):
        response=SimpleNamespace(next_page_token="resume-here", offline_at=None)
        factory=Mock(side_effect=[iter([response]), iter([])])
        waits=[]
        result=self.run_worker(stream_factory=factory, max_responses=2, max_reconnects=1,
            wait=lambda seconds: waits.append(seconds) or False)
        self.assertEqual(result.reconnects, 1)
        self.assertEqual(factory.call_args_list[1].args, ("chat-1", "resume-here"))
        self.assertEqual(waits, [2.0])
    def test_revocation_blocks_reconnect(self):
        response=SimpleNamespace(next_page_token="resume", offline_at=None)
        factory=Mock(side_effect=[iter([response]), iter([])])
        def revoke(_):
            self.registry.revoke("video-1", actor="owner")
            return False
        with self.assertRaises(PermissionError):
            self.run_worker(stream_factory=factory, max_responses=2, max_reconnects=1, wait=revoke)
        self.assertEqual(factory.call_count, 1)
    def test_permission_denied_is_not_retried(self):
        factory=Mock(side_effect=RpcError("PERMISSION_DENIED"))
        with self.assertRaises(StreamListError): self.run_worker(stream_factory=factory)
        self.assertEqual(factory.call_count, 1)
    def test_transient_error_retries(self):
        response=SimpleNamespace(next_page_token=None, offline_at="ended")
        factory=Mock(side_effect=[RpcError("UNAVAILABLE"), iter([response])])
        waits=[]
        result=self.run_worker(stream_factory=factory, max_reconnects=1,
            wait=lambda seconds: waits.append(seconds) or False)
        self.assertEqual((result.responses_received,result.reconnects,result.offline),(1,1,True))
        self.assertEqual(waits,[2.0])
    def test_callback_failure_does_not_advance_cursor(self):
        response=SimpleNamespace(next_page_token="must-not-save", offline_at=None)
        with self.assertRaises(RuntimeError):
            self.run_worker(stream_factory=lambda *_: iter([response]),
                on_response=Mock(side_effect=RuntimeError("storage unavailable")))
        self.assertIsNone(self.checkpoints.load("video-1"))
    def test_stop_event_prevents_connection(self):
        stop=threading.Event(); stop.set(); factory=Mock()
        result=self.run_worker(stream_factory=factory, stop_event=stop)
        self.assertEqual(result.responses_received,0); factory.assert_not_called()
    def test_mismatched_checkpoint_is_rejected(self):
        self.checkpoints.save("video-1",live_chat_id="other-chat",page_token="p")
        with self.assertRaises(ValueError): self.run_worker()

if __name__ == "__main__": unittest.main()
