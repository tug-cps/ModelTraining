import os
import pandas as pd

from typing import List
from .metrics_vals import MetricsVal, MetrValsSet
from ...datamodels.datamodels.wrappers.feature_extension import ExpandedModel
from ...datamodels.datamodels.validation import metrics
from ...datamodels.datamodels.validation.white_test import white_test
from ..Parameters.trainingresults import TrainingResults
from ...Preprocessing.FeatureSelection.feature_selectors import FeatureSelector


class MetricsCalc:
    metr_names = {'Metrics': ['R2', 'CV-RMS', 'MAPE'],
                  'FeatureSelect': ['selected_features', 'all_features'],
                  'pvalues': ['pvalue_lm']}
    metr_vals: MetrValsSet = MetrValsSet()

    def __init__(self, metr_names=None):
        if metr_names is not None:
            self.metr_names = metr_names

    ################################# Metrics calculation #############################################################

    def calc_perf_metrics(self, result: TrainingResults, n_predictors=0):
        n_samples = result.train_index.shape[0] + result.test_index.shape[0]
        list_metrs = []
        for feat in result.target_feat_names:
            y_true = result.test_target_vals(feat)
            y_pred = result.test_pred_vals(feat)
            # Get metrics
            metrs = metrics.all_metrics(y_true=y_true, y_pred=y_pred)
            # Additional metrics
            if 'RA' in self.metr_names['Metrics']:
                metrs.update({"RA": metrics.rsquared_adj(y_true, y_pred, n_samples, n_predictors)})
            if 'RA_SKLEARN' in self.metr_names['Metrics']:
                metrs.update(
                    {"RA_SKLEARN": metrics.rsquared_sklearn_adj(y_true, y_pred, n_samples, n_predictors)})
            for k, v in metrs.items():
                if k in self.metr_names['Metrics']:
                    list_metrs.append(MetricsVal(metrics_type='Metrics', metrics_name=k, val=v, target_feat=feat))
        return list_metrs

    def analyze_featsel(self, selectors):
        """
        Analyze feature selection
        @param selectors: List of selectors
        @return: pd.DataFrame containing results
        """
        list_metrs = []
        for i, selector in enumerate(selectors):
            sel_metrs = selector.get_metrics()
            selector_name = f'{selector.__class__.__name__}_{i}'
            for k, v in sel_metrs.items():
                list_metrs.append(MetricsVal(metrics_type='FeatureSelect', metrics_name=f'{selector_name}_{k}', val=v))
        return list_metrs

    def white_test(self, result: TrainingResults):
        """
        White test for all target features in the training result.
        @param result: TrainingResult structure
        @param selected_metrics: Selected metrics for white test. Supported: 'pvalue_lm', 'pvalue_f'
        """
        list_metr_vals = []
        for feat in result.target_feat_names:
            white_pvals = white_test(result.test_input, result.test_target_vals(feat) - result.test_pred_vals(feat))
            for k, v in white_pvals.items():
                if k in self.metr_names['pvalues']:
                    list_metr_vals.append(MetricsVal(metrics_type='pvalues', metrics_name=k, val=v, target_feat=feat))
        return list_metr_vals

    ####################################  Dataframe ###################################################################

    def white_test_df(self, result: TrainingResults, df_index=None):
        """
        White test for all target features in the training result.
        @param result: TrainingResult structure
        @param selected_metrics: Selected metrics for white test. Supported: 'pvalue_lm', 'pvalue_f'
        @param df_index: Optional: index for dataframe
        """
        df_white = pd.DataFrame()
        for feat in result.target_feat_names:
            white_pvals = white_test(result.test_input, result.test_target_vals(feat) - result.test_pred_vals(feat))
            df_white_feat = pd.DataFrame(data=white_pvals.values(), index=white_pvals.keys()).transpose()[self.metr_names['pvalues']].add_suffix(f'_{feat}')
            df_white = df_white_feat if df_white.empty else df_white.join(df_white_feat)
        if df_index is not None:
            df_white.index = df_index
        return df_white

    def calc_perf_metrics_df(self, result: TrainingResults, n_predictors=0, df_index=None):
        """
        Calculate metrics
        @param result: TrainingResults structure
        @param n_predictors: number of predictors - only used for R_adj metric
        @param df_index: Optional: index for dataframe
        @return pd.Dataframe containing metrics
        """
        n_samples = result.train_index.shape[0] + result.test_index.shape[0]
        df_metrs = pd.DataFrame()
        for feat in result.target_feat_names:
            y_true = result.test_target_vals(feat)
            y_pred = result.test_pred_vals(feat)
            # Get metrics
            metrs = metrics.all_metrics(y_true=y_true, y_pred=y_pred)
            # Additional metrics
            if 'RA' in self.metr_names['Metrics']:
                metrs.update({"RA": metrics.rsquared_adj(y_true, y_pred, n_samples, n_predictors)})
            if 'RA_SKLEARN' in self.metr_names['Metrics']:
                metrs.update(
                    {"RA_SKLEARN": metrics.rsquared_sklearn_adj(y_true, y_pred, n_samples, n_predictors)})
            metrs = {k: v for k, v in metrs.items() if k in self.metr_names['Metrics']}
            df_metrs_feat = pd.DataFrame(data=metrs.values(), index=metrs.keys()).transpose()[self.metr_names['Metrics']].add_suffix(f'_{feat}')
            df_metrs = df_metrs_feat if df_metrs.empty else df_metrs.join(df_metrs_feat)
        if df_index is not None:
            df_metrs.index = df_index
        return df_metrs

    def analyze_featsel_df(self, model: ExpandedModel, selectors: List[FeatureSelector], df_index=None):
        """
        Analyze feature selection
        @param model: Model to analyze - expanders are needed to get feature names
        @param selectors: List of selectors
        @param df_index: Optional: index for dataframe
        @return: pd.DataFrame containing results
        """
        model_name = f'{model.name}_{model.transformers.type_transf_full()}'
        df_featsel_full = pd.DataFrame()
        for i, selector in enumerate(selectors):
            sel_metrs = selector.get_metrics()
            selector_name = f'{selector.__class__.__name__}_{i}'
            df_featsel = pd.DataFrame(data=sel_metrs.values(), index=sel_metrs.keys()).transpose()
            df_featsel = df_featsel[self.metr_names['FeatureSelect']].add_suffix(f'_{selector_name}_{model_name}_FeatureSelect')
            df_featsel_full = df_featsel if df_featsel_full.empty else df_featsel_full.join(df_featsel)
        df_featsel_full.index = [model.__class__.__name__]
        if df_index is not None:
            df_featsel_full.index = df_index
        return df_featsel_full

    ############################################# Store metrics ########################################################

    def add_metr_val(self, metr_val: MetricsVal):
        """
        Add metrics to internal metrics set
        @param metr_val: MetricsVal struct
        """
        self.metr_vals.add_metr_val(metr_val)

    def add_metr_vals(self, metrs: List[MetricsVal]):
        """
        Add metrics to internal metrics set
        @param metrs: list of metrics
        """
        self.metr_vals.add_metr_vals(metrs)

    def get_metr_df(self):
        """
        Get dataframe containing currently stored metrics
        @return: pd Dataframe
        """
        return self.metr_vals.create_df_metrics()

    def store_all_metrics(self, results_path="./", timestamp=""):
        """
        Store metrics df to files - get subsets of dataframes to store separately
        @param results_path: result dir - optional argument
        @param timestamp: timestamp of experiment
        """
        df_metrs = self.metr_vals.create_df_metrics("")
        df_metrs.to_csv(os.path.join(results_path, f'AllMetrics_full_{timestamp}.csv'),index_label='Model', float_format='%.3f')

        # Get subsets
        df_metrics = self.metr_vals.create_df_metrics('Metrics')
        df_featsel = self.metr_vals.create_df_metrics('FeatureSelect')
        df_whitetest = self.metr_vals.create_df_metrics('pvalues')

        # Store results
        for df, filename in zip([df_metrics, df_featsel, df_whitetest], ['Metrics','feature_select','whitetest']):
            if not df.empty:
                df.to_csv(os.path.join(results_path, f'{filename}_full_{timestamp}.csv'),index_label='Model', float_format='%.3f')
        # Store single metrics separately
        for name in self.metr_names['Metrics']:
            columns = [column for column in df_metrics.columns if name in column]
            df_metrics[columns].to_csv(os.path.join(results_path, f'Metrics_{timestamp}_{name}.csv'),index_label='Model', float_format='%.3f')