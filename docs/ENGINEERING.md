# Character-independent engineering optimizations

Reviewed October 13, 2026 against the original Gentleman streaming, latency,
moving-base, teeth, detail-balance and October 4 refresh records. QinChe uses
the same standalone audio/rendering path. Most optimizations were already
shared; this update restores immediate per-frame delivery in the ChatGPT bridge.

The local source records were `feathertalk_lab/LOOP-BASE.zh-CN.md`,
`LATENCY-COMPARISON.zh-CN.md`, `DETAIL-APPLIED.zh-CN.md`, `RESULTS.zh-CN.md`,
and `feathertalk_refresh_20261004/HANDOFF_CURRENT.zh-CN.md` in SpecterSaysHi.

| Optimization | Benefit | QinChe implementation |
| --- | --- | --- |
| Keep one selected visual model and audio encoder loaded | Avoid model loading for each reply | `runtime/engine_runtime.py`; character selection happens before loading |
| Cache each moving reference on the GPU in contiguous NCHW layout | Avoid repeating crops and transfers online | `engine/loop_core.py`, selected character's frames and boxes |
| Warm real streaming input sizes using silence | Reduce first-use audio encoder and visual kernel work | Existing startup warmup in `engine/loop_core.py` |
| Limit CPU worker fan-out | Avoid excessive threads under the container's four-CPU quota | Torch/OpenCV use one thread in the moving engine; BLAS limits remain configured |
| 100 ms input packets and fast mode | No extra future-audio wait | Existing 24 kHz PCM16 input, zero-lookahead mode |
| Four seconds of audio history and bounded diagnostics | Prevent long replies from growing memory indefinitely | `runtime/realtime_session.py` clears consumed PCM and per-frame records |
| Continuous resampling across packet boundaries | Avoid resetting the 24-to-16 kHz phase every packet | Existing `runtime/streaming_resampler.py` |
| **Send each generated frame immediately** | First frame does not wait for later frames in its packet | **Restored in `runtime/frame_delivery.py` and `specter_server.py`** |
| Disable TCP small-packet waiting | Avoid transport delay | Verified asyncio's socket transport sets `TCP_NODELAY` in the installed runtime |
| Bound browser and sender queues; discard canceled frames | Prevent growing display lag and stale-frame flashes | Existing viewer decode tokens, four-frame queue and audio bridge backpressure |
| Same-character teeth with lip clipping and visibility control | Restore teeth while preserving moving lips | QinChe's selected donor 08 and its own per-frame anchors |
| Soft generation boundary and local brightness sharpening | Reduce seams and softness without extra audio buffering | Existing renderer/detail filter; QinChe also uses its jaw support mask |
| Precompute matched idle chin patches | Avoid model work during idle and appearance jumps at handoff | QinChe's own verified `chin_patches.npy`, matched video and poster |
| Continuous moving-base indices and forward/reverse loop mapping | Preserve head/body motion through speech and idle | QinChe's 250-frame loop; all paired assets use the same mapping |
| 400 ms residual-to-idle transition, interruption and resume | Return to the corresponding moving frame | Existing `runtime/idle_transition.py` and publisher state machine |
| HTTP byte ranges for idle media | Enable actual browser seek and loop handoff | Verified `206` response through Starlette's `FileResponse` |
| Latest explicit source owns the renderer | Prevent multiple sessions from fighting over output | Existing app/Classic/browser takeover and shutdown logic |

## Restored frame delivery

The original moving-base Gentleman server generated and emitted one frame at a
time. The standalone ChatGPT bridge instead collected all frames from an audio
packet before broadcasting any of them. The new bridge advances the generator
in a worker thread, sends that frame, then requests the next frame. It also
streams final audio flushes. Inference remains serialized under the existing
ownership lock; model inputs, JPEG quality and visual assets are unchanged.

Regression checks prove the first frame is sent while generation of the second
is still blocked, the event loop remains available, and errors close the
generator without rendering an unwanted tail.

## Before/after measurement

Same QinChe checkpoint and local speech PCM, seven 1.6-second trials in each
series, 100 ms packets and the actual viewer decode/display path. The summary
uses the six trials after the first. Raw per-trial timings are included in
[the measurement record](benchmarks/qinche-stream-20261013.json).

| Metric | Before | Final version |
| --- | ---: | ---: |
| Median first frame received | 64.5 ms | 55.8 ms |
| Median first decoded frame assigned, followed by browser rAF | 90.9 ms | 81.2 ms |
| Speech / settling frames per trial | 40 / 10 | 40 / 10 |
| Displayed frames per trial | 50 | 50 |

Timing begins when the first complete audio packet is sent. It excludes ChatGPT
generation, capture and packet filling, model loading, and physical screen
scanout. The runs are sequential on a shared local GPU, not an isolated,
randomized performance experiment. The first final-version trial was
106.9 / 159.1 ms; initial-use jitter is still present. These numbers do not
measure the difference between audible ChatGPT playback and the avatar.

An additional full-output startup warmup was tested. It did not consistently
improve the first trial, so the final version keeps the proven visual/audio
shape warmup. No unselected mouth smoothing experiment is enabled.

## Which earlier optimizations need a different design

The early static-image Gentleman experiment sent lossless mouth patches over
a fixed portrait to avoid encoding the whole image. Both current characters
use moving full-frame references. That static-patch protocol cannot preserve
their moving body/background by itself, so they retain full JPEG frames and
the original moving-base compositor.

The earlier standalone audio demo controlled playback and scheduled pictures
against its audio clock. GPTSaysHi receives audio after ChatGPT plays it; it
continues to use bounded immediate display instead of adding that demo's
80 ms playback buffer. A shared playback clock is a separate capability.

## Reproduce

With the selected avatar running:

```powershell
python -m unittest discover -s tests -p "test_*.py"
node .\tests\benchmark_stream.cjs current
node .\tests\integration_avatar.cjs
```

The two browser checks use a generated tone by default. Supply a local mono
24 kHz PCM16 file as the next argument to use speech; the benchmark needs at
least 1.6 seconds, and the integration check needs at least one idle-loop
duration plus 1.2 seconds. Timing and screenshots stay in ignored `results/`.
