import os
import unittest

import numpy

from molml.molecule import BagOfBonds, Connectivity
from molml.molecule import CoulombMatrix, EncodedBond
from molml.utils import read_file_data


DATA_PATH = os.path.join(os.path.dirname(__file__), "data")

METHANE_PATH = os.path.join(DATA_PATH, "methane.out")
METHANE_ELEMENTS, METHANE_NUMBERS, METHANE_COORDS = read_file_data(
    METHANE_PATH)
METHANE = (METHANE_ELEMENTS, METHANE_COORDS)
METHANE2 = (METHANE[0], 2 * METHANE[1])

BIG_PATH = os.path.join(DATA_PATH, "big.out")
BIG_ELEMENTS, BIG_NUMBERS, BIG_COORDS = read_file_data(BIG_PATH)
BIG = (BIG_ELEMENTS, BIG_COORDS)

MID_PATH = os.path.join(DATA_PATH, "mid.out")
MID_ELEMENTS, MID_NUMBERS, MID_COORDS = read_file_data(MID_PATH)
MID = (MID_ELEMENTS, MID_COORDS)

ALL_DATA = [METHANE, MID, BIG]
ALL_ATOM = numpy.array([[1, 4, 0, 0],
                        [2, 3, 0, 4],
                        [25, 15, 5, 4]])


def assert_close_statistics(array, expected):
    '''
    Compare float arrays by comparing some statistics.
    '''
    value = numpy.array([
                        array.mean(),
                        array.std(),
                        array.min(),
                        array.max(),
                        ])
    numpy.testing.assert_array_almost_equal(value, expected)


class ConnectivityTest(unittest.TestCase):

    def test_fit_atom(self):
        a = Connectivity(depth=1)
        a.fit(ALL_DATA)
        self.assertEqual(a._base_chains,
                         set([('N',), ('C',), ('O',), ('H',)]))

    def test_fit_atom_separated(self):
        a = Connectivity(depth=1)
        a.fit([METHANE2])
        self.assertEqual(a._base_chains,
                         set([('C',), ('H',)]))
        self.assertTrue(
            (a.transform([METHANE2]) == numpy.array([[1, 4]])).all())

    def test_fit_bond(self):
        a = Connectivity(depth=2)
        a.fit(ALL_DATA)
        self.assertEqual(a._base_chains,
                         set([('H', 'O'), ('C', 'H'), ('H', 'N'), ('C', 'C'),
                              ('H', 'H'), ('O', 'O'), ('C', 'N'), ('C', 'O')]))

    def test_fit_angle(self):
        a = Connectivity(depth=3)
        a.fit(ALL_DATA)
        self.assertEqual(a._base_chains,
                         set([('H', 'N', 'H'), ('C', 'N', 'H'),
                              ('C', 'C', 'O'), ('N', 'C', 'N'),
                              ('C', 'O', 'C'), ('C', 'N', 'C'),
                              ('H', 'C', 'H'), ('C', 'O', 'H'),
                              ('C', 'C', 'C'), ('C', 'C', 'H'),
                              ('H', 'C', 'O'), ('N', 'C', 'O'),
                              ('H', 'C', 'N'), ('C', 'C', 'N')]))

    def test_fit_dihedral(self):
        # This is to test the double order flipping (CCCH vs HCCC)
        a = Connectivity(depth=4)
        a.fit(ALL_DATA)
        self.assertEqual(a._base_chains,
                         set([('N', 'C', 'N', 'C'), ('C', 'C', 'C', 'O'),
                              ('H', 'C', 'O', 'C'), ('H', 'C', 'C', 'N'),
                              ('H', 'C', 'N', 'C'), ('N', 'C', 'C', 'O'),
                              ('C', 'C', 'C', 'N'), ('H', 'C', 'C', 'H'),
                              ('C', 'C', 'N', 'C'), ('O', 'C', 'N', 'C'),
                              ('C', 'C', 'O', 'C'), ('C', 'C', 'C', 'H'),
                              ('C', 'C', 'C', 'C'), ('H', 'C', 'C', 'O'),
                              ('C', 'C', 'N', 'H'), ('N', 'C', 'O', 'H'),
                              ('C', 'C', 'O', 'H'), ('N', 'C', 'N', 'H')]))

    def test_fit_atom_bond(self):
        # This should be the exact same thing as doing it with
        # use_bond_order=False
        a = Connectivity(depth=1, use_bond_order=True)
        a.fit(ALL_DATA)
        self.assertEqual(a._base_chains,
                         set([('N',), ('C',), ('O',), ('H',)]))

    def test_fit_bond_bond(self):
        a = Connectivity(depth=2, use_bond_order=True)
        a.fit(ALL_DATA)
        self.assertEqual(a._base_chains,
                         set([(('H', 'N', '1'),), (('C', 'N', '3'),),
                              (('H', 'O', '1'),), (('H', 'H', '1'),),
                              (('C', 'H', '1'),), (('O', 'O', '1'),),
                              (('C', 'N', '2'),), (('C', 'O', '1'),),
                              (('C', 'C', '3'),), (('C', 'N', 'Ar'),),
                              (('C', 'C', '1'),), (('C', 'O', 'Ar'),),
                              (('C', 'C', '2'),), (('C', 'C', 'Ar'),)]))

    def test_fit_atom_coordination(self):
        a = Connectivity(depth=1, use_coordination=True)
        a.fit(ALL_DATA)
        self.assertEqual(a._base_chains,
                         set([('C1',), ('N3',), ('N2',), ('O2',), ('N1',),
                              ('O1',), ('C4',), ('H0',), ('H1',), ('O0',),
                              ('C3',), ('C2',)]))

    def test_transform(self):
        a = Connectivity()
        a.fit(ALL_DATA)
        self.assertTrue((a.transform(ALL_DATA) == ALL_ATOM).all())

    def test_small_to_large_transform(self):
        a = Connectivity()
        a.fit([METHANE])
        self.assertTrue((a.transform(ALL_DATA) == ALL_ATOM[:, :2]).all())

    def test_large_to_small_transform(self):
        a = Connectivity()
        a.fit([BIG])
        self.assertTrue((a.transform(ALL_DATA) == ALL_ATOM).all())

    def test_transform_before_fit(self):
        a = Connectivity()
        with self.assertRaises(ValueError):
            a.transform(ALL_DATA)

    def test_fit_transform(self):
        a = Connectivity()
        self.assertTrue((a.fit_transform(ALL_DATA) == ALL_ATOM).all())

    def test_unknown(self):
        a = Connectivity(add_unknown=True)
        expected_results = numpy.array([[1,  4, 0],
                                        [2,  3, 4],
                                        [25, 15, 9]])
        a.fit([METHANE])
        self.assertTrue((a.transform(ALL_DATA) == expected_results).all())


