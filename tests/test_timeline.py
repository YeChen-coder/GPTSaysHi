import unittest
from runtime.timeline import TimelineFrames


class PlaybackTimeline(unittest.TestCase):
    def test_reverse_half_maps_to_the_same_unique_references(self):
        frames = [object() for _ in range(251)]
        indices = list(range(251)) + list(range(249, 0, -1))
        timeline = TimelineFrames(frames, indices)
        self.assertEqual(len(timeline), 500)
        self.assertIs(timeline[250], frames[250])
        self.assertIs(timeline[251], frames[249])
        self.assertIs(timeline[499], frames[1])
        self.assertIs(timeline[0], frames[0])
        self.assertEqual(max(abs(indices[(i + 1) % 500] - indices[i]) for i in range(500)), 1)

    def test_invalid_source_index_is_rejected(self):
        for indices in ([], [0, 2], [-1]):
            with self.assertRaises(ValueError):
                TimelineFrames(['first', 'second'], indices)
