# ARO-CHAT-0163 | Stickman Video Director Integration Presentation

Date: 2026-11-24

## Decision

**Recommendation: adopt as an optional pre-production companion, not as a core renderer dependency.**

Upstream project: https://github.com/kaomei/stickman-video-director

The upstream repository is a script-to-storyboard / animated-explainer workflow. Its Director Mode produces a treatment, storyboard, scene prompts, and sound design for manual clip generation/editing. Its Autopilot Mode can assemble illustrated scenes, narration, captions, and sound effects when a compatible agent, generation services, and local rendering environment are available.

This complements THE ARO's original-commentary/content-pack workflow. It does not replace the GTA 6 engine's authorized local recording, candidate review, FFmpeg/FFprobe rendering, source-rights registry, or channel-owner upload approval.

## Fit with the existing project

The canonical project handoff describes a local-first workflow: authorized chat analysis, candidate review, rendering from locally supplied authorized media, preview/review, explicit owner approval, and separately authorized upload preparation. It explicitly does not download or rip livestream video.

The Stickman Director should therefore be used only for original explanatory/commentary videos such as:
- GTA 6 update explainers written in THE ARO's own words;
- feature/tutorial walkthroughs using original diagrams and stickman scenes;
- short context videos that lead into a separately reviewed gameplay clip.

It must not be treated as a source of GTA 6 gameplay footage, a livestream downloader, or a way to bypass source-media permission checks.

## Recommended integration boundary

### Phase 1 — Director Mode only (lowest-risk proof of concept)

1. Start with a short, original THE ARO script and a 30-second landscape storyboard.
2. Use Director Mode to produce a treatment, shot list, camera/action prompts, and sound-design notes.
3. Manually generate or assemble the scene assets using services already approved by the project owner.
4. Export a local MP4 and pass it through the existing FFprobe/render-review workflow.
5. Keep the result in the existing local review state. Do not auto-upload or publish.

Director Mode is the best first experiment because it preserves scene-by-scene human control and avoids introducing the upstream Autopilot runtime into the main application.

### Phase 2 — optional adapter after the proof of concept

If the first experiment is useful, add a small adapter that accepts a project-owned script/storyboard manifest and records:
- script ID and version;
- scene order and durations;
- prompt text and visual-style identifier;
- generated asset paths and hashes;
- audio/voice asset paths and hashes;
- third-party license/evidence references;
- output MP4 path and FFprobe metadata;
- human review decision.

The adapter should produce a manifest and local assets only. The existing engine remains responsible for rights preflight, local render validation, review state, and any later upload approval.

### Phase 3 — Autopilot evaluation (not part of the initial implementation)

Evaluate only after Phase 1 proves useful. The upstream README states that Autopilot requires an agent environment with file access and command execution, image-generation and voiceover services, and a local rendering setup. The upstream documentation lists Node.js 20+ and FFmpeg for its Code Engine runtime, Python with Pillow and NumPy for helpers, and OpenCV for some optional tools.

These services may carry separate costs. The upstream Skill being open source does not mean image, voice, or video generation services are included in a ChatGPT subscription or free of charge.

## Licensing and supply-chain controls

- The upstream repository declares the MIT License. If source files or substantial portions are copied or distributed, preserve the original copyright and license notice.
- Third-party images, music, sound effects, voices, fonts, and generated assets may have separate terms. The upstream README explicitly says these are not covered automatically by its MIT license.
- Before any code is vendored: pin an exact upstream commit, inspect its complete license and asset notices, review its dependency manifest and install scripts, run its tests in isolation, and record a software-bill-of-materials/license note.
- Do not add the upstream project as a mandatory runtime dependency. Do not commit API keys, OAuth tokens, generated private media, or paid-service credentials.

## Non-goals and safety gates

- No scraping, stream ripping, or remote video extraction.
- No use of third-party GTA 6 footage without documented permission.
- No automatic upload, public publishing, or background publishing.
- No weakening of source-rights, per-clip approval, channel-owner identity, or current-permission checks.
- No import of the upstream Autopilot code into the core application during the initial phase.
- No claims that a stickman animation is actual GTA 6 gameplay.

## Acceptance criteria for Phase 1

- One original 30-second 16:9 script and scene-by-scene treatment.
- A human-approved storyboard before any paid generation or full asset run.
- All assets have known origins and license/evidence notes.
- A local MP4 is generated without using unauthorized game footage.
- Existing FFprobe validation passes and the local review record remains pending human approval.
- No YouTube upload or public publishing is attempted.

## Source references

- Upstream repository and workflow overview: https://github.com/kaomei/stickman-video-director
- Upstream MIT license: https://github.com/kaomei/stickman-video-director/blob/main/LICENSE
- Upstream README describes Director Mode, Autopilot Mode, required tools, and third-party asset licensing.
- Project-local baseline: docs/PROJECT_HANDOFF.md and README.md.

## Status

- Proposal only; no upstream source code, assets, dependencies, or runtime behavior have been added.
- Local tests: NOT RUN; this change is documentation-only.
- Next step after owner review: run one manual Director Mode storyboard experiment before considering any adapter or Autopilot integration.
