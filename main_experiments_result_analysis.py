from ModelTraining.Training.TrainingUtilities.trainingparams_expanded import TrainingParamsExpanded
from ModelTraining.Utilities import TrainingData
from ModelTraining.feature_engineering.featureengineering.featureselectors import FeatureSelector
from ModelTraining.feature_engineering.featureengineering.featureexpanders import FeatureExpansion
from ModelTraining.Utilities.MetricsExport.metrics_calc import MetricsCalc
from ModelTraining.Utilities.MetricsExport.result_export import ResultExport
from ModelTraining.Training.TrainingUtilities.training_utils import load_from_json
from ModelTraining.Data.DataImport.featureset.featureset import FeatureSet
from ModelTraining.datamodels.datamodels.wrappers.expandedmodel import ExpandedModel
import os
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--usecase_names", type=str, default='CPS-Data,SensorA6,SensorB2,SensorC6,Solarhouse1,Solarhouse2')
    parser.add_argument("--model_types", type=str, default='RidgeRegression,LassoRegression,PLSRegression,RandomForestRegression')
    args = parser.parse_args()
    model_types = model_names = args.model_types.split(",")
    list_usecases = args.usecase_names.split(",")
    data_dir = "../"
    root_dir = "./"
    plot_enabled = False

    # Model parameters and expansion parameters
    parameters_full = {model_type: load_from_json(os.path.join(root_dir, 'Configuration/GridSearchParameters', f'parameters_{model_type}.json')) for model_type in model_types}
    expander_parameters = load_from_json(os.path.join(root_dir, 'Configuration','expander_params_PolynomialExpansion.json' ))

    selected_thresh = "rdc"
    transf_cfg_files = [f"train_params_{selected_thresh}_0_05_{expansion_type}_r_0_05.json" for expansion_type in
                        ['basic', 'poly']]
    list_train_params = [
        TrainingParamsExpanded.load(os.path.join(root_dir, "Configuration", "TrainingParameters", file)) for file in
        transf_cfg_files]
    params_names = [f'{selected_thresh}-value_0.05_R-value_0.05']

    # Use cases
    config_path = os.path.join(root_dir, 'Configuration')
    dict_usecases = [load_from_json(os.path.join(config_path,"UseCaseConfig", f"{name}.json")) for name in
                     list_usecases]


    # Results output
    timestamp = "Experiment_20220919_114519"
    results_path = os.path.join(root_dir, 'results', timestamp)
    os.makedirs(results_path, exist_ok=True)
    metrics_path = os.path.join(root_dir, 'results', timestamp, 'Metrics')
    os.makedirs(metrics_path, exist_ok=True)
    metrics_names = {'FeatureSelect': ['selected_features', 'all_features'], 'Metrics': ['rsquared', 'cvrmse', 'mape'], 'pvalues': ['pvalue_lm', 'pvalue_f']}

# %%
    print('Analyzing results')
    metr_exp = MetricsCalc(metr_names=metrics_names)
    for dict_usecase in dict_usecases:
        usecase_name = dict_usecase['name']
        feature_set = FeatureSet(os.path.join(root_dir,"Data", "Configuration", "FeatureSet", dict_usecase['fmu_interface']))
        for params_name in params_names:
            result_exp = ResultExport(results_root=os.path.join(results_path, usecase_name, params_name),
                                      plot_enabled=True)
            for training_params in list_train_params:
                for model_type in model_types:
                    for feat in feature_set.get_output_feature_names():
                        # Load results
                        result = TrainingData.load_pkl(result_exp.results_root,
                                                          f'results_{model_type}_{feat}_{training_params.str_expansion(range=[2,-1])}.pkl') # TODO fix this
                        model_dir = os.path.join(result_exp.results_root,
                                                 f'Models/{feat}/{model_type}_{training_params.str_expansion(range=[2,-1])}/{feat}')
                        model = ExpandedModel.load_pkl(model_dir, "expanded_model.pkl")
                        result_exp.export_result_full(model, result, training_params.str_expansion(range=[2,-1]))
                        # Calculate metrics
                        selectors = model.transformers.get_transformers_of_type(FeatureSelector)
                        metr_vals = metr_exp.calc_all_metrics(result, selectors, model.get_num_predictors())
                        # Set metrics identifiers
                        for metr_val in metr_vals:
                            metr_val.set_metr_properties(model_type, model.name,
                                                         model.transformers.type_last_transf(FeatureExpansion),
                                                         params_name, usecase_name)
                        metr_exp.add_metr_vals(metr_vals)
    metr_exp.store_all_metrics(results_path=metrics_path, timestamp=timestamp)
    print('Result analysis finished')