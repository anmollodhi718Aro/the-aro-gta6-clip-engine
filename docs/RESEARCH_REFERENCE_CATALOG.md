# Research Reference Catalog

**Canonical file:** `docs/RESEARCH_REFERENCE_CATALOG.md`  
**Last checked:** 2026-11-20 (UTC date; GitHub and project documentation snapshots)  
**Owner:** THE ARO  
**Current workstream:** ARO-ZERO-ONE

This catalog records engineering observations, not endorsements. Stars/forks are approximate display counts observed on GitHub on the check date. Repository source paths and license files were inspected through the connected GitHub repository interface. No external source code was copied into THE ARO.

## 1. OpenShorts

- **Repository:** https://github.com/mutonby/openshorts
- **Default branch:** `main`
- **Stars / forks:** approximately 5.6k / 1.3k (GitHub display, 2026-11-20)
- **License:** MIT for core application. The `cloud/` directory has a separate OpenShorts Commercial License; do not treat the whole tree as MIT.
- **Latest commit observed:** `b3cd947bc48ad1fc8093bb8f8291b9fb02e9bb2f` (2026-11-19T20:08:43Z); no GitHub releases were returned by the releases endpoint; open issues are active (first page included #197 through #193).
- **Files inspected:** `README.md`, `LICENSE`, `clip_selection.py`, `reframe_v2.py`, `quality_probe.py`, `ffmpeg_utils.py`, `docker-compose.yml`.
- **Architecture observations:** Python backend and dashboard are split into Docker Compose services; a dedicated renderer service is present. Clip selection is separated into pure helpers. Reframing has a low-resolution analysis pass followed by FFmpeg-native rendering, scene segmentation and concatenation. FFmpeg encoder selection is centralized. Quality probing and UI/review/editor modules are distinct.
- **Useful ideas:** explicit analysis/render boundaries; face/speaker tracking and scene-aware layouts; centralized encoder policy; independent renderer service; quality preflight; editable clip review.
- **Risks / limitations:** broad, comparatively large system with GPU/cloud/hosted concerns; dependencies and deployment complexity exceed the immediate local-first milestone. `cloud/` license exception must be respected. Any remote media adapter must not be copied into THE ARO unless its source authorization model matches THE ARO's explicit permission rules.
- **Decision:** **STUDY ONLY** for now. Revisit small, isolated ideas (especially analysis/render separation and explainable layout decisions) after first verified local MP4. Do not import the whole application or its cloud service.

## 2. AI YouTube Shorts Generator

- **Repository:** https://github.com/Anil-matcha/AI-Youtube-Shorts-Generator
- **Default branch:** `main`
- **Stars / forks:** approximately 6.1k / 1.1k (GitHub display, 2026-11-20)
- **License:** MIT (LICENSE inspected).
- **Latest commit observed:** `1142a747b0056da5551970e88ca9f1ec85deafc5` (2026-11-12T13:36:12Z); no GitHub releases were returned; open issues are active (first page included #92 through #88).
- **Files inspected:** `README.md`, `LICENSE`, `shorts_generator/highlights.py`, `shorts_generator/pipeline.py`, `shorts_generator/local/llm.py`, `shorts_generator/local/clipper.py`.
- **Architecture observations:** Python pipeline with API and local modes; transcript-based LLM highlight selection; pluggable LLM function; local transcription and cropping components; highlight ranking/deduplication; OpenCV face-aware vertical crop. The default API path delegates processing to MuAPI. The local path includes a YouTube downloader component.
- **Useful ideas:** provider-neutral LLM function contract; structured candidate scores and short reasons; overlap suppression; transcript chunking for long recordings; separate transcription, highlight selection and crop stages.
- **Risks / limitations:** API mode is externally hosted and usage-dependent. Local path includes URL-based YouTube acquisition/downloading, which is not an approved acquisition route for THE ARO by default. Highlight quality/virality claims are not evidence of performance on GTA gameplay. The current README mentions third-party API providers and model costs that require independent verification before adoption.
- **Decision:** **ADAPT IDEAS ONLY** after first MP4. Consider transcript-to-candidate scoring interfaces and dedupe logic using authorized local recordings; do not import its downloader or assume its API mode satisfies creator permissions.

## 3. Auto-Editor

- **Repository:** https://github.com/WyattBlue/auto-editor
- **Default branch:** `master`
- **Stars / forks:** approximately 5.8k / 726 (GitHub display, 2026-11-20)
- **License:** Unlicense / public-domain dedication (LICENSE inspected).
- **Latest commit observed:** `f93867c2adc895bca9406b55b5a50259c5194df4` (2026-11-20T01:24:28Z); latest stable release observed: `31.9.0` (2026-11-13); no open issues were returned by the issues endpoint.
- **Files inspected:** `README.md`, `LICENSE`, `src/analyze/audio.nim`, `src/analyze/motion.nim`, `src/edit.nim`.
- **Architecture observations:** Nim command-line editor; analysis methods include audio loudness, motion, black-frame and subtitle analysis; edit expressions combine analysis labels with timeline actions; supports exports to common editing applications.
- **Useful ideas:** optional audio/motion analysis as candidate features; silence/gap detection; configurable thresholds and margins; explainable analysis labels.
- **Risks / limitations:** Nim implementation and native media-processing stack are not drop-in Python components. Automatic silence removal is not a substitute for semantic highlight detection and could cut important gameplay audio or reactions.
- **Decision:** **STUDY ONLY**. If needed later, prototype a small, separately tested audio/motion signal adapter that emits candidate metadata; preserve original media and never auto-delete content.

## 4. Remotion

- **Repository:** https://github.com/remotion-dev/remotion
- **Default branch:** `main`
- **Stars / forks:** approximately 71.9k / 6.0k (GitHub display, 2026-11-20)
- **License:** Remotion's main software uses a special proprietary license, not an OSI open-source license. Individuals and qualifying organizations of up to 3 people may qualify for the Free License; other company use requires a Company License. Automation/rendering products have separate pricing/terms. Confirm eligibility and current terms before any production use.
- **Latest commit observed:** `d6cac5559dcf6ff52c7aa7a288f5d9394fa3c54e` (2026-11-19T16:35:58Z); latest stable release observed: `v4.0.545` (2026-11-18); open issues are active (first page included #13546 through #13540).
- **Files inspected:** `README.md`, `LICENSE.md`, `packages/renderer/package.json`, `packages/player/package.json`, `packages/captions/package.json`.
- **Architecture observations:** React/TypeScript programmatic video framework with separate renderer, Player, captions, Studio, and cloud/lambda packages. Renderer uses Node/Bun and has native compositor packages; Player embeds preview in React; captions package is independently MIT licensed.
- **Useful ideas:** template-driven title/caption overlays; reusable motion components; in-app preview/player; explicit rendering abstraction.
- **Risks / limitations:** main framework license is conditional and not MIT. Renderer has native package/runtime dependencies and requires a Node/Bun toolchain; this would introduce a second media-rendering stack beside FFmpeg. Separate packages can carry different license declarations (for example, captions package MIT).
- **Decision:** **STUDY ONLY / DEFER**. Do not introduce Remotion into the P0 renderer. Re-evaluate only for a later Studio motion-template feature after licensing, bundle/runtime, and cost analysis.

## Cross-reference conclusion

1. **Do not replace the existing FFmpeg renderer.** The selected ARO-ZERO-ONE branch already has local rendering, no-overwrite publication, and FFprobe validation.
2. **Keep acquisition, analysis, render, review, and publishing authorization as separate boundaries.**
3. **No third-party code or dependencies were adopted by this research task.**
4. **No benchmark was run against THE ARO media pipeline.** Repository popularity and external claims do not establish performance or compatibility.
5. **Next useful engineering task:** run the existing local Windows wizard against an authorized sample recording, then validate the resulting MP4 with FFprobe and playback. After that, select one small highlight-scoring improvement backed by synthetic tests.

## Evidence links

- OpenShorts README: https://github.com/mutonby/openshorts/blob/main/README.md
- OpenShorts LICENSE: https://github.com/mutonby/openshorts/blob/main/LICENSE
- AI YouTube Shorts Generator README: https://github.com/Anil-matcha/AI-Youtube-Shorts-Generator/blob/main/README.md
- AI YouTube Shorts Generator LICENSE: https://github.com/Anil-matcha/AI-Youtube-Shorts-Generator/blob/main/LICENSE
- Auto-Editor README: https://github.com/WyattBlue/auto-editor/blob/master/README.md
- Auto-Editor LICENSE: https://github.com/WyattBlue/auto-editor/blob/master/LICENSE
- Remotion README: https://github.com/remotion-dev/remotion/blob/main/README.md
- Remotion LICENSE: https://github.com/remotion-dev/remotion/blob/main/LICENSE.md
- Remotion licensing/pricing: https://www.remotion.dev/docs/license/pricing


## ARO-CHAT-0022 research revalidation snapshot — 2026-11-20

Live GitHub REST metadata and raw README/LICENSE/source files were rechecked for the four priority references. Counts below are point-in-time GitHub values, not quality scores.

| Reference | Stars | Forks | Open issues | Last push (UTC) | License metadata | Source files inspected in this recheck | Decision |
|---|---:|---:|---:|---|---|---|---|
| [OpenShorts](https://github.com/mutonby/openshorts) | 9,421 | 1,976 | 80 | 2026-11-20 00:17:50 | MIT repo metadata; README/license/source inspected | `README.md`, `LICENSE`, `clip_selection.py`, `reframe_v2.py` | STUDY ONLY; preserve the cloud/ directory's separate commercial-license exception recorded above |
| [AI YouTube Shorts Generator](https://github.com/Anil-matcha/AI-Youtube-Shorts-Generator) | 6,341 | 1,156 | 33 | 2026-11-12 13:36:13 | MIT | `README.md`, `shorts_generator/highlights.py`, `LICENSE` | ADAPT IDEAS ONLY; its README advertises MuAPI and its source has an API/local split; do not adopt URL-downloader acquisition into THE ARO |
| [Auto-Editor](https://github.com/WyattBlue/auto-editor) | 6,016 | 750 | 0 | 2026-11-20 05:26:33 | Unlicense | `README.md`, `LICENSE` | STUDY ONLY; audio/motion cut signals are optional candidate metadata, not semantic highlight truth |
| [Remotion](https://github.com/remotion-dev/remotion) | 74,438 | 6,311 | 207 | 2026-11-19 16:36:01 | GitHub API reports NOASSERTION; inspect the repository's own special `LICENSE.md` | `README.md`, `LICENSE.md` | STUDY ONLY; free-license eligibility is conditional and some company use requires a Company License; do not adopt until licensing/architecture is reviewed |

### Engineering conclusions from source inspection
- OpenShorts' `reframe_v2.py` explicitly separates a low-resolution analysis pass from FFmpeg-native scene rendering and concatenation. This is a useful future architecture reference, but the current THE ARO local FFmpeg renderer should remain the P0 path until the first authorized MP4 is accepted.
- OpenShorts' README describes a Python/FastAPI + React/Vite + Docker stack and publishing integrations. Its `cloud/` license exception remains a material boundary; do not treat every directory as MIT merely because the core license is MIT.
- AI YouTube Shorts Generator's `highlights.py` exposes a pluggable LLM function and separates transcript chunking, highlight scoring and overlap suppression. These are useful design ideas for later authorized-local-media analysis. Its default hosted API and URL-based acquisition path are not approved THE ARO source adapters.
- Auto-Editor is a Nim CLI centered on audio loudness and motion-based editing. It is not a drop-in Python dependency. Silence/motion should be optional signals because they can remove meaningful game audio or reactions.
- Remotion's repository-level GitHub license metadata is `NOASSERTION`; the project's own `LICENSE.md` defines a special Free License for individuals and qualifying small organizations and a Company License for others. Recheck legal eligibility before commercial adoption. No dependency was added.
- No external source code was copied and no dependency was introduced during this research recheck.


## ARO-CHAT-0034 live research revalidation — 2026-11-20

This is a point-in-time refresh of the existing four-reference research record. GitHub REST repository metadata, README, license files and selected implementation files were inspected through the GitHub connector. Counts are snapshots, not quality measures. No external source code was copied and no dependency was added.

| Reference | Stars | Forks | Open issues | Last push (UTC) | GitHub license metadata | Decision |
|---|---:|---:|---:|---|---|---|
| [OpenShorts](https://github.com/mutonby/openshorts) | 9,488 | 1,998 | 81 | 2026-11-20 16:36:37 | MIT (core; cloud/ exception) | STUDY ONLY |
| [AI YouTube Shorts Generator](https://github.com/Anil-matcha/AI-Youtube-Shorts-Generator) | 6,353 | 1,160 | 33 | 2026-11-12 13:36:13 | MIT | ADAPT IDEAS ONLY |
| [Auto-Editor](https://github.com/WyattBlue/auto-editor) | 6,022 | 754 | 0 | 2026-11-20 15:32:41 | Unlicense | STUDY ONLY |
| [Remotion](https://github.com/remotion-dev/remotion) | 74,542 | 6,333 | 192 | 2026-11-20 16:46:29 | NOASSERTION at repository level; special license file | STUDY ONLY / DEFER |

### OpenShorts

- **Files inspected:** README.md, LICENSE, docker-compose.yml, clip_selection.py, reframe_v2.py, quality_probe.py, and render-service source inventory (bundle.ts, composition-metadata.test.ts, render-worker.ts, server.ts).
- **Architecture verified:** Docker Compose separates backend, dashboard and renderer services. reframe_v2.py performs a low-resolution (up to 640px) analysis pass, then uses FFmpeg-native scene rendering and concatenation; it maps source audio into rendered scenes. Clip selection helpers are standard-library-only and isolate some ranking logic.
- **Useful ARO ideas:** keep analysis and rendering separate; model scene-level layout decisions as explicit data; centralize renderer orchestration; keep candidate selection helpers deterministic and testable; probe output quality before review.
- **Risks:** the system is much larger than the local-first MVP and includes GPU, hosted, cloud, downloader and publishing surfaces. The README/license distinguish the core MIT application from the separately commercially licensed cloud/ directory. URL-based source handling and autopublishing must not be adopted as default ARO behavior.
- **Decision:** STUDY ONLY. Revisit a small, provider-neutral analysis/render boundary after first authorized MP4. Do not import the full application or cloud directory.

### AI YouTube Shorts Generator

- **Files inspected:** README.md, LICENSE, shorts_generator/highlights.py, shorts_generator/pipeline.py, shorts_generator/clipper.py, and requirements.txt.
- **Architecture verified:** separate transcription, highlight generation and crop stages; API and local execution paths; injectable LLM function; transcript chunking; structured score, hook and reason fields; local crop path uses OpenCV while API mode delegates crop to MuAPI.
- **Useful ARO ideas:** provider-neutral highlight scorer interface; structured candidate explanations; transcript chunking; overlap/deduplication; explicit candidate result model.
- **Risks:** default API mode requires a third-party service; local mode includes YouTube URL acquisition/downloading. Neither API claims nor viral scores establish performance on GTA gameplay. THE ARO authorization model requires a user-owned or creator-authorized local media handoff.
- **Decision:** ADAPT IDEAS ONLY. Consider scoring/deduplication concepts for authorized local recordings; do not adopt downloader or hosted acquisition path.

### Auto-Editor

- **Files inspected:** README.md, LICENSE, src/edit.nim, src/analyze/audio.nim, and src/analyze/motion.nim.
- **Architecture verified:** Nim-based CLI; analysis/edit expression pipeline; audio loudness and frame-motion signals; SIMD implementations in analysis modules; configurable active/inactive timeline actions and margins; export to editing timelines.
- **Useful ARO ideas:** optional audio/motion feature signals, configurable thresholds, deterministic signal extraction and explainable labels.
- **Risks:** native Nim/libav implementation is not a drop-in Python dependency. Silence or motionlessness is not semantic importance and can remove meaningful gameplay audio, dialogue or reaction moments.
- **Decision:** STUDY ONLY. If later justified, build a small independent signal adapter that emits metadata only; never auto-delete or trim original source content based solely on silence.

### Remotion

- **Files inspected:** README.md, LICENSE.md, packages/renderer/package.json, packages/player/package.json, and packages/captions/package.json.
- **Architecture verified:** React/TypeScript programmatic video framework with separate renderer and Player packages; renderer targets Node.js or Bun and depends on execa, WebSocket support and platform-specific native compositor packages. Player embeds previews in React. The captions package declares MIT independently.
- **License finding:** repository metadata is NOASSERTION; renderer and Player package metadata refer to LICENSE.md, which sets a special Free License for individuals and qualifying small organizations and requires a Company License for others. The captions package is separately MIT. Eligibility must be checked against the actual intended legal entity and use case.
- **Useful ARO ideas:** reusable caption/motion templates and an embeddable preview player for a later Studio layer.
- **Risks:** adding Remotion renderer introduces Node/Bun and native compositor dependencies beside the existing FFmpeg pipeline, plus a conditional license. Package-level licenses differ.
- **Decision:** STUDY ONLY / DEFER. Do not add the renderer to P0. Revisit only for a later Studio template feature after architecture and license review; evaluate captions independently if needed.

### Integration conclusion

1. Keep the current FFmpeg renderer as the P0 rendering path; no external project justifies replacing it before first authorized MP4 acceptance.
2. Preserve independent authorization boundaries for source acquisition and destination publishing.
3. The only low-risk concepts worth carrying forward are explainable candidate scoring, deduplication, optional audio/motion signals, explicit analysis/render separation and a future preview-player pattern.
4. No dependencies, external source code or publishing integrations were adopted in this research task.
5. No ARO media benchmark or compatibility test was run; repository metrics are not performance evidence.
6. Highest-value next engineering work remains an authorized local sample render, FFprobe verification (video + audio, dimensions, duration) and playback review. The real GTA 6 milestone remains blocked until an authorized recording/export is supplied.
