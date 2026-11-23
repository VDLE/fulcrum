#unit tests for stats_engine.py
"""
Tests for app.utility.analytics.stats_engine  (run from server_backend/:  pytest tests/test_stats_engine.py)

These tests ARE the spec. Public API to implement in
server_backend/app/utility/analytics/stats_engine.py:

    describe(values)                       -> dict
    mode(values)                           -> list
    one_sample_ttest(values, popmean)      -> dict
    independent_ttest(a, b, equal_var=False) -> dict   (Welch by default)
    paired_ttest(a, b)                     -> dict
    one_way_anova(*groups)                 -> dict
    linear_fit(x, y)                       -> dict
    normality_test(values, alpha=0.05)     -> dict
    normal_fit(values, n_points=100)       -> dict
    histogram(values, bins=10)             -> dict

Conventions every function must follow:
  * inputs may be a list, tuple, numpy array, or polars Series
  * None / NaN entries are dropped before computing
  * results contain only plain Python floats/ints/lists/None, never numpy types
    or NaN, so Flask's jsonify works. (Tested via json.dumps(..., allow_nan=False).)
  * not enough data raises ValueError (routes catch it and return HTTP 400)
  * "sample" statistics use ddof=1 (variance, std)

Expected values below were computed by hand or with scipy 1.14 / numpy 2.2.
"""
import unittest 
import json
import math
import os
import numpy as np
import pytest
from scipy import stats as sp

from app.utility.analytics import stats_engine as se

#textbook example set: mean 5, population std 2, sample variance 32/7.
DATA = [2, 4, 4, 4, 5, 5, 7, 9]

def assert_json_safe(result):
    """Fails if the result holds numpy scalars or NaN/inf."""
    json.dumps(result, allow_nan=False)

# --------------------------------------------------------------------------
# describe / mode
# --------------------------------------------------------------------------
class TestDescribe:
    def test_basic_values(self):
        r = se.describe(DATA)
        assert r["n"] == 8
        assert r["mean"] == pytest.approx(5.0)
        assert r["median"] == pytest.approx(4.5)
        assert r["min"] == 2
        assert r["max"] == 9
        assert r["range"] == pytest.approx(7)
        assert r["variance"] == pytest.approx(32 / 7)
        assert r["std"] == pytest.approx(math.sqrt(32 / 7))
        assert r["mode"] == [4]

    def test_quartiles_use_linear_interpolation(self):
        r = se.describe(DATA)  # same as numpy.percentile default
        assert r["q1"] == pytest.approx(4.0)
        assert r["q3"] == pytest.approx(5.5)
        assert r["iqr"] == pytest.approx(1.5)

    def test_json_safe(self):
        assert_json_safe(se.describe(DATA))

    def test_single_value_has_no_sample_std(self):
        r = se.describe([7])
        assert r["n"] == 1
        assert r["mean"] == 7
        assert r["median"] == 7
        assert r["range"] == 0
        assert r["std"] is None
        assert r["variance"] is None
        assert_json_safe(r)

    def test_drops_none_and_nan(self):
        r = se.describe([2, None, 4, float("nan"), 4, 4, 5, 5, 7, 9])
        assert r["n"] == 8
        assert r["mean"] == pytest.approx(5.0)

    def test_accepts_numpy_array(self):
        assert se.describe(np.array(DATA))["mean"] == pytest.approx(5.0)

    def test_accepts_polars_series(self):
        pl = pytest.importorskip("polars")
        assert se.describe(pl.Series(DATA))["median"] == pytest.approx(4.5)

    @pytest.mark.parametrize("bad", [[], [None, None], [float("nan")]])
    def test_empty_raises(self, bad):
        with pytest.raises(ValueError):
            se.describe(bad)

class TestMode:
    def test_single_mode(self):
        assert se.mode(DATA) == [4]

    def test_ties_return_all_modes_sorted(self):
        assert se.mode([3, 1, 1, 2, 2]) == [1, 2]

    def test_no_repeats_returns_empty_list(self):
        assert se.mode([1, 2, 3, 4]) == []

    def test_float_values(self):
        assert se.mode([1.5, 2.5, 2.5, 3.5]) == [2.5]

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            se.mode([])

# --------------------------------------------------------------------------
# t-tests
# --------------------------------------------------------------------------
class TestOneSampleTTest:
    def test_mean_equals_popmean(self):
        r = se.one_sample_ttest(DATA, popmean=5)
        assert r["t_stat"] == pytest.approx(0.0, abs=1e-12)
        assert r["p_value"] == pytest.approx(1.0)
        assert r["df"] == 7

    def test_known_values(self):
        r = se.one_sample_ttest(DATA, popmean=3)
        assert r["t_stat"] == pytest.approx(math.sqrt(7))  # 2.6458
        assert r["p_value"] == pytest.approx(0.03314550026377369)
        assert r["df"] == 7
        assert_json_safe(r)

    def test_needs_two_points(self):
        with pytest.raises(ValueError):
            se.one_sample_ttest([5], popmean=3)

