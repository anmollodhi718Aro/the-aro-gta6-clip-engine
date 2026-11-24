import contextlib,io,json,tempfile,unittest
from datetime import datetime,timezone
from pathlib import Path
from backend.app.cli import analyze_file
from backend.app.detection import DetectorConfig
from backend.app.models import PermissionRecord
from backend.app.registry import SourceRecord,SourceRegistry
class CliTests(unittest.TestCase):
 def write_input(self,root,scopes):
  events=[]
  for bucket in range(4):
   for item in range(9 if bucket==3 else 2):
    sec=bucket*10+item
    events.append({"event_id":f"{bucket}-{item}","source_id":"demo",
      "timestamp":f"2026-11-18T12:00:{sec:02d}+00:00","text":"synthetic"})
  payload={"permission":{"source_id":"demo","granted_by":"fixture","scopes":scopes,
    "granted_at":"2026-11-18T11:59:00+00:00","expires_at":"2026-11-18T13:00:00+00:00"},"events":events}
  path=Path(root)/"input.json"; path.write_text(json.dumps(payload),encoding="utf-8"); return path
 def test_inline_fixture_outputs_review_only_candidates(self):
  with tempfile.TemporaryDirectory() as root:
   src=self.write_input(root,["analyze_chat"]); out=Path(root)/"plan.json"
   with contextlib.redirect_stdout(io.StringIO()): code=analyze_file(src,out,DetectorConfig())
   data=json.loads(out.read_text(encoding="utf-8"))
   self.assertEqual(code,0); self.assertEqual(data["candidate_count"],1)
   self.assertEqual(data["candidates"][0]["status"],"needs_review")
   self.assertTrue(data["candidates"][0]["candidate_id"]); self.assertFalse(data["publishing_enabled"])
 def test_registry_is_authoritative(self):
  with tempfile.TemporaryDirectory() as root:
   src=self.write_input(root,[])
   grant=datetime(2026,11,18,11,59,tzinfo=timezone.utc)
   permission=PermissionRecord("demo","creator",frozenset({"analyze_chat"}),grant)
   registry=Path(root)/"sources.json"
   SourceRegistry(registry).register(SourceRecord("demo","Creator","fixture://ref",permission))
   with contextlib.redirect_stdout(io.StringIO()):
    code=analyze_file(src,Path(root)/"plan.json",DetectorConfig(),registry,"demo")
   self.assertEqual(code,0)
 def test_missing_permission_fails_closed(self):
  with tempfile.TemporaryDirectory() as root:
   src=self.write_input(root,["view_only"]); out=Path(root)/"plan.json"
   with contextlib.redirect_stderr(io.StringIO()): code=analyze_file(src,out,DetectorConfig())
   self.assertEqual(code,2); self.assertFalse(out.exists())
if __name__=="__main__": unittest.main()
