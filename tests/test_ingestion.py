import unittest
from datetime import datetime,timedelta,timezone
from backend.app.ingestion import normalize_event_batch
from backend.app.models import PermissionRecord
class IngestionTests(unittest.TestCase):
 def setUp(self):
  self.start=datetime(2026,11,18,12,0,tzinfo=timezone.utc)
  self.permission=PermissionRecord("s","owner",frozenset({"analyze_chat"}),self.start-timedelta(minutes=1),self.start+timedelta(hours=1))
 def event(self,eid,seconds,text="hello"):
  return {"event_id":eid,"source_id":"s","timestamp":(self.start+timedelta(seconds=seconds)).isoformat(),"text":text}
 def test_sort_deduplicate_and_utc(self):
  events=normalize_event_batch([self.event("b",12),self.event("a",2),self.event("a",2)],self.permission)
  self.assertEqual([x.event_id for x in events],["a","b"]); self.assertEqual(events[0].timestamp.tzinfo,timezone.utc)
 def test_conflicting_duplicate_rejected(self):
  with self.assertRaises(ValueError): normalize_event_batch([self.event("x",2),self.event("x",3)],self.permission)
 def test_wrong_source_and_expired_permission_rejected(self):
  item=self.event("x",2); item["source_id"]="wrong"
  with self.assertRaises(ValueError): normalize_event_batch([item],self.permission)
  with self.assertRaises(PermissionError): normalize_event_batch([self.event("late",3601)],self.permission)
 def test_batch_text_and_timestamp_limits(self):
  with self.assertRaises(ValueError): normalize_event_batch([self.event("x",2)],self.permission,max_events=0)
  with self.assertRaises(ValueError): normalize_event_batch([self.event("x",2,"123456")],self.permission,max_text_length=5)
  item=self.event("x",2); del item["timestamp"]
  with self.assertRaises(ValueError): normalize_event_batch([item],self.permission)
if __name__=="__main__": unittest.main()
