import json,shutil,subprocess,tempfile,unittest
from datetime import datetime,timedelta,timezone
from pathlib import Path
from unittest.mock import patch
from backend.app.models import PermissionRecord
from backend.app.render import RenderError,render_clip
class RenderUnitTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory(); self.folder=Path(self.temp.name)
  self.source=self.folder/"source.mp4"; self.source.write_bytes(b"fixture"); self.output=self.folder/"clip.mp4"
  self.permission=PermissionRecord("s","owner",frozenset({"edit_media"}),datetime.now(timezone.utc)-timedelta(minutes=1))
 def tearDown(self): self.temp.cleanup()
 def render(self,**kw):
  opts={"start_seconds":2,"duration_seconds":12,"rights_confirmed":True,"permission":self.permission}; opts.update(kw)
  return render_clip(self.source,self.output,**opts)
 def test_rights_and_registered_scope_required(self):
  with self.assertRaises(PermissionError): self.render(rights_confirmed=False)
  with self.assertRaises(PermissionError): self.render(permission=None)
  view=PermissionRecord("s","owner",frozenset({"analyze_chat"}),datetime.now(timezone.utc)-timedelta(minutes=1))
  with self.assertRaises(PermissionError): self.render(permission=view)
 def test_invalid_bounds(self):
  for start,duration in [(-1,2),(0,0),(0,181),(float("nan"),3),(0,float("inf"))]:
   with self.assertRaises(ValueError): self.render(start_seconds=start,duration_seconds=duration)
 def test_overwrite_and_same_path(self):
  self.output.write_bytes(b"keep")
  with self.assertRaises(FileExistsError): self.render()
  self.assertEqual(self.output.read_bytes(),b"keep")
  with self.assertRaises(ValueError):
   render_clip(self.source,self.source,start_seconds=0,duration_seconds=5,rights_confirmed=True,permission=self.permission)
 @patch("backend.app.render.os.link")
 @patch("backend.app.render.shutil.which",return_value="/usr/bin/ffmpeg")
 @patch("backend.app.render.subprocess.run")
 def test_concurrent_destination_creation_is_never_overwritten(self,run,_which,link):
  def fake_run(command,**kwargs):
   Path(command[-1]).write_bytes(b"rendered review clip")
   return subprocess.CompletedProcess(command,0,"","")
  def concurrent_creator(_source,destination):
   Path(destination).write_bytes(b"concurrent owner file")
   raise FileExistsError("destination was created concurrently")
  run.side_effect=fake_run
  link.side_effect=concurrent_creator
  with self.assertRaises(RenderError): self.render()
  self.assertEqual(self.output.read_bytes(),b"concurrent owner file")
  self.assertEqual(list(self.folder.glob(".clip.*.mp4")),[])
 @patch("backend.app.render.shutil.which",return_value="/usr/bin/ffmpeg")
 @patch("backend.app.render.subprocess.run")
 def test_safe_argument_list_and_atomic_output(self,run,_which):
  def fake(cmd,**kw): Path(cmd[-1]).write_bytes(b"mp4"); return subprocess.CompletedProcess(cmd,0,"","")
  run.side_effect=fake; self.assertEqual(self.render(),self.output)
  self.assertIsInstance(run.call_args.args[0],list); self.assertFalse(run.call_args.kwargs["shell"])
 @patch("backend.app.render.shutil.which",return_value=None)
 def test_missing_ffmpeg(self,_which):
  with self.assertRaises(RenderError): self.render()
 @patch("backend.app.render.shutil.which",return_value="/usr/bin/ffmpeg")
 @patch("backend.app.render.subprocess.run")
 def test_timeout_cleans_temp(self,run,_which):
  def fake(cmd,**kw): Path(cmd[-1]).write_bytes(b"partial"); raise subprocess.TimeoutExpired(cmd,kw["timeout"])
  run.side_effect=fake
  with self.assertRaises(RenderError): self.render()
  self.assertEqual(list(self.folder.glob(".clip.*.mp4")),[])
@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),"FFmpeg/FFprobe unavailable")
class RenderE2E(unittest.TestCase):
 def test_synthetic_animation_render_and_probe(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder); source=root/"synthetic.mp4"; output=root/"clip.mp4"
   made=subprocess.run([shutil.which("ffmpeg"),"-hide_banner","-loglevel","error","-f","lavfi","-i","testsrc2=size=160x120:rate=15","-t","3","-pix_fmt","yuv420p","-c:v","libx264","-y",str(source)],capture_output=True,text=True,timeout=60,shell=False)
   self.assertEqual(made.returncode,0,made.stderr)
   permission=PermissionRecord("synthetic","fixture",frozenset({"edit_media"}),datetime.now(timezone.utc)-timedelta(minutes=1))
   render_clip(source,output,start_seconds=.5,duration_seconds=1,rights_confirmed=True,permission=permission)
   probe=subprocess.run([shutil.which("ffprobe"),"-v","error","-show_entries","format=duration","-of","json",str(output)],capture_output=True,text=True,timeout=30,shell=False)
   self.assertEqual(probe.returncode,0,probe.stderr)
   duration=float(json.loads(probe.stdout)["format"]["duration"])
   self.assertGreaterEqual(duration,.8); self.assertLessEqual(duration,1.3); self.assertGreater(output.stat().st_size,0)
if __name__=="__main__": unittest.main()
