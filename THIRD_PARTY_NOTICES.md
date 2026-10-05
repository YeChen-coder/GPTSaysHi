# Third-party components

The Python files under `vendor/feathertalk/` originate from
[FeatherTalk](https://github.com/anliyuan/FeatherTalk), commit
`ace1227ec0a367a983101bfc17d7e5fcf2bfb63f`. Their Apache 2.0 license is
preserved in `vendor/feathertalk/LICENSE`. These runtime files are vendored
without requiring a checkout of SpecterSaysHi or FeatherTalk.

The separately downloaded avatar bundle includes the FeatherTalk audio
encoder checkpoint and the selected Specter character checkpoint, idle
frames, face landmarks, teeth references, and matched chin patches.
The package contains runtime assets only; original training clips and
recorded conversations are excluded.

PyTorch, MediaPipe, OpenCV, Librosa, Transformers, FastAPI, Uvicorn and
WebSockets retain their respective upstream licenses. Versions used by
the avatar container are pinned in `requirements-avatar.txt`.
