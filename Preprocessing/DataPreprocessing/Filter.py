from sklearn.base import TransformerMixin
import numpy as np
import scipy.signal as sig
import pandas as pd

from ModelTraining.datamodels.datamodels.processing.feature_extension.StoreInterface import StoreInterface


class Filter(TransformerMixin, StoreInterface):
    """
    Signal filter - based on sklearn TransformerMixin. Can be stored to pickle file (StoreInterface).
    Options:
        - keep_nans: Filtered signal still keeps NaN values from original signals
        - remove_offset: Remove offset from signal before filtering, apply offset afterwards
    """
    keep_nans = False
    mask_nan = None
    remove_offset = False
    offset = None
    coeffs = [[0], [0]]

    def __init__(self, remove_offset=False, keep_nans=False, **kwargs):
        self._set_attrs(remove_offset=remove_offset, keep_nans=keep_nans)

    def fit_transform(self, X, y=None, **fit_params):
        """
        Fit transformer - Overrides TransformerMixin method.
        @param x: Input feature vector (n_samples, n_features)
        @param y: Target feature vector (n_samples)
        """
        if self.remove_offset:
            self.offset = np.nanmean(X, axis=0)
            X = X - self.offset
        if self.keep_nans:
            self.mask_nan = X.isna()
            X = np.nan_to_num(X)
        x_filt = self._fit_transform(X)
        if self.remove_offset:
            x_filt = x_filt + self.offset
        if self.keep_nans:
            x_filt[self.mask_nan is True] = np.nan
        return x_filt

    def _fit_transform(self, X, y=None, **fit_params):
        """
        Filter signal. Override if necessary.
        @param x: Input feature vector (n_samples, n_features)
        @param y: Target feature vector (n_samples)
        """
        return sig.lfilter(*self.coeffs, X, axis=0)


class ButterworthFilter(Filter):
    """
    Butterworth lowpass filter for data smoothing.
    """
    T = 10
    order = 2

    def __init__(self, T=10, order=2, **kwargs):
        super().__init__(**kwargs)
        self._set_attrs(T=T, order=order)
        self.coeffs = sig.butter(self.order, 1 / T)


class ChebyshevFilter(Filter):
    """
       Chebyshev lowpass filter for data smoothing.
    """
    T = 10
    order = 2
    ripple = 0.1
    coeffs = None

    def __init__(self, T=10, order=2, ripple=0.1, **kwargs):
        super().__init__(**kwargs)
        self._set_attrs(T=T, order=order, ripple=ripple)
        self.coeffs = sig.cheby1(self.order, ripple, 1 / T)


class Envelope_MA(Filter):
    """
        Envelope detector through moving average (parameter T of moving average filter can be set)
    """
    T = 10
    envelope_h = None
    envelope_l = None
    envelope_avg = None

    def __init__(self, T=10, **kwargs):
        super().__init__(**kwargs)
        self._set_attrs(T=T)

    def _fit_transform(self, X, y=None, **fit_params):
        """
        Calculate envelope.
        This is taken from https://stackoverflow.com/a/69357933
        @param x: Input feature vector (n_samples, n_features)
        @param y: Target feature vector (n_samples)
        """
        X_df = pd.DataFrame(X)
        self.envelope_h = X_df.rolling(window=self.T).max().shift(int(-self.T / 2))
        self.envelope_l = X_df.rolling(window=self.T).min().shift(int(-self.T / 2))
        self.envelope_avg = np.mean(np.dstack((self.envelope_l, self.envelope_h)),axis=-1)
        return self.envelope_avg

    def get_max_env(self):
        """
            Get upper bound of envelope
        """
        return self.envelope_h

    def get_min_env(self):
        """
        Get lower bound of envelope
        """
        return self.envelope_l

