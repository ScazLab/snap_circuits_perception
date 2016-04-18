from unittest import TestCase
import numpy as np

from board_perception.part_classifier import (
    H_MARGIN, W_MARGIN, H_CELL, W_CELL,
    NORTH, SOUTH, EAST, WEST, ROTATION, PART_TAG_LOCATION,
    cell_coordinate, rotate_tag_location, tag_location_from_part,
    inverse_orientation, part_reference_from_tag_location,
    LabeledCellExtractor)


class DummyImage():

    shape = (600, 400)

    def __getitem__(self, slices):
        return (slices[0].start, slices[0].stop,
                slices[1].start, slices[1].stop)


class TestCellCoordinate(TestCase):

    def test_0_0_is_margins(self):
        self.assertEqual(cell_coordinate(0, 0), (H_MARGIN, W_MARGIN))

    def test_0_1(self):
        self.assertEqual(cell_coordinate(0, 1), (H_MARGIN, W_MARGIN + W_CELL))

    def test_1_0(self):
        self.assertEqual(cell_coordinate(1, 0), (H_MARGIN + H_CELL, W_MARGIN))


class TestRotations(TestCase):

    def test_is_rotation(self):
        for (a, b, c, d) in [r.flatten() for r in ROTATION]:
            self.assertEqual(a * d - b * c, 1)

    def test_east_is_identity(self):
        self.assertEqual(tuple(ROTATION[EAST].flatten()), (1, 0, 0, 1))

    def test_rotate_tag_location(self):
        np.testing.assert_array_equal(
            rotate_tag_location((2, 3), EAST), np.array([2, 3]))
        np.testing.assert_array_equal(
            rotate_tag_location((2, 3), WEST), np.array([-2, -3]))
        np.testing.assert_array_equal(
            rotate_tag_location((2, 3), NORTH), np.array([-3, 2]))
        np.testing.assert_array_equal(
            rotate_tag_location((2, 3), SOUTH), np.array([3, -2]))

    def test_rotates_float(self):
        np.testing.assert_array_equal(
            rotate_tag_location((.2, 3.5), SOUTH), np.array([3.5, -.2]))

    def test_tag_location_from_part(self):
        np.testing.assert_array_equal(
            tag_location_from_part('5', np.array([4, 3]), EAST),
            np.array([4, 4.5]))
        np.testing.assert_array_equal(
            tag_location_from_part('5', np.array([4, 3]), SOUTH),
            np.array([5.5, 3]))
        np.testing.assert_array_equal(
            tag_location_from_part('u2', np.array([4, 3]), WEST),
            np.array([3.5, 2]))
        np.testing.assert_array_equal(
            tag_location_from_part('u2', np.array([4, 3]), NORTH),
            np.array([3, 3.5]))

    def test_inverse_orientation(self):
        self.assertEqual(inverse_orientation(NORTH), SOUTH)
        self.assertEqual(inverse_orientation(SOUTH), NORTH)
        self.assertEqual(inverse_orientation(WEST), EAST)
        self.assertEqual(inverse_orientation(EAST), WEST)

    def test_part_reference_from_tag_location(self):
        loc = np.random.randint(10, size=(2,))
        for label in PART_TAG_LOCATION:
            for o in [NORTH, EAST, WEST, SOUTH]:
                np.testing.assert_array_equal(
                    part_reference_from_tag_location(
                        label, tag_location_from_part(label, loc, o), o),
                    loc)


class TestLabeledCellExtractor(TestCase):

    def setUp(self):
        board = {"parts": [
                           {"id": 0,
                            "label": "4",
                            "location": [1, 4, "west"]
                            },
                           {"id": 1,
                            "label": "2",
                            "location": [3, 1, "north"]
                            },
                           {"id": 9,
                            "label": "u2",
                            "location": [4, 6, "east"]
                            },
                           ]}
        img = DummyImage()
        self.extr = LabeledCellExtractor(img, board)

    def test_set_labels(self):
        labels = {(1, 2.5): ("4", WEST),
                  (2.5, 1): ("2", NORTH),
                  (4.5, 7): ("u2", EAST)}
        self.assertEqual(labels, self.extr.labels)

    def test_labeled_cells(self):
        v, h = self.extr.labeled_cells()
        self.assertEqual(9 * 6, len(h))
        self.assertEqual(9 * 6, len(v))
        non_empty_h = [(l, o, c) for ((l, o), c) in h if l is not None]
        non_empty_v = [(l, o, c) for ((l, o), c) in v if l is not None]
        self.assertEqual([("4", WEST)], [(l, o) for (l, o, c) in non_empty_h])
        self.assertEqual([("2", NORTH), ("u2", EAST)],
                         [(l, o) for (l, o, c) in non_empty_v])
        # This is only a non-regression test from a known correct state
        self.assertEqual([(106, 148, 111, 129)],
                         [c for (l, o, c) in non_empty_h])
        self.assertEqual([(235, 277, 51, 69), (408, 450, 290, 308)],
                         [c for (l, o, c) in non_empty_v])


def visual_test():
    import os
    import json
    import cv2
    data = os.path.join(os.path.dirname(__file__), '../../data/')
    with open(os.path.join(data, 'board5.json')) as b:
        board = json.load(b)
    img = cv2.imread(os.path.join(data, 'frame0005.jpg'))
    # Create alpha channel
    alpha = .1 * np.ones((img.shape[0], img.shape[1], 1))
    extr = LabeledCellExtractor(alpha, board)
    vert, hori = extr.labeled_cells()
    for ((l, o), c) in vert + hori:
        if l is not None:
            c[:, :, :] = 1.  # Modifies underlying alpha
    img = np.asarray(img * alpha, dtype=np.int8)
    cv2.imshow('tags', img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    visual_test()
