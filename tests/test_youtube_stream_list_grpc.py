"""Tests for the optional YouTube streamList gRPC adapter."""
import unittest
from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import Mock
from backend.app.youtube_stream_list_grpc import make_stream_factory, response_to_chat_events

class FakeGrpc:
    def __init__(self): self.closed = False
    def ssl_channel_credentials(self): return object()
    @contextmanager
    def secure_channel(self, target, credentials):
        self.target = target
        try: yield object()
        finally: self.closed = True

class FakeMessages:
    class LiveChatMessageListRequest:
        def __init__(self, **kwargs): self.kwargs = kwargs

class FakeServices:
    class V3DataLiveChatMessageServiceStub:
        def __init__(self, channel): pass
        def StreamList(self, request, metadata):
            FakeServices.last = (request, metadata)
            return iter(["one", "two"])

class GrpcAdapterTests(unittest.TestCase):
    def test_requires_exactly_one_credential(self):
        with self.assertRaises(ValueError):
            make_stream_factory(api_key="", oauth_token="", grpc_module=FakeGrpc(),
                messages_module=FakeMessages, services_module=FakeServices)
        with self.assertRaises(ValueError):
            make_stream_factory(api_key="key", oauth_token="token", grpc_module=FakeGrpc(),
                messages_module=FakeMessages, services_module=FakeServices)
    def test_api_key_request_and_channel_lifecycle(self):
        grpc = FakeGrpc()
        factory = make_stream_factory(api_key="test-key", grpc_module=grpc,
            messages_module=FakeMessages, services_module=FakeServices)
        self.assertEqual(list(factory("chat-1", "cursor-1")), ["one", "two"])
        request, metadata = FakeServices.last
        self.assertEqual(request.kwargs, {"part":["snippet"],"live_chat_id":"chat-1","page_token":"cursor-1"})
        self.assertEqual(metadata, (("x-goog-api-key","test-key"),))
        self.assertEqual(grpc.target, "dns:///youtube.googleapis.com:443")
        self.assertTrue(grpc.closed)
    def test_oauth_metadata(self):
        factory = make_stream_factory(oauth_token="token", grpc_module=FakeGrpc(),
            messages_module=FakeMessages, services_module=FakeServices)
        list(factory("chat-1", None))
        self.assertEqual(FakeServices.last[1], (("authorization","Bearer token"),))
    def test_rejects_blank_chat_id(self):
        factory = make_stream_factory(api_key="key", grpc_module=FakeGrpc(),
            messages_module=FakeMessages, services_module=FakeServices)
        with self.assertRaises(ValueError): list(factory(" ", None))
    def test_converts_chat_events(self):
        snippet = SimpleNamespace(published_at="2026-11-18T10:00:00Z", display_message="hello")
        response = SimpleNamespace(items=[SimpleNamespace(id="event-1", snippet=snippet)])
        events = response_to_chat_events(response, "video-1")
        self.assertEqual(len(events), 1)
        self.assertEqual((events[0].event_id,events[0].source_id,events[0].text),("event-1","video-1","hello"))

if __name__ == "__main__": unittest.main()