class EncodedBondTest(unittest.TestCase):

    def test_fit(self):
        a = EncodedBond()
        a.fit(ALL_DATA)
        self.assertEqual(a._element_pairs,
                         set([('H', 'O'), ('O', 'O'), ('N', 'O'), ('C', 'O'),
                              ('C', 'H'), ('H', 'N'), ('H', 'H'), ('C', 'C'),
                              ('C', 'N'), ('N', 'N')]))

    def test_transform(self):
        a = EncodedBond()
        a.fit([METHANE])
        # This is a cheap test to prevent needing all the values here
        expected_results = numpy.array([
            0.042672,  # mean
            0.246663,  # std
            0.,  # min
            2.392207,  # max
        ])
        try:
            m = a.fit_transform([METHANE])
            assert_close_statistics(m, expected_results)
        except AssertionError as e:
            self.fail(e)

    def test_large_to_small_transform(self):
        a = EncodedBond()
        a.fit([MID])
        # This is a cheap test to prevent needing all the values here
        expected_results = numpy.array([
            0.042672,  # mean
            0.246663,  # std
            0.,  # min
            2.392207,  # max
        ])
        try:
            m = a.fit_transform([METHANE])
            assert_close_statistics(m, expected_results)
        except AssertionError as e:
            self.fail(e)

    def test_fit_transform(self):
        a = EncodedBond()
        # This is a cheap test to prevent needing all the values here
        expected_results = numpy.array([
            0.042672,  # mean
            0.246663,  # std
            0.,  # min
            2.392207,  # max
        ])
        try:
            m = a.fit_transform([METHANE])
            assert_close_statistics(m, expected_results)
        except AssertionError as e:
            self.fail(e)

    def test_transform_before_fit(self):
        a = EncodedBond()
        with self.assertRaises(ValueError):
            a.transform(ALL_DATA)

    def test_smoothing_function(self):
        a = EncodedBond(smoothing="norm_cdf")

        # This is a cheap test to prevent needing all the values here
        expected_results = numpy.array([
            3.859534e+000,  # mean
            2.182923e+000,  # std
            0.,  # min
            6.000000e+000,  # max
        ])
        try:
            m = a.fit_transform([METHANE])
            assert_close_statistics(m, expected_results)
        except AssertionError as e:
            self.fail(e)

    def test_smoothing_function_error(self):
        a = EncodedBond(smoothing="not valid")

        with self.assertRaises(KeyError):
            a.fit_transform([METHANE])

    def test_max_depth_neg(self):
        a = EncodedBond(max_depth=-1)
        # This is a cheap test to prevent needing all the values here
        expected_results = numpy.array([
            0.503237244954,  # mean
            0.857850829564,  # std
            0.,  # min
            7.15861023,  # max
        ])
        try:
            m = a.fit_transform([BIG])
            assert_close_statistics(m, expected_results)
        except AssertionError as e:
            self.fail(e)

    def test_max_depth_1(self):
        a = EncodedBond(max_depth=1)

        # This is a cheap test to prevent needing all the values here
        expected_results = numpy.array([
            0.0443793,  # mean
            0.33766942,  # std
            0.,  # min
            5.76559336,  # max
        ])
        try:
            m = a.fit_transform([BIG])
            assert_close_statistics(m, expected_results)
        except AssertionError as e:
            self.fail(e)

    def test_max_depth_3(self):
        a = EncodedBond(max_depth=3)

        # This is a cheap test to prevent needing all the values here
        expected_results = numpy.array([
            0.18434482,  # mean
            0.62589799,  # std
            0.,  # min
            7.15861023,  # max
        ])
        try:
            m = a.fit_transform([BIG])
            assert_close_statistics(m, expected_results)
        except AssertionError as e:
            self.fail(e)

    def test_spacing_inverse(self):
        a = EncodedBond(spacing="inverse")

        # This is a cheap test to prevent needing all the values here
        expected_results = numpy.array([
            0.051207,  # mean
            0.269248,  # std
            0.,  # min
            2.387995,  # max
        ])
        try:
            m = a.fit_transform([METHANE])
            assert_close_statistics(m, expected_results)
        except AssertionError as e:
            self.fail(e)

    def test_spacing_log(self):
        a = EncodedBond(spacing="log")

        # This is a cheap test to prevent needing all the values here
        expected_results = numpy.array([
            0.072768,  # mean
            0.318508,  # std
            0.,  # min
            2.339376,  # max
        ])
        try:
            m = a.fit_transform([METHANE])
            assert_close_statistics(m, expected_results)
        except AssertionError as e:
            self.fail(e)

    def test_spacing_invalid(self):
        a = EncodedBond(spacing="not valid")

        with self.assertRaises(KeyError):
            a.fit_transform([METHANE])

    def test_form_element(self):
        a = EncodedBond(form=1)

        # This is a cheap test to prevent needing all the values here
        expected_results = numpy.array([
            0.085345,  # mean
            0.452595,  # std
            0.,  # min
            4.784414,  # max
        ])
        try:
            m = a.fit_transform([METHANE])
            self.assertEqual(m.shape, (1, 200))
            assert_close_statistics(m, expected_results)
        except AssertionError as e:
            self.fail(e)

    def test_form_0(self):
        a = EncodedBond(form=0)

        # This is a cheap test to prevent needing all the values here
        expected_results = numpy.array([
            0.085345,  # mean
            0.343574,  # std
            0.,  # min
            2.392207,  # max
        ])
        try:
            m = a.fit_transform([METHANE])
            self.assertEqual(m.shape, (1, 100))
            assert_close_statistics(m, expected_results)
        except AssertionError as e:
            self.fail(e)


