"""Approved QinChe rendering: native face, mapped moving references, local mouth."""
import json
import time
from pathlib import Path

import cv2
import numpy as np
import torch

from character_assets import character_assets
from face_utils import crop_face, extract_inner, mask_mouth, reshape_audio_feat
from native_face_match import NativeFaceMatch
from stream_core import Engine
from timeline import TimelineFrames


class NativeLoopEngine(Engine):
    def __init__(self):
        self.assets = character_assets()
        if self.assets.renderer != 'native_face':
            raise ValueError('NativeLoopEngine requires the native_face character profile')
        self.checkpoint_path = self.assets.checkpoint
        super().__init__(checkpoint=str(self.checkpoint_path), base_image=self.assets.image,
                         base_landmarks=self.assets.landmarks)
        torch.set_num_threads(1)
        cv2.setNumThreads(1)
        root = self.assets.base
        self.manifest = json.loads((root / 'manifest.json').read_text())
        self.unique_frames = np.load(root / 'frames.npy', mmap_mode='r')
        self.landmarks = np.load(root / 'landmarks.npy')
        self.unique_bboxes = np.load(root / 'bboxes.npy')
        self.source_indices = np.load(root / 'source_indices.npy')
        self.frames = TimelineFrames(self.unique_frames, self.source_indices)
        self.count = len(self.frames)
        if (self.count != self.manifest['frames'] or len(self.unique_frames) != self.manifest['unique_frames']
                or self.landmarks.shape != (len(self.unique_frames), 110, 2)):
            raise ValueError('Native character reference geometry does not match its timeline')
        self.bboxes = self.unique_bboxes[self.source_indices]
        self.references = np.asarray([extract_inner(crop_face(frame, tuple(box)))
                                      for frame, box in zip(self.unique_frames, self.unique_bboxes)])
        masked = np.asarray([mask_mouth(reference.copy()) for reference in self.references])
        inputs = np.concatenate([self.references.transpose(0, 3, 1, 2), masked.transpose(0, 3, 1, 2)], axis=1)
        self.model_inputs = (torch.from_numpy(inputs).to(self.device).float() / 255).contiguous()
        self.matcher = NativeFaceMatch()
        self.prepared = [self.matcher.prepare(frame, points, box)
                         for frame, points, box in zip(self.unique_frames, self.landmarks, self.unique_bboxes)]
        self.compositor = 'NativeFaceMatch'
        self.teeth = None
        self.teeth_mode = 'model'
        self.detail_profile = 'original'
        self.detail_last_ms = 0.
        self.native_match_last_ms = 0.
        self.idle_video_path = root / 'idle.mp4'
        self.idle_poster_path = root / 'poster.jpg'
        self.begin(0)
        started = time.perf_counter()
        with torch.inference_mode():
            self.visual(self.model_inputs[0:1], torch.zeros(1, 40, 1024, device=self.device))
        for seconds in [i / 10 for i in range(1, 52)] + [4.12, 4.14, 4.52, 4.54, 5.12, 5.14]:
            self.encode(np.zeros(round(seconds * 16000), np.float32))
        self.sync()
        self.stream_shape_warmup_seconds = time.perf_counter() - started

    def idle_frame(self, index):
        return self.frames[index].copy()

    def begin(self, frame):
        self.cursor = int(frame) % self.count
        self.indices = []
        self.teeth_rows = []
        self.matcher.field = None

    @torch.inference_mode()
    def render(self, window):
        index = self.cursor
        source = int(self.source_indices[index])
        prediction = self.visual(self.model_inputs[source:source + 1],
                                 reshape_audio_feat(torch.from_numpy(window))[None].to(self.device))[0]
        prediction = (prediction.cpu().numpy().transpose(1, 2, 0) * 255).clip(0, 255).astype(np.uint8)
        started = time.perf_counter()
        roi = self.matcher.apply(prediction, self.references[source], self.prepared[source])
        self.native_match_last_ms = (time.perf_counter() - started) * 1000
        image = self.unique_frames[source].copy()
        x1, y1, x2, y2 = map(int, self.unique_bboxes[source])
        image[y1:y2, x1:x2] = roi
        self.cursor = (index + 1) % self.count
        self.indices.append(index)
        self.teeth_rows.append({'ms': 0., 'replaced': False})
        return image, prediction
