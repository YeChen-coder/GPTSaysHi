# Shared streaming, separate character rendering

Current approved QinChe integration: October 17, 2026. This replaces the rejected
October 12 QinChe visual model and all its appearance patches. Gentleman keeps
its own October 4 rendering profile and resources.

## Character profiles

| Item | Approved QinChe | Gentleman |
| --- | --- | --- |
| Visual model | Clean random-start epoch 100 | October 4 selected checkpoint |
| Checkpoint SHA-256 | `7c44912c27f52ff84fdc632c63446d9a835c6aa1915c1ecb7d2a0251786feace` | `205e908f2e9ae8364417110d14f35c856ead742a0dd6c5b1a6388b5da507715d` |
| Reference timeline | 251 unique frames, `0..250,249..1`, 500 playback frames | Existing 500-frame expanded reference |
| Selected source | Natural listening take 1 | Existing selected candidate 1 |
| Composition | Supplied `NativeFaceMatch`, unchanged | Existing soft lower-face blend |
| Teeth | Model-generated | Same-person donor restoration |
| Detail/chin | Original native face, no overlays/sharpening | Matched chin cache and local sharpening |
| End of speech | Direct native idle; no extra settling or viewer crossfade | Existing ten-frame / 400 ms residual settling |

`characters.json` stores each profile and its settings. The factory in
`runtime/engine_runtime.py` loads one selected visual model. QinChe uses
`engine/native_loop_core.py`; Gentleman uses `engine/loop_core.py`. Global legacy
teeth/detail settings cannot add Gentleman or rejected QinChe patches to the
native profile. Retired assets are not exposed as a selectable character.

## Approved mouth composition

The supplied `runtime/native_face_match.py` is copied without algorithm changes.
Its SHA-256 is
`4c763464098d1a02e5668527c50ecc36575bf6709e452294d9e645da4bc06d60`.
The 110-point geometry uses lips 90..109 and nose 51..65. Masks, references and
native ROIs are prepared once for all 251 unique frames. Online composition
uses the same source index for model input, landmarks, mask and native pixels.

Only the local mouth support is composited at native resolution. The center
contains the generated mouth, without blending in the source's closed mouth.
The surrounding color field uses 0.8 previous / 0.2 current field and resets for
each independent speech session. No future frames are used by this correction.
It is color matching, not mouth-motion smoothing.

The supplied approved prediction sequences reproduce 750 protected-pixel
checks and seven approved full-frame PNGs exactly, before encoding. JPEG and
MP4 compression do not preserve pixel equality. Live audio encoding is still a
bounded-window approximation; these reproduction checks isolate composition
and do not claim every live prediction is identical to an offline export.

## Shared engineering retained

- One persistent model/encoder; contiguous NCHW reference inputs cached on GPU.
- Silence-based visual/audio warmup over the actual streaming shapes, before
  service readiness. It is not repeated for every sentence.
- Four-CPU container limit, Torch/OpenCV thread control and bounded histories.
- Existing timestamp plus mono 24 kHz PCM16 input, continuous 24-to-16 kHz
  resampling and filter-tail flush. The FIR holds about 1.33 ms of input; fast
  mode adds zero future-feature frames, not absolute zero delay.
- About four seconds of encoder history and clearing diagnostic lists, without
  storing predictions or per-frame review records in the online service.
- Immediate publication from one worker per packet through a capacity-two
  queue, exception forwarding and joined cancellation/cleanup.
- Renderer ownership lock and latest-explicit-source takeover. The color field
  belongs to the selected engine and cannot be shared concurrently.
- JPEG95, WebSocket repeated compression disabled, slow-viewer timeout,
  bounded browser queue, offscreen decoding and stale-frame tokens.
- HTTP byte ranges and video-frame synchronization. The browser and `/health`
  use QinChe's 500-frame playback timeline, not 251-frame modulo.
- Native idle continues from the final displayed timeline index. Without a
  viewer sync, QinChe continues its engine cursor between replies.

QinChe's approved export did not include an added mouth-closing animation. Its
live profile therefore returns directly to the corresponding native idle frame.
The legacy settling implementation remains available to Gentleman.

## Validation and timings

See [current validation](VALIDATION.md) for actual streaming checks and new-model
timings. Earlier performance numbers used different models and appearance
pipelines and do not measure this version.

The prior audit is retained as [historical October 13 notes](ENGINEERING-20261013.md).
It describes the retired QinChe bundle and general techniques; it does not
select current assets or processing.

The old static-avatar mouth-patch transport cannot be applied directly to a
moving full-body reference. Full JPEG composition is retained. ChatGPT still
owns audible playback, so the viewer has no shared audio presentation clock.
