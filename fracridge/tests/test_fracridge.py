import numpy as np
from fracridge import fracridge, vec_len, FracRidge, FracRidgeCV
from sklearn.utils.estimator_checks import check_estimator
import pytest


def run_fracridge(X, y, fracs, jit):
    fracridge(X, y, fracs=fracs, jit=jit)


@pytest.mark.parametrize("nn, pp", [(1000, 10), (10, 100)])
@pytest.mark.parametrize("bb", [(1), (2)])
@pytest.mark.parametrize("jit", [True, False])
def test_benchmark_fracridge(nn, pp, bb, jit, benchmark):
    X, y, _, _ = make_data(nn, pp, bb)
    fracs = np.arange(.1, 1.1, .1)
    benchmark(run_fracridge, X, y, fracs, jit)


def make_data(nn, pp, bb, fit_intercept=False):
    np.random.seed(1)
    X = np.random.randn(nn, pp)
    y = np.random.randn(nn, bb).squeeze()
    if fit_intercept:
        X = np.hstack([X, np.ones(X.shape[0])[:, np.newaxis]])
    coef_ols = np.linalg.pinv(X.T @ X) @ X.T @ y
    pred_ols = X @ coef_ols
    if fit_intercept:
        coef_ols = coef_ols[:-1]
        X = X[:, :-1]
    return X, y, coef_ols, pred_ols


@pytest.mark.parametrize("nn, pp", [(1000, 10), (10, 100)])
@pytest.mark.parametrize("bb", [(1), (2)])
def test_fracridge_ols(nn, pp, bb):
    X, y, coef_ols, _ = make_data(nn, pp, bb)
    fracs = np.arange(.1, 1.1, .1)
    coef, alpha = fracridge(X, y, fracs=fracs)
    coef = coef[:, -1, ...]
    assert np.allclose(coef, coef_ols, atol=10e-3)
    assert np.all(np.diff(alpha, axis=0) <= 0)


@pytest.mark.parametrize("frac", [0.1, 0.23, 1])
@pytest.mark.parametrize("nn, pp", [(1000, 10), (10, 100)])
@pytest.mark.parametrize("bb", [(1), (2)])
def test_fracridge_fracs(frac, nn, pp, bb):
    X, y, coef_ols, _ = make_data(nn, pp, bb)
    # Make sure that you get the fraction you asked for
    coef, _ = fracridge(X, y, fracs=np.array([frac]))
    assert np.all(
        np.abs(
            frac -
            vec_len(coef, axis=0) / vec_len(coef_ols, axis=0)) < 0.01)

def test_FracRidge_estimator():
    check_estimator(FracRidge())
    check_estimator(FracRidgeCV())

@pytest.mark.parametrize("nn, pp", [(1000, 10), (10, 100)])
@pytest.mark.parametrize("bb", [(1), (2)])
@pytest.mark.parametrize("fit_intercept", [False])
def test_FracRidge_ols(nn, pp, bb, fit_intercept):
    X, y, coef_ols, _ = make_data(nn, pp, bb)
    fracs = np.arange(.1, 1.1, .1)
    FR = FracRidge(fracs=fracs, fit_intercept=fit_intercept)
    FR.fit(X, y)
    assert np.allclose(FR.coef_[:, -1, ...], coef_ols, atol=10e-3)


@pytest.mark.parametrize("nn, pp", [(1000, 10), (10, 100)])
@pytest.mark.parametrize("bb", [(1), (2)])
@pytest.mark.parametrize("frac", [0.1, 0.23, 1])
def test_FracRidge_fracs(nn, pp, bb, frac):
    X, y, coef_ols, _ = make_data(nn, pp, bb)
    FR = FracRidge(fracs=frac)
    FR.fit(X, y)
    assert np.all(
        np.abs(
            frac -
            vec_len(FR.coef_, axis=0) / vec_len(coef_ols, axis=0)) < 0.01)


@pytest.mark.parametrize("nn, pp", [(1000, 10), (10, 100)])
@pytest.mark.parametrize("bb", [(1), (2)])
@pytest.mark.parametrize("fit_intercept", [True, False])
@pytest.mark.parametrize("jit", [True, False])
def test_FracRidge_predict(nn, pp, bb, fit_intercept, jit):
    X, y, coef_ols, pred_ols = make_data(nn, pp, bb, fit_intercept)
    fracs = np.arange(.1, 1.1, .1)
    FR = FracRidge(fracs=fracs, fit_intercept=fit_intercept, jit=jit)
    FR.fit(X, y)
    pred_fr = FR.predict(X)
    assert np.allclose(pred_fr[:, -1, ...], pred_ols, atol=10e-3)


# @pytest.mark.parametrize("nn, pp", [(1000, 10), (10, 100)])
# @pytest.mark.parametrize("bb", [(1), (2)])
# @pytest.mark.parametrize("fit_intercept", [True, False])
# @pytest.mark.parametrize("jit", [True, False])
# def test_FracRidge_predict(nn, pp, bb, fit_intercept, jit):
#     X, y, coef_ols, pred_ols = make_data(nn, pp, bb, fit_intercept)
#     frac_grid = np.arange(.1, 1.1, .1)
#     FR = FracRidgeCV(frac_grid=frac_grid, fit_intercept=fit_intercept, jit=jit)
#     FR.fit(X, y)
#     pred_fr = FR.predict(X)
#     assert np.allclose(pred_fr[:, -1, ...], pred_ols, atol=10e-3)


def test_FracRidge_singleton_frac():
    X = np.array([[1.64644051],
                  [2.1455681]])
    y = np.array([1., 2.])
    fracs = 0.1
    FR = FracRidge(fracs=fracs)
    FR.fit(X, y)
    pred_fr = FR.predict(X)
    assert pred_fr.shape == y.shape