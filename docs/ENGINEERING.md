# Shared streaming, separate character rendering

Current approved QinChe integration: October 19, 2026. Epoch 115 and relaxed
waiting take 2 replace the October 17 close-up profile and earlier rejected
QinChe appearance patches. Gentleman keeps
its own October 4 rendering profile and resources.

## Character profiles

| Item | Approved QinChe | Gentleman |
| --- | --- | --- |
| Visual model | Selected new-base epoch 115 | October 4 selected checkpoint |
| Checkpoint SHA-256 | `007975c1ecda2870144d3f150e4c98d3caab1ee422045d904213a457052730b7` | `205e908f2e9ae8364417110d14f35c856ead742a0dd6c5b1a6388b5da507715d` |
| Reference timeline | 251 unique frames, `0..250,249..1`, 500 playback frames | Existing 500-frame expanded reference |
| Selected source | Relaxed waiting take 2 | Existing selected candidate 1 |
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
- Transparent mouth PNG for QinChe, JPEG95 for Gentleman; WebSocket repeated compression disabled, slow-viewer timeout,
  bounded browser queue, offscreen decoding and stale-frame tokens.
- HTTP byte ranges and video-frame synchronization. The browser and `/health`
  use QinChe's 500-frame playback timeline, not 251-frame modulo.
- Native idle continues from the final displayed timeline index. Without a
  viewer sync, QinChe advances the idle timeline by wall clock between replies.

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

QinChe uses the same continuously visible native video for idle and speaking.
The viewer aligns its timeline to each mouth patch, correcting drift beyond two
frames. PNG pixels outside the actual mouth support are transparent; the RGB
inside is already feathered by NativeFaceMatch and must not be alpha-blended a
second time. This replaces the former full-frame JPEG overlay that switched the
entire image between video and JPEG color paths. The native idle is explicitly
encoded and tagged BT.709 limited. Gentleman retains full-frame JPEG rendering.

The versioned `/view?protocol=2` contract prevents old full-frame viewers from
stretching a cropped PNG to the entire window. Refresh after an upgrade.
ChatGPT still owns audible playback, so the viewer has no shared audio clock.
See [the October 19 migration](QINCHE-20261019.md) and its browser color checks.