class TestIndependentTTest:
    A = [1, 2, 3, 4, 5]
    B = [2, 3, 4, 5, 6]

    def test_welch_is_default(self):
        r = se.independent_ttest(self.A, self.B)
        assert r["t_stat"] == pytest.approx(-1.0)
        assert r["p_value"] == pytest.approx(0.34659350708733416)
        assert r["df"] == pytest.approx(8.0)
        assert_json_safe(r)

    def test_equal_var_matches_scipy(self):
        r = se.independent_ttest(self.A, self.B, equal_var=True)
        ref = sp.ttest_ind(self.A, self.B, equal_var=True)
        assert r["t_stat"] == pytest.approx(ref.statistic)
        assert r["p_value"] == pytest.approx(ref.pvalue)

    def test_clearly_different_groups_are_significant(self):
        a = [12, 15, 11, 14, 13, 16]
        b = [22, 25, 21, 24, 23, 26]
        r = se.independent_ttest(a, b)
        assert r["t_stat"] == pytest.approx(-9.258200997725515)
        assert r["p_value"] == pytest.approx(3.2065531538603353e-06)

    def test_swapping_groups_flips_sign_only(self):
        r1 = se.independent_ttest(self.A, self.B)
        r2 = se.independent_ttest(self.B, self.A)
        assert r1["t_stat"] == pytest.approx(-r2["t_stat"])
        assert r1["p_value"] == pytest.approx(r2["p_value"])

    def test_p_value_is_a_probability(self):
        r = se.independent_ttest([3, 9, 4, 8, 1], [7, 2, 6, 6, 5])
        assert 0.0 <= r["p_value"] <= 1.0

    def test_zero_variance_in_both_groups_gives_null_p(self):
        r = se.independent_ttest([5, 5, 5], [5, 5, 5])
        assert r["p_value"] is None
        assert_json_safe(r)

    def test_each_group_needs_two_points(self):
        with pytest.raises(ValueError):
            se.independent_ttest([1], [1, 2, 3])

class TestPairedTTest:
    def test_known_values(self):
        r = se.paired_ttest([1, 2, 3, 4, 5], [2, 4, 5, 4, 8])
        assert r["t_stat"] == pytest.approx(-3.1378581622109443)
        assert r["p_value"] == pytest.approx(0.03491970667453904)
        assert r["df"] == 4
        assert_json_safe(r)

    def test_length_mismatch_raises(self):
        with pytest.raises(ValueError):
            se.paired_ttest([1, 2, 3], [1, 2])

    def test_pairs_with_missing_values_are_dropped_together(self):
        # (3, None) and (None, 8) removed as pairs, leaving 3 usable pairs
        r = se.paired_ttest([1, 2, 3, None, 5], [2, 4, None, 4, 8])
        ref = sp.ttest_rel([1, 2, 5], [2, 4, 8])
        assert r["df"] == 2
        assert r["t_stat"] == pytest.approx(ref.statistic)

# --------------------------------------------------------------------------
# ANOVA
# --------------------------------------------------------------------------
class TestOneWayAnova:
    G1 = [6, 8, 4, 5, 3, 4]
    G2 = [8, 12, 9, 11, 6, 8]
    G3 = [13, 9, 11, 8, 7, 12]

    def test_known_values(self):
        r = se.one_way_anova(self.G1, self.G2, self.G3)
        assert r["f_stat"] == pytest.approx(9.264705882352942)
        assert r["p_value"] == pytest.approx(0.0023987773293929083)
        assert r["df_between"] == 2
        assert r["df_within"] == 15
        assert_json_safe(r)

    def test_identical_groups_not_significant(self):
        r = se.one_way_anova([1, 2, 3], [1, 2, 3], [1, 2, 3])
        assert r["f_stat"] == pytest.approx(0.0, abs=1e-12)
        assert r["p_value"] == pytest.approx(1.0)

    def test_needs_at_least_two_groups(self):
        with pytest.raises(ValueError):
            se.one_way_anova(self.G1)

