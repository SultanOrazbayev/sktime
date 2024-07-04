"""Forecasting benchmarks tests."""

import os

import pandas as pd
import pytest

from sktime.benchmarking.benchmarks import coerce_estimator_and_id
from sktime.benchmarking.forecasting import ForecastingBenchmark
from sktime.forecasting.naive import NaiveForecaster
from sktime.forecasting.trend import TrendForecaster
from sktime.performance_metrics.forecasting import (
    MeanAbsoluteError,
    MeanAbsolutePercentageError,
    MeanSquaredPercentageError,
)
from sktime.split import ExpandingWindowSplitter
from sktime.tests.test_switch import run_test_module_changed

EXPECTED_RESULTS_1 = pd.DataFrame(
    data={
        "validation_id": "[dataset=data_loader_simple]_"
        + "[cv_splitter=ExpandingWindowSplitter]",
        "model_id": "NaiveForecaster",
        "MeanSquaredPercentageError_fold_0_test": 0.0,
        "MeanSquaredPercentageError_fold_1_test": 0.111,
        "MeanSquaredPercentageError_mean": 0.0555,
        "MeanSquaredPercentageError_std": 0.0785,
    },
    index=[0],
)
EXPECTED_RESULTS_2 = pd.DataFrame(
    data={
        "validation_id": "[dataset=data_loader_simple]_"
        + "[cv_splitter=ExpandingWindowSplitter]",
        "model_id": "NaiveForecaster",
        "MeanAbsolutePercentageError_fold_0_test": 0.0,
        "MeanAbsolutePercentageError_fold_1_test": 0.333,
        "MeanAbsolutePercentageError_mean": 0.1666,
        "MeanAbsolutePercentageError_std": 0.2357,
        "MeanAbsoluteError_fold_0_test": 0.0,
        "MeanAbsoluteError_fold_1_test": 1.0,
        "MeanAbsoluteError_mean": 0.5,
        "MeanAbsoluteError_std": 0.7071,
    },
    index=[0],
)

COER_CASES = [
    (
        NaiveForecaster(),
        "NaiveForecaster",
        {"NaiveForecaster": NaiveForecaster()},
    ),
    (NaiveForecaster(), None, {"NaiveForecaster": NaiveForecaster()}),
    (
        [NaiveForecaster(), TrendForecaster()],
        None,
        {
            "NaiveForecaster": NaiveForecaster(),
            "TrendForecaster": TrendForecaster(),
        },
    ),
    (
        {"estimator_1": NaiveForecaster()},
        None,
        {"estimator_1": NaiveForecaster()},
    ),
]


def data_loader_simple() -> pd.DataFrame:
    """Return simple data for use in testing."""
    return pd.DataFrame([2, 2, 3])


@pytest.mark.skipif(
    not run_test_module_changed("sktime.benchmarking"),
    reason="run test only if benchmarking module has changed",
)
@pytest.mark.parametrize(
    "expected_results_df, scorers",
    [
        (EXPECTED_RESULTS_1, [MeanSquaredPercentageError()]),
        (EXPECTED_RESULTS_2, [MeanAbsolutePercentageError(), MeanAbsoluteError()]),
    ],
)
def test_forecastingbenchmark(tmp_path, expected_results_df, scorers):
    """Test benchmarking a forecaster estimator."""
    benchmark = ForecastingBenchmark()

    benchmark.add_estimator(NaiveForecaster(strategy="last"))

    cv_splitter = ExpandingWindowSplitter(
        initial_window=1,
        step_length=1,
        fh=1,
    )
    benchmark.add_task(data_loader_simple, cv_splitter, scorers)

    results_file = tmp_path / "results.csv"
    artefacts_store_dir = tmp_path / "artefacts"
    results_df = benchmark.run(results_file, artefacts_store_dir)
    assert os.path.exists(artefacts_store_dir)
    # For each fold and scorer predictions and ground truth should be stored
    for i in range(2):
        for scorer in scorers:
            assert os.path.exists(
                os.path.join(
                    artefacts_store_dir,
                    "[dataset=data_loader_simple]_"
                    + "[cv_splitter=ExpandingWindowSplitter]",
                    "NaiveForecaster",
                    "y_pred",
                    f"{scorer.name}_fold_{i}.csv",
                )
            )
            assert os.path.exists(
                os.path.join(
                    artefacts_store_dir,
                    "[dataset=data_loader_simple]_"
                    + "[cv_splitter=ExpandingWindowSplitter]",
                    "NaiveForecaster",
                    "y_test",
                    f"{scorer.name}_fold_{i}.csv",
                )
            )

    results_df = results_df.drop(columns=["runtime_secs"])

    pd.testing.assert_frame_equal(
        expected_results_df, results_df, check_exact=False, atol=0, rtol=0.001
    )


@pytest.mark.skipif(
    not run_test_module_changed("sktime.benchmarking"),
    reason="run test only if benchmarking module has changed",
)
@pytest.mark.parametrize("estimator, estimator_id, expected_output", COER_CASES)
def test_coerce_estimator_and_id(estimator, estimator_id, expected_output):
    """Test coerce_estimator_and_id return expected output."""
    assert (
        coerce_estimator_and_id(estimator, estimator_id) == expected_output
    ), "coerce_estimator_and_id does not return the expected output."


@pytest.mark.skipif(
    not run_test_module_changed("sktime.benchmarking"),
    reason="run test only if benchmarking module has changed",
)
@pytest.mark.parametrize(
    "estimators",
    [
        ({"N": NaiveForecaster(), "T": TrendForecaster()}),
        ([NaiveForecaster(), TrendForecaster()]),
    ],
)
def test_multiple_estimators(estimators):
    """Test add_estimator with multiple estimators."""
    # single estimator test is checked in test_forecastingbenchmark
    benchmark = ForecastingBenchmark()
    benchmark.add_estimator(estimators)
    registered_estimators = benchmark.estimators.entity_specs.keys()
    assert len(registered_estimators) == len(
        estimators
    ), "add_estimator does not register all estimators."
