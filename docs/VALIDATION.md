# Standalone validation

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
