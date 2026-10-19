# Standalone validation

## Current QinChe - October 19, 2026

The approved epoch-115 new-base model and relaxed waiting take 2 now replace the
October 17 profile. QinChe uses transparent mouth PNGs over continuously visible
native video with explicit BT.709 signaling. Details, timing, color checks and
resource identities are in [the current migration record](QINCHE-20261019.md).

The following sections preserve older validation; their models and performance
numbers do not describe the current default.


## Historical QinChe replacement — October 17, 2026

The previous QinChe bundle is retired. Historical sections below do not select
the current model or appearance. The October 17 approval handoff is implemented
by the native rendering profile described in [ENGINEERING.md](ENGINEERING.md).

- Checkpoint: clean random-start `epoch_100.pth`, SHA-256
  `7c44912c27f52ff84fdc632c63446d9a835c6aa1915c1ecb7d2a0251786feace`.
  The supplied 110-point NativeFaceMatch code is unchanged, SHA-256
  `4c763464098d1a02e5668527c50ecc36575bf6709e452294d9e645da4bc06d60`.
- Eleven runtime asset files are hash-verified. The resource archive is
  515,751,094 bytes, SHA-256
  `ec6c951c9924622b5e20cb4b700b443a847ee1f0885e528b5dd5181e8e2fcca9`.
  The silent native idle is 500 frames / 20 seconds; its SHA-256 is
  `929326af5c9aae2fd613e8a492aceb731c0963635c60e38ac60eb84e9059d8b7`.
- Same supplied predictions, geometry and causal color history reproduced all
  seven approved PNGs pixel-for-pixel. All 750 speech frames preserved protected
  native pixels exactly before JPEG/MP4 encoding. This verifies composition,
  not equivalence of live versus offline audio features.
- Sixteen host distribution/control checks passed; four additional NumPy/OpenCV
  compositor checks passed in the avatar image. Coverage includes the 500-to-251
  source map, profile isolation, correct 110-point support, generated mouth
  center, color-field history/reset, worker exceptions and joined cancellation.
- The real viewer received 530 continuous speech frames across the 20-second
  loop, both direction changes, seek/range/wrap, interruption, repeated speech
  and publisher reconnection. Native QinChe has no generated settling frames or
  viewer crossfade. There were no page errors.
- Sixty seconds of wall-clock-paced held-out speech generated 1,500 frames with
  continuous timeline indices. RSS was 1,919,748 KiB at each ten-second sample;
  change from the 20-second sample to the final sample was zero. This is a
  one-minute working-set check, not an hours-long soak test.
- New-model timing used the held-out speech 12 PCM with 100 ms packets: seven
  1.6-second trials. First trial receipt/display indicator: 116.5 / 142.0 ms;
  median over the remaining six: 34.75 / 79.2 ms. Timing begins at the first
  complete packet send and ends at receipt or decoded-image assignment followed
  by rAF; it excludes upstream generation/capture, packet filling and physical
  display scanout. This is a fresh measurement, not a reused Gentleman result.
- Windows source takeover/native bridge shutdown and actual isolated Edge
  155.0.4283.62 / Chrome 155.0.8059.80 capture passed. Browser fixtures were local;
  no new signed-in ChatGPT Live call was made during these automated checks.
- Gentleman retains its original checkpoint, teeth, matched chin and 400 ms
  settling profile. Its separate regression also passed 530 speech frames plus
  ten settling frames, both loop turns, interruption/resume and reconnection.
  The standalone app stays on port 19088; the Specter service
  and the approved comparison viewer on 19102 are not reconfigured by this work.

The seven new-model trials are retained in
[the October 17 benchmark record](benchmarks/qinche-native-20261017.json).

## Engineering audit — October 13, 2026

- Compared Gentleman engineering records with the selected QinChe runtime;
  [the audit](ENGINEERING.md) maps caching, warmup, streaming, transport,
  display, teeth, detail and idle-handoff optimizations to their shared code.
- Restored immediate per-frame publication, including EOF flushes. Twelve CPU
  checks pass, including three new regression checks for first-frame delivery
  before later inference completes, worker errors and disconnected consumers.
- Same-input, seven-trial viewer measurements passed before and after the
  change. Final steady medians were 55.8 ms to first receipt and 81.2 ms to the
  decoded-image/rAF display indicator, versus 64.5 / 90.9 ms before. Each trial
  received and displayed all 40 speech plus ten settling frames. Raw timings
  and measurement limits are in the audit; initial-use jitter remains.
- The actual viewer passed 280-frame continuous QinChe speech, both loop turns,
  HTTP Range/seek/wrap, the exact idle handoff index, interruption, speech
  resumption during settling and publisher reconnection, without page errors.
