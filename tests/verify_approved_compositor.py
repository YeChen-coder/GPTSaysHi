"""Optional local reproduction against supplied approved predictions and PNGs."""
import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, '/opt/FeatherTalk')
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'runtime'))
from native_face_match import NativeFaceMatch
from face_utils import crop_face, extract_inner

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--base', required=True, type=Path)
parser.add_argument('--approved', required=True, type=Path)
parser.add_argument('--output', required=True, type=Path)
args = parser.parse_args()
frames = np.load(args.base / 'frames.npy', mmap_mode='r')
boxes = np.load(args.base / 'bboxes.npy')
points = np.load(args.base / 'landmarks.npy')
indices = np.load(args.base / 'source_indices.npy')
matcher = NativeFaceMatch()
prepared = [matcher.prepare(frame, pts, box) for frame, pts, box in zip(frames, points, boxes)]
references = [extract_inner(crop_face(frame, tuple(box))) for frame, box in zip(frames, boxes)]
checks = comparisons = 0
for name in ['qinche_speech_03_v14', 'qinche_speech_12_v14', 'qinche_speech_36_v14']:
    matcher.field = None
    predictions = np.load(args.approved / (name + '_predictions.npy'), mmap_mode='r')
    assert len(predictions) == 250
    for index, prediction in enumerate(predictions):
        cursor = 50 + index
        source = int(indices[cursor])
        roi = matcher.apply(prediction, references[source], prepared[source])
        mask = prepared[source]['alpha'][..., 0] == 0
        np.testing.assert_array_equal(roi[mask], prepared[source]['native'][mask])
        checks += 1
        if name == 'qinche_speech_03_v14' and cursor in [50, 62, 100, 162, 237, 287, 299]:
            image = frames[source].copy()
            x1, y1, x2, y2 = map(int, boxes[source])
            image[y1:y2, x1:x2] = roi
            expected = cv2.imread(str(args.approved / f'frame_{cursor}_native.png'))
            np.testing.assert_array_equal(image, expected)
            comparisons += 1
report = {'passed': True, 'native_preservation_checks': checks, 'approved_png_exact_matches': comparisons,
          'scope': 'Same supplied predictions, references, geometry and causal color-field history; pre-encoding'}
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report))
