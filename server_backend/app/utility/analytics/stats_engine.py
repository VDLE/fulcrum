#stats_engine.py: should be used to make calculations for mean, median, mode, range, SD, t-test or ANOVA, linregress for line of best fit
#Shapiro-Wilk, and a normal-curve fit.

from collections import Counter
from math import isfinite, isnan, sqrt
from statistics import mean, median, quantiles, variance


def _numeric_values(values):
    """Drop missing data and convert array scalars to Python numbers."""
    numbers = []
    for value in values:
        if value is None:
            continue
        number = float(value)
        if isnan(number):
            continue
        # Infinity cannot be represented in a strict JSON response.
        if not isfinite(number):
            raise ValueError("Values must be finite")
        numbers.append(number)

    if not numbers:
        raise ValueError("At least one numeric value is required")
    return numbers


def _modes(numbers):
    """Return all repeated values tied for the highest frequency."""
    counts = Counter(numbers)
    highest_frequency = max(counts.values())
    if highest_frequency == 1:
        return []
    return sorted(number for number, count in counts.items() if count == highest_frequency)


def describe(values):
    """Summarize one numeric sample using JSON-safe Python values."""
    numbers = _numeric_values(values)
    n = len(numbers)
    minimum = min(numbers)
    maximum = max(numbers)

    # Sample variance divides by n - 1. A single value has no sample variance.
    sample_variance = variance(numbers) if n > 1 else None
    standard_deviation = sqrt(sample_variance) if sample_variance is not None else None

    # Inclusive quartiles interpolate at positions 0.25 and 0.75 times (n - 1).
    q1, _, q3 = quantiles(numbers, method="inclusive") if n > 1 else (minimum,) * 3

    return {
        "n": n,
        "mean": mean(numbers),
        "median": median(numbers),
        "min": minimum,
        "max": maximum,
        "range": maximum - minimum,
        "variance": sample_variance,
        "std": standard_deviation,
        "mode": _modes(numbers),
        "q1": q1,
        "q3": q3,
        "iqr": q3 - q1,
    }


def mode(values):
    """Return the sorted modes of one numeric sample."""
    return _modes(_numeric_values(values))

def one_sample_ttest(DATA, mu): #needs pval, degrees of freedom (df), and t_stat
    pass

#the following values should have equal_var be default true if no value is provided, see how python does this.
def independent_ttest(DATA1, DATA2, equal_var):
    equal_var = True #for testing purposes, we will assume equal variance. This can be changed later if needed.
    pass

def paired_ttest(DATA1, DATA2): #needs pval, t_stat, df, and confidence interval
    pass

def one_way_anova(DATA1, DATA2, DATA3): #needs pval, f_stat, df_between, df_within
    pass

def linear_fit(DATA1, DATA2): #needs slope, intercept, r_value, p_value, std_err, r squared, and n from describe (use callbacks!)
    pass

def normality_test(DATA): #Shapiro-Wilk test, needs pval and W statistic
    pass

def histogram(DATA): #needs edges, counts, and density
    pass