- Windows source replacement/native bridge shutdown and actual isolated Edge
  and Chrome tab capture passed with the incremental bridge.
- Gentleman also passed seven viewer trials with all 40 speech and ten settling
  frames received/displayed per trial. After that compatibility check, the
  standalone service was switched back to QinChe.
- Model weights, avatar resource manifests, JPEG quality and input protocol
  were not changed. The service remains in fast mode with 100 ms packets,
  four seconds of history and a 400 ms return to matched idle.

## QinChe update — October 13, 2026

- Nine CPU distribution/selection checks passed, including `.env` versus shell
  precedence, rejection of unknown identities, identity-specific model/media
  hashes and verification of only the selected character's manifest.
- All 84 QinChe runtime resource files matched SHA-256. The visual checkpoint
  is the completed v14 training run's best validation epoch 22:
  `3940a2fc552570e35190e783f408d7e24db239f3c56a436c98ed3263ada94daf`.
  The resource archive is 540,963,041 bytes, SHA-256
  `6125305134a021c1fc41480d1000fa3f31560927b0cbd3f44d62f1b48aeff1d5`.
- Standalone Docker build and GPU startup passed for both characters. Switching
  to gentleman restored its unchanged October 4 checkpoint and 500-frame loop;
  switching back selected QinChe's 250-frame, 25 fps, 10-second loop. One visual
  model is loaded per service process. All runtime mounts remain inside this
  standalone project.
- Six seconds of local 24 kHz speech produced 150 QinChe speech frames and ten
  settling frames. Starting near the loop end exercised index wraparound. Teeth
  restoration ran on speech; output returned to idle without server errors.
- Source ownership and native bridge shutdown integration passed with QinChe.
  Actual Edge 153.0.4234.32 and Chrome 155.0.8059.40 extension capture passed in
  isolated profiles: selected-tab audio drove QinChe, unrelated tab audio sent
  no packets, and replacement/navigation stopped capture without reconnecting.
  These browser checks used local fixtures, not a signed-in Live conversation.
- QinChe's per-frame jaw support is applied to generation and sharpening to
  preserve the native collar. Its supplied matched-idle cache is verified
  against its own model, base, bounding boxes and patch hashes. This update does
  not enable the unselected mouth smoothing experiment.
- Original gentleman resource files and their release metadata remain intact.
  The Specter service on port 18988 was not restarted or reconfigured by this
  work. The standalone service on port 19088 is left on QinChe.

## Initial package — October 4, 2026

The standalone repository was tested from its own directory, virtual environment,
Dockerfile and downloaded-asset layout. The container is `gptsayshi-avatar-1` and
uses `gptsayshi:local`; it does not mount SpecterSaysHi or use its prebuilt image.

## Completed checks

- Five distribution tests passed: English UI surfaces, no parent-checkout mount,
  archive file-list enforcement, rejection of corrupted resources and successful
  resource installation with post-install corruption detection.
- Python and browser extension syntax checks passed. Docker Compose validation,
  image construction, Windows capture-helper compilation and standalone GPU
  startup passed.
- All 110 runtime asset files matched their recorded SHA-256 hashes. The
  separately packaged archive is 565,258,738 bytes, with SHA-256
  `ce6c79e5f9ede271cb74a83c69604c9a19c0323e4465b45b78d44f5dca6142e3`.
- Source ownership integration passed: app → Classic → browser, replacement
  during speech, rapid consecutive connections and rejection of an unknown
  source. A real Windows capture bridge stopped with exit code 0 when superseded,
  including while its target process was silent. It did not reconnect to take over.
- Edge 153.0.4234.32 and Chrome 154.0.8037.93 passed actual extension and
  `tabCapture` tests in isolated browser profiles. An unrelated audible tab sent
  zero packets. The selected ChatGPT-origin fixture supplied 24 kHz audio and
  generated avatar frames. Navigation stopped capture; a newer app source stopped
  the extension; explicit reactivation switched back.
- The preview, extension manifest, tooltip, buttons, status messages and
  project-generated error strings use English. The repository author's original
  bilingual introduction remains intact in README.md.
- The original Specter service on port 18988 retained its original checkpoint
  and had no generated speech frames from this work.

## What the browser tests establish

The integration tests use local, generated tone fixtures with a ChatGPT origin,
not signed-in browsing profiles or a real ChatGPT Live conversation. They test
the actual browser media API and audio-to-avatar pipeline. Earlier development
also captured a real ChatGPT app conversation, but those conversation recordings
are not included in this repository or release.

No precise end-to-end lip-sync latency or consumption of an account's voice
allowance was measured. Playback remains controlled by ChatGPT rather than by a
shared audio/video presentation clock in GPTSaysHi.

Run the portable checks using the commands in README.md. Integration reports
are written to ignored local `results/` directories.