# --------------------------------------------------------------------------
# Line of best fit
# --------------------------------------------------------------------------
class TestLinearFit:
    def test_perfect_line(self):
        r = se.linear_fit([1, 2, 3, 4, 5], [2, 4, 6, 8, 10])
        assert r["slope"] == pytest.approx(2.0)
        assert r["intercept"] == pytest.approx(0.0, abs=1e-12)
        assert r["r_squared"] == pytest.approx(1.0)
        assert r["p_value"] < 1e-6

    def test_known_noisy_values(self):
        # Hand check: Sxy=6, Sxx=10, Syy=6 -> slope .6, intercept 2.2, r^2 = 36/60
        r = se.linear_fit([1, 2, 3, 4, 5], [2, 4, 5, 4, 5])
        assert r["slope"] == pytest.approx(0.6)
        assert r["intercept"] == pytest.approx(2.2)
        assert r["r_squared"] == pytest.approx(0.6)
        assert r["r"] == pytest.approx(0.7745966692414833)
        assert r["p_value"] == pytest.approx(0.12402706265755467)
        assert r["std_err"] == pytest.approx(0.28284271247461906)
        assert r["n"] == 5
        assert_json_safe(r)

    def test_negative_slope(self):
        r = se.linear_fit([1, 2, 3, 4], [8, 6, 4, 2])
        assert r["slope"] == pytest.approx(-2.0)
        assert r["r"] == pytest.approx(-1.0)

    def test_length_mismatch_raises(self):
        with pytest.raises(ValueError):
            se.linear_fit([1, 2, 3], [1, 2])

    def test_constant_x_raises(self):
        with pytest.raises(ValueError):
            se.linear_fit([2, 2, 2, 2], [1, 2, 3, 4])

    def test_needs_three_points(self):
        with pytest.raises(ValueError):
            se.linear_fit([1, 2], [1, 2])

# --------------------------------------------------------------------------
# Normality + normal curve
# --------------------------------------------------------------------------
NORMAL_SAMPLE = np.random.default_rng(0).normal(50, 10, 200)
SKEWED_SAMPLE = np.random.default_rng(0).exponential(5, 200)

class TestNormalityTest:
    def test_normal_sample_passes(self):
        r = se.normality_test(NORMAL_SAMPLE)
        assert r["statistic"] == pytest.approx(0.9889611133726955)
        assert r["p_value"] == pytest.approx(0.12552461158219275)
        assert r["is_normal"] is True
        assert_json_safe(r)

    def test_skewed_sample_fails(self):
        r = se.normality_test(SKEWED_SAMPLE)
        assert r["p_value"] < 1e-6
        assert r["is_normal"] is False

    def test_alpha_controls_verdict(self):
        # p ~= 0.1255: normal at alpha .05, rejected at alpha .2
        assert se.normality_test(NORMAL_SAMPLE, alpha=0.05)["is_normal"] is True
        assert se.normality_test(NORMAL_SAMPLE, alpha=0.2)["is_normal"] is False

    def test_needs_three_points(self):
        with pytest.raises(ValueError):
            se.normality_test([1, 2])

class TestNormalFit:
    def test_parameters_use_sample_std(self):
        r = se.normal_fit(NORMAL_SAMPLE)
        assert r["mean"] == pytest.approx(50.15263139659941)
        assert r["std"] == pytest.approx(9.63590864449417)

    def test_curve_shape(self):
        r = se.normal_fit(NORMAL_SAMPLE, n_points=101)
        x, y = r["x"], r["pdf"]
        assert len(x) == len(y) == 101
        assert x == sorted(x)
        assert all(v >= 0 for v in y)
        # peak sits at the mean
        peak_x = x[int(np.argmax(y))]
        assert peak_x == pytest.approx(r["mean"], abs=r["std"] * 0.1)

    def test_pdf_matches_scipy(self):
        r = se.normal_fit(DATA, n_points=25)
        expected = sp.norm.pdf(r["x"], loc=r["mean"], scale=r["std"])
        assert r["pdf"] == pytest.approx(list(expected))

    def test_curve_covers_the_distribution(self):
        r = se.normal_fit(NORMAL_SAMPLE, n_points=400)
        area = np.trapezoid(r["pdf"], r["x"])
        assert area == pytest.approx(1.0, abs=0.01)  # curve spans >= +/-4 std

    def test_json_safe(self):
        assert_json_safe(se.normal_fit(DATA))

    def test_zero_variance_raises(self):
        with pytest.raises(ValueError):
            se.normal_fit([5, 5, 5, 5])

class TestHistogram:
    def test_known_bins(self):
        r = se.histogram([1, 2, 2, 3, 3, 3, 4, 4, 4, 4], bins=4)
        assert r["edges"] == pytest.approx([1, 1.75, 2.5, 3.25, 4])
        assert r["counts"] == [1, 2, 3, 4]

    def test_counts_sum_to_n_and_edges_length(self):
        r = se.histogram(NORMAL_SAMPLE, bins=12)
        assert sum(r["counts"]) == 200
        assert len(r["edges"]) == 13
        assert len(r["counts"]) == 12

    def test_density_integrates_to_one(self):
        r = se.histogram(NORMAL_SAMPLE, bins=12)
        widths = np.diff(r["edges"])
        assert float(np.sum(np.array(r["density"]) * widths)) == pytest.approx(1.0)

    def test_json_safe(self):
        assert_json_safe(se.histogram(DATA, bins=3))