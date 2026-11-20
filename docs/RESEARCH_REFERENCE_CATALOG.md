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
