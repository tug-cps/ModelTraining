import logging
from .TrainingUtilities import training_utils as train_utils
from .predict import predict_with_history
from .GridSearch import best_estimator
from ..Training.TrainingUtilities.parameters import TrainingParams
from ..Training.TrainingUtilities.trainingparams_expanded import TrainingParamsExpanded
from ..datamodels.datamodels.processing import datascaler
from ..datamodels import datamodels
from ..datamodels.datamodels.wrappers.expandedmodel import ExpandedModel, TransformerSet


def run_training_model(data, training_params=TrainingParams(), model_parameters={}, prediction_type='History'):
    """
        Function: run training and test - Train models based on training data.
        Includes:
            Train-test split
            Feature expansion
            Feature selection
            Grid search
            Prediction

        Parameters:
            @param data: data to run training on
            @param training_params: list of training parameters
            @param prediction_type: Type of prediction - choose 'History' or 'ground truth'
            @param model_parameters: parameters for grid search

        Returns:
            @return model, prediction result: model, Training results
        """
    create_df = True if isinstance(training_params, TrainingParamsExpanded) else False
    index, x, y, feature_names = train_utils.extract_training_and_test_set(data, training_params,create_df=create_df)
    train_data = train_utils.create_train_data(index, x, y, training_split=training_params.training_split)
    index_train, x_train, y_train = train_data.train_index, train_data.train_input, train_data.train_target
    index_test, x_test, y_test = train_data.test_index, train_data.test_input, train_data.test_target
    # Create model
    logging.info(f"Training model with input of shape: {x_train.shape} and targets of shape {y_train.shape}")
    model = getattr(datamodels, training_params.model_type)(
                                  x_scaler_class=getattr(datascaler, training_params.normalizer),
                                  name=training_params.str_target_feats(),
                                  parameters={})
    # Create expanded model wrapper
    if isinstance(training_params, TrainingParamsExpanded):
        model = ExpandedModel(transformers=TransformerSet.from_list_params(training_params.transformer_params),
                              model=model, feature_names=feature_names)
    # Select features + Grid Search
    best_params = best_estimator(model, x_train, y_train, parameters=model_parameters)
    if isinstance(model, ExpandedModel):
        model.get_estimator().set_params(**best_params)
    else:
        model.model.set_params(**best_params)
    # Train final model
    model.train(x_train, y_train)
    # Predict test data
    y_pred = predict_with_history(model, index_test, x_test, y_test, training_params) \
        if prediction_type == 'History' else model.predict(x_test)

    train_data.test_prediction = y_pred
    return model, train_data