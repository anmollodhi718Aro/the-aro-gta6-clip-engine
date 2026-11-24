import tempfile,unittest
from datetime import datetime,timedelta,timezone
from pathlib import Path
from backend.app.models import PermissionRecord
from backend.app.registry import SourceRecord,SourceRegistry
class RegistryTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(); self.path=Path(self.tmp.name)/"nested"/"sources.json"
  now=datetime.now(timezone.utc); p=PermissionRecord("src","owner",frozenset({"analyze_chat","edit_media"}),now-timedelta(minutes=1),now+timedelta(hours=1))
  self.record=SourceRecord("src","Synthetic Creator","fixture://permission",p)
  self.registry=SourceRegistry(self.path)
 def tearDown(self): self.tmp.cleanup()
 def test_round_trip_and_active_scope(self):
  self.registry.register(self.record)
  self.assertEqual(SourceRegistry(self.path).get("src"),self.record)
  self.assertEqual(self.registry.require("src","edit_media",datetime.now(timezone.utc)),self.record)
 def test_duplicate_and_missing_scope_fail(self):
  self.registry.register(self.record)
  with self.assertRaises(ValueError): self.registry.register(self.record)
  with self.assertRaises(PermissionError): self.registry.require("src","publish",datetime.now(timezone.utc))
 def test_revocation_persists(self):
  self.registry.register(self.record); at=datetime.now(timezone.utc); self.registry.revoke("src",at)
  with self.assertRaises(PermissionError): self.registry.require("src","edit_media",at+timedelta(seconds=1))
 def test_mismatched_permission_source_rejected(self):
  p=PermissionRecord("other","owner",frozenset({"edit_media"}),datetime.now(timezone.utc))
  with self.assertRaises(ValueError): SourceRecord("src","Creator","ref",p)
 def test_corrupt_json_rejected(self):
  self.path.parent.mkdir(parents=True); self.path.write_text("{bad",encoding="utf-8")
  with self.assertRaises(ValueError): self.registry.list_sources()
if __name__=="__main__": unittest.main()
