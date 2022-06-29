from abc import abstractmethod
from scipy import signal as sig

from sklearn.base import TransformerMixin, BaseEstimator
from .compensators import OffsetComp, NaNComp
from ..interfaces import BaseFitTransform, MaskFeats, PickleInterface


class Filter(MaskFeats, BaseFitTransform, PickleInterface, TransformerMixin):
    """
    Signal filter - based on sklearn TransformerMixin. Can be stored to pickle file.
    Options:
        - keep_nans: Filtered signal still keeps NaN values from original signals
        - remove_offset: Remove offset from signal before filtering, apply offset afterwards
    """
    offset_comp = None
    nan_comp = None
    coef_ = [[0], [0]]

    def __init__(self, remove_offset=False, keep_nans=False, **kwargs):
        MaskFeats.__init__(self, **kwargs)
        self.offset_comp = OffsetComp(remove_offset)
        self.nan_comp = NaNComp(keep_nans)

    def fit(self, X, y=None, **fit_params):
        return super().fit(self.mask_feats(X))

    def _fit(self, X, y=None, **fit_params):
        self.coef_ = self.calc_coef(X, y, **fit_params)

    def transform(self, X):
        """
        Filter signal
        @param x: Input feature vector (n_samples, n_features)
        """
        X_masked = self.mask_feats(X)
        # Remove offset and NaNs
        X_to_filter = self.nan_comp.fit_transform(self.offset_comp.fit_transform(X_masked))
        # Transform features
        x_filt = self._transform(X_to_filter)
        # Apply NaNs and offset
        x_filt = self.offset_comp.inverse_transform(self.nan_comp.inverse_transform(x_filt))
        return self.combine_feats(x_filt, X)

    def _transform(self, X):
        """
        Filter signal. Override if necessary.
        @param x: Input feature vector (n_samples, n_features)
        @param y: Target feature vector (n_samples)
        """
        return sig.lfilter(*self.coef_, X, axis=0)

    def get_coef(self):
        """
        Get filter coefficients.
        """
        return self.coef_

    @abstractmethod
    def calc_coef(self, X, y=None, **fit_params):
        """
        Override this method to create filter coeffs.
        """
        raise NotImplementedError
