import unittest

try:
    import cv2
    import numpy as np
    from runtime.native_face_match import NativeFaceMatch
except ModuleNotFoundError:
    np = None


@unittest.skipIf(np is None, 'Install NumPy/OpenCV or run these checks in the avatar image')
class NativeFaceComposition(unittest.TestCase):
    def setUp(self):
        points = np.zeros((110, 2), np.float32)
        theta = np.linspace(np.pi, 0, 33)
        points[:33] = np.stack([76 + 65 * np.cos(theta), 32 + 108 * np.sin(theta)], axis=1)
        theta = np.linspace(0, 2 * np.pi, 15, endpoint=False)
        points[51:66] = np.stack([76 + 10 * np.cos(theta), 68 + 10 * np.sin(theta)], axis=1)
        points[60] = [76, 84]
        theta = np.linspace(0, 2 * np.pi, 20, endpoint=False)
        points[90:110] = np.stack([76 + 22 * np.cos(theta), 106 + 7 * np.sin(theta)], axis=1)
        yy, xx = np.mgrid[:152, :152]
        self.native = np.stack([xx, yy, (xx + yy) // 2], axis=2).astype(np.uint8)
        self.points = points
        self.reference = self.native[4:148, 4:148].copy()
        self.prediction = 255 - self.reference
        self.matcher = NativeFaceMatch()
        self.prepared = self.matcher.prepare(self.native, points, (0, 0, 152, 152))

    def test_nose_chin_and_all_pixels_outside_mouth_remain_exactly_native(self):
        original = self.native.copy()
        result = self.matcher.apply(self.prediction, self.reference, self.prepared)
        protected = self.prepared['alpha'][..., 0] == 0
        np.testing.assert_array_equal(result[protected], original[protected])
        for point in self.points[list(range(51, 66)) + [16]]:
            x, y = np.rint(point).astype(int)
            self.assertEqual(self.prepared['alpha'][y, x, 0], 0)
        np.testing.assert_array_equal(self.native, original)

    def test_mouth_center_is_generated_without_blending_the_closed_source_mouth(self):
        result = self.matcher.apply(self.prediction, self.reference, self.prepared)
        self.assertEqual(self.prepared['alpha'][106, 76, 0], 1)
        corrected = np.rint(np.clip(self.prediction.astype(np.float32) + self.matcher.field, 0, 255)).astype(np.uint8)
        np.testing.assert_array_equal(result[106, 76], corrected[102, 72])
        self.assertGreater(float(np.linalg.norm(result[106, 76].astype(float) - self.native[106, 76])), 10)

    def test_color_field_uses_only_current_and_previous_frames(self):
        self.matcher.apply(self.prediction, self.reference, self.prepared)
        previous = self.matcher.field.copy()
        other = np.full_like(self.prediction, 30)
        fresh = NativeFaceMatch()
        fresh.apply(other, self.reference, self.prepared)
        self.matcher.apply(other, self.reference, self.prepared)
        np.testing.assert_allclose(self.matcher.field, .8 * previous + .2 * fresh.field)
        self.matcher.field = None
        self.matcher.apply(other, self.reference, self.prepared)
        np.testing.assert_array_equal(self.matcher.field, fresh.field)

    def test_other_landmark_layouts_are_rejected(self):
        with self.assertRaisesRegex(AssertionError, '110-point'):
            self.matcher.prepare(self.native, self.points[:98], (0, 0, 152, 152))
