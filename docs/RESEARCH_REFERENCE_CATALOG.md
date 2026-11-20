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

## 2026-11-20 live metadata and README/license revalidation (ARO-CHAT-0028)

The following counts are GitHub API observations retrieved during the 13:15 IST audit on 2026-11-20. Counts are time-sensitive and are not quality scores.

| Repository | Stars | Forks | Default branch | Latest push observed (UTC) | GitHub license metadata |
|---|---:|---:|---|---|---|
| [OpenShorts](https://github.com/mutonby/openshorts) | 9,421 | 1,976 | `main` | 2026-11-20 00:17:50 | MIT |
| [AI YouTube Shorts Generator](https://github.com/Anil-matcha/AI-Youtube-Shorts-Generator) | 6,342 | 1,156 | `main` | 2026-11-12 13:36:13 | MIT |
| [Auto-Editor](https://github.com/WyattBlue/auto-editor) | 6,016 | 750 | `master` | 2026-11-20 05:26:33 | Unlicense |
| [Remotion](https://github.com/remotion-dev/remotion) | 74,439 | 6,312 | `main` | 2026-11-19 16:36:01 | NOASSERTION (repository uses `LICENSE.md`) |

### Files rechecked in this session

- OpenShorts: repository metadata, `README.md`, `LICENSE`. README describes a Python/Docker self-hosted workflow, separate hosted cloud offering, face-tracked reframing and an API/MCP surface. The core MIT license does not override the separate commercial license applying to `cloud/`; no cloud code is approved for reuse by this audit.
- AI YouTube Shorts Generator: repository metadata, `README.md`, `LICENSE`. README describes API mode via MuAPI and local mode using `yt-dlp`, `faster-whisper`, FFmpeg and OpenCV. MIT applies to repository code, but the URL downloader is not an approved THE ARO acquisition adapter. Prefer only the pluggable scoring, transcript chunking and overlap-deduplication ideas.
- Auto-Editor: repository metadata, `README.md`, `LICENSE`. Nim CLI with audio-threshold and motion-based editing; Unlicense text dedicates the code to the public domain. README separately notes proprietary assets for its online/app offerings. Do not add Nim as a runtime dependency; use audio/motion only as optional candidate signals.
- Remotion: repository metadata, `README.md`, `LICENSE.md`. React/TypeScript programmatic video framework with reusable components, Player and batch/server rendering. The current Free License allows individuals and for-profit organizations with up to three employees (as well as listed non-profit/evaluation cases) to create videos commercially; other for-profit organizations require a Company License. The license also restricts using Remotion code to create a derivative product for sale/rent/licensing/sublicensing. Legal eligibility must be checked before any adoption.

### Updated engineering decisions

- OpenShorts: STUDY ONLY. Revisit its analysis/render separation and layout reasoning after the first authorized MP4.
- AI YouTube Shorts Generator: ADAPT IDEAS ONLY. Do not import its URL acquisition path or rely on hosted API behavior.
- Auto-Editor: STUDY ONLY. Its audio/motion labels may be optional signals; silence is not semantic evidence of a low-value gameplay moment.
- Remotion: STUDY ONLY / LICENSE REVIEW REQUIRED. No dependency or source code adopted.
- No third-party source code copied and no dependency added during this revalidation.