class CoulombMatrixTest(unittest.TestCase):

    def test_fit(self):
        a = CoulombMatrix()
        a.fit(ALL_DATA)
        self.assertEqual(a._max_size, 49)

    def test_transform(self):
        a = CoulombMatrix()
        a.fit([METHANE])
        expected_results = numpy.array([
            [36.8581052,   5.49459021,   5.49462885,   5.4945,
                5.49031286,   5.49459021,   0.5,   0.56071947,
                0.56071656,   0.56064037,   5.49462885,   0.56071947,
                0.5,   0.56071752,   0.56064089,   5.4945,
                0.56071656,   0.56071752,   0.5,   0.56063783,
                5.49031286,   0.56064037,   0.56064089,   0.56063783,
                0.5]])
        try:
            numpy.testing.assert_array_almost_equal(
                a.transform([METHANE]),
                expected_results)
        except AssertionError as e:
            self.fail(e)

    def test_small_to_large_transform(self):
        a = CoulombMatrix()
        a.fit([METHANE])
        with self.assertRaises(ValueError):
            a.transform(ALL_DATA)

    def test_large_to_small_transform(self):
        a = CoulombMatrix()
        a.fit([MID])

        expected_results = numpy.array([
            [36.8581052,   5.49459021,   5.49462885,   5.4945,
             5.49031286,   0.,   0.,   0.,
             0.,   5.49459021,   0.5,   0.56071947,
             0.56071656,   0.56064037,   0.,   0.,
             0.,   0.,   5.49462885,   0.56071947,
             0.5,   0.56071752,   0.56064089,   0.,
             0.,   0.,   0.,   5.4945,
             0.56071656,   0.56071752,   0.5,   0.56063783,
             0.,   0.,   0.,   0.,
             5.49031286,   0.56064037,   0.56064089,   0.56063783,
             0.5] + [0.0] * 40
        ])
        try:
            numpy.testing.assert_array_almost_equal(
                a.transform([METHANE]),
                expected_results)
        except AssertionError as e:
            self.fail(e)

    def test_transform_before_fit(self):
        a = CoulombMatrix()
        with self.assertRaises(ValueError):
            a.transform(ALL_DATA)

    def test_fit_transform(self):
        a = CoulombMatrix()
        expected_results = numpy.array([
            [36.8581052,   5.49459021,   5.49462885,   5.4945,
                5.49031286,   5.49459021,   0.5,   0.56071947,
                0.56071656,   0.56064037,   5.49462885,   0.56071947,
                0.5,   0.56071752,   0.56064089,   5.4945,
                0.56071656,   0.56071752,   0.5,   0.56063783,
                5.49031286,   0.56064037,   0.56064089,   0.56063783,
                0.5]])
        try:
            numpy.testing.assert_array_almost_equal(
                a.fit_transform([METHANE]),
                expected_results)
        except AssertionError as e:
            self.fail(e)


