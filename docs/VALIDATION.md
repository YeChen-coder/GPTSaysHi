# Standalone validation — October 4, 2026

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
