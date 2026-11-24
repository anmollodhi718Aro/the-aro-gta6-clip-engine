import tempfile,unittest
from datetime import datetime,timezone
from pathlib import Path
from backend.app.review import ReviewLedger
class ReviewTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(); self.path=Path(self.tmp.name)/"reviews.json"; self.ledger=ReviewLedger(self.path)
 def tearDown(self): self.tmp.cleanup()
 def test_append_and_reload(self):
  now=datetime.now(timezone.utc); saved=self.ledger.record("c1","s1","approved","reviewer",now,"checked")
  self.assertEqual(ReviewLedger(self.path).get("c1"),saved)
 def test_one_final_decision_only(self):
  now=datetime.now(timezone.utc); self.ledger.record("c1","s1","rejected","reviewer",now)
  with self.assertRaises(ValueError): self.ledger.record("c1","s1","approved","reviewer",now)
 def test_reject_invalid_decision_and_reviewer(self):
  now=datetime.now(timezone.utc)
  with self.assertRaises(ValueError): self.ledger.record("c1","s1","published","reviewer",now)
  with self.assertRaises(ValueError): self.ledger.record("c2","s1","approved"," ",now)
if __name__=="__main__": unittest.main()