class BagOfBondsTest(unittest.TestCase):

    def test_fit(self):
        a = BagOfBonds()
        a.fit([METHANE])
        expected_results = {
            ('C', 'H'): 4,
            ('H', 'H'): 6,
        }
        self.assertEqual(a._bag_sizes, expected_results)

    def test_fit_multi_mol(self):
        a = BagOfBonds()
        a.fit(ALL_DATA)
        expected_results = {
            ('H', 'O'): 60,
            ('C', 'H'): 375,
            ('H', 'N'): 75,
            ('C', 'C'): 300,
            ('H', 'H'): 105,
            ('O', 'O'): 6,
            ('C', 'N'): 125,
            ('N', 'O'): 20,
            ('C', 'O'): 100,
            ('N', 'N'): 10,
        }
        self.assertEqual(a._bag_sizes, expected_results)

    def test_transform(self):
        a = BagOfBonds()
        a.fit([METHANE])
        expected_results = numpy.array([
            [5.49462885, 5.49459021, 5.4945, 5.49031286, 0.56071947,
             0.56071752, 0.56071656, 0.56064089, 0.56064037, 0.56063783]
        ])
        try:
            numpy.testing.assert_array_almost_equal(
                a.transform([METHANE]),
                expected_results)
        except AssertionError as e:
            self.fail(e)

    def test_small_to_large_transform(self):
        a = BagOfBonds()
        a.fit([METHANE])
        with self.assertRaises(ValueError):
            a.transform(ALL_DATA)

    def test_large_to_small_transform(self):
        a = BagOfBonds()
        a.fit([BIG])

        expected_results = numpy.array([
            [0.0] * 300 +
            [5.494628848219048, 5.494590213211275, 5.494499999706413,
             5.49031286145183] +
            [0.0] * 596 +
            [0.5607194714171738, 0.5607175240809282, 0.5607165613824526,
             0.5606408892793993, 0.5606403708987712, 0.560637829974531] +
            [0.0] * 270
        ])
        try:
            numpy.testing.assert_array_almost_equal(
                a.transform([METHANE]),
                expected_results)
        except AssertionError as e:
            self.fail(e)

    def test_transform_before_fit(self):
        a = BagOfBonds()
        with self.assertRaises(ValueError):
            a.transform(ALL_DATA)


if __name__ == '__main__':
    unittest.main()
