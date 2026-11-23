# Local Clip Rendering

The local renderer accepts only an operator-supplied file path. It does not fetch streams, download media, access platform APIs, or publish output.

## Requirements

- Python 3.11+
- FFmpeg and FFprobe installed on the local machine
- A permission JSON record with the matching source_id, a current grant, and the clip_media scope
- Media that the operator owns or is explicitly authorized to edit, with separate third-party rights checked
- A reviewed start time and duration

## Example

Create a permission record:

~~~json
{
  "source_id": "my-authorized-recording",
  "granted_by": "creator-owner",
  "scopes": ["clip_media"],
  "granted_at": "2026-11-24T00:00:00+00:00",
  "expires_at": "2026-11-25T00:00:00+00:00"
}
~~~

Run from the repository root:

~~~bash
python -m backend.app.render_cli ./owned-recording.mp4 \
  --permission-json ./permission.json \
  --source-id my-authorized-recording \
  --start-seconds 30 \
  --duration-seconds 20 \
  --output ./review-clip.mp4 \
  --confirm-local-render
python -m unittest discover -s tests -v
~~~

The renderer fails closed if confirmation or clip_media permission is absent, source IDs differ, timestamps are invalid, the output already exists, or FFmpeg/FFprobe validation fails. The requested duration is capped at 10 minutes. Rendering occurs in a private temporary directory beside the destination. The validated result is published to the requested local path with an atomic create-if-absent operation, so a concurrent writer's file is never overwritten or removed. Output is local and requires human review; publishing remains out of scope.

Use synthetic fixtures for automated tests. Do not commit private recordings, access tokens, or permission evidence containing personal information.
