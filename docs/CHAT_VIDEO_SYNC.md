# Chat/video clock synchronization

The chat detector emits UTC timestamps, while FFmpeg needs offsets relative to a local media file. Never assume the clocks match.

The synchronization convention is: chat time = media time + chat_minus_media_seconds. Therefore media offset = chat timestamp - media start timestamp - measured offset.

The ClockSync record requires a finite measured offset, a timezone-aware measurement timestamp, a method description, and nonnegative uncertainty. The default accepted uncertainty is at most 2 seconds. An estimate without a measurement is not acceptable.

candidate_media_bounds converts the candidate's pre/post-roll interval, clamps it to the media duration, and rejects empty, out-of-range, overlong, or excessively uncertain mappings. render_candidate passes those local offsets to the existing rights-gated, no-overwrite FFmpeg renderer.

Example values must come from a real synchronization measurement and actual media metadata. This module does not download streams, infer synchronization, bypass creator consent, or publish clips.
