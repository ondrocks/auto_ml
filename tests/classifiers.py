import datetime
import os
import random
import sys
sys.path = [os.path.abspath(os.path.dirname(__file__))] + sys.path

from auto_ml import Predictor
from auto_ml.utils_models import load_ml_model


import dill
import numpy as np
import pandas as pd
from nose.tools import assert_equal, assert_not_equal, with_setup
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

import utils_testing as utils

def optimize_final_model_classification(model_name=None):
    np.random.seed(0)

    df_titanic_train, df_titanic_test = utils.get_titanic_binary_classification_dataset()

    column_descriptions = {
        'survived': 'output'
        , 'embarked': 'categorical'
        , 'pclass': 'categorical'
    }

    ml_predictor = Predictor(type_of_estimator='classifier', column_descriptions=column_descriptions)

    ml_predictor.train(df_titanic_train, optimize_final_model=True, model_names=model_name)

    test_score = ml_predictor.score(df_titanic_test, df_titanic_test.survived)

    print('test_score')
    print(test_score)

    # Small sample sizes mean there's a fair bit of noise here
    lower_bound = -0.215

    if model_name == 'DeepLearningClassifier':
        lower_bound = -0.235
    if model_name == 'LGBMClassifier':
        lower_bound = -0.221

    assert lower_bound < test_score < -0.17



def categorical_ensembling_classification(model_name=None):
    np.random.seed(0)

    df_titanic_train, df_titanic_test = utils.get_titanic_binary_classification_dataset()

    column_descriptions = {
        'survived': 'output'
        , 'embarked': 'categorical'
        , 'pclass': 'categorical'
    }

    ml_predictor = Predictor(type_of_estimator='classifier', column_descriptions=column_descriptions)

    ml_predictor.train_categorical_ensemble(df_titanic_train, model_names=model_name, categorical_column='embarked')

    test_score = ml_predictor.score(df_titanic_test, df_titanic_test.survived)

    print('test_score')
    print(test_score)

    lower_bound = -0.215

    if model_name == 'DeepLearningClassifier':
        lower_bound = -0.237
    if model_name == 'XGBClassifier':
        lower_bound = -0.235
    if model_name == 'LGBMClassifier':
        lower_bound = -0.22
    if model_name == 'GradientBoostingClassifier':
        lower_bound = -0.23
    if model_name == 'CatBoostClassifier':
        lower_bound = -0.25


    assert lower_bound < test_score < -0.17


def getting_single_predictions_classification(model_name=None):
    np.random.seed(0)

    df_titanic_train, df_titanic_test = utils.get_titanic_binary_classification_dataset()

    column_descriptions = {
        'survived': 'output'
        , 'embarked': 'categorical'
        , 'pclass': 'categorical'
    }

    ml_predictor = Predictor(type_of_estimator='classifier', column_descriptions=column_descriptions)

    ml_predictor.train(df_titanic_train, model_names=model_name)

    file_name = ml_predictor.save(str(random.random()))

    saved_ml_pipeline = load_ml_model(file_name)
    # if model_name == 'DeepLearningClassifier':
    #     from auto_ml.utils_models import load_keras_model

    #     saved_ml_pipeline = load_keras_model(file_name)
    # else:
    #     with open(file_name, 'rb') as read_file:
    #         saved_ml_pipeline = dill.load(read_file)

    os.remove(file_name)
    try:
        keras_file_name = file_name[:-5] + '_keras_deep_learning_model.h5'
        os.remove(keras_file_name)
    except:
        pass


    df_titanic_test_dictionaries = df_titanic_test.to_dict('records')

    # 1. make sure the accuracy is the same

    predictions = []
    for row in df_titanic_test_dictionaries:
        predictions.append(saved_ml_pipeline.predict_proba(row)[1])

    print('predictions')
    print(predictions)

    first_score = utils.calculate_brier_score_loss(df_titanic_test.survived, predictions)
    print('first_score')
    print(first_score)
    # Make sure our score is good, but not unreasonably good

    lower_bound = -0.215
    if model_name == 'DeepLearningClassifier':
        lower_bound = -0.245
    if model_name == 'CatBoostClassifier':
        lower_bound = -0.22

    assert lower_bound < first_score < -0.17

    # 2. make sure the speed is reasonable (do it a few extra times)
    data_length = len(df_titanic_test_dictionaries)
    start_time = datetime.datetime.now()
    for idx in range(1000):
        row_num = idx % data_length
        saved_ml_pipeline.predict(df_titanic_test_dictionaries[row_num])
    end_time = datetime.datetime.now()
    duration = end_time - start_time

    print('duration.total_seconds()')
    print(duration.total_seconds())

    # It's very difficult to set a benchmark for speed that will work across all machines.
    # On my 2013 bottom of the line 15" MacBook Pro, this runs in about 0.8 seconds for 1000 predictions
    # That's about 1 millisecond per prediction
    # Assuming we might be running on a test box that's pretty weak, multiply by 3
    # Also make sure we're not running unreasonably quickly
    assert 0.2 < duration.total_seconds() < 15


    # 3. make sure we're not modifying the dictionaries (the score is the same after running a few experiments as it is the first time)

    predictions = []
    for row in df_titanic_test_dictionaries:
        predictions.append(saved_ml_pipeline.predict_proba(row)[1])

    print('predictions')
    print(predictions)
    print('df_titanic_test_dictionaries')
    print(df_titanic_test_dictionaries)
    second_score = utils.calculate_brier_score_loss(df_titanic_test.survived, predictions)
    print('second_score')
    print(second_score)
    # Make sure our score is good, but not unreasonably good

    assert lower_bound < second_score < -0.17



def getting_single_predictions_multilabel_classification(model_name=None):
    # auto_ml does not support multilabel classification for deep learning at the moment
    if model_name == 'DeepLearningClassifier' or model_name == 'CatBoostClassifier':
        return

    np.random.seed(0)

    df_twitter_train, df_twitter_test = utils.get_twitter_sentiment_multilabel_classification_dataset()

    column_descriptions = {
        'airline_sentiment': 'output'
        , 'airline': 'categorical'
        , 'text': 'ignore'
        , 'tweet_location': 'categorical'
        , 'user_timezone': 'categorical'
        , 'tweet_created': 'date'
    }

    ml_predictor = Predictor(type_of_estimator='classifier', column_descriptions=column_descriptions)
    ml_predictor.train(df_twitter_train, model_names=model_name)

    file_name = ml_predictor.save(str(random.random()))

    # if model_name == 'DeepLearningClassifier':
    #     from auto_ml.utils_models import load_keras_model

    #     saved_ml_pipeline = load_keras_model(file_name)
    # else:
    #     with open(file_name, 'rb') as read_file:
    #         saved_ml_pipeline = dill.load(read_file)
    saved_ml_pipeline = load_ml_model(file_name)

    os.remove(file_name)
    try:
        keras_file_name = file_name[:-5] + '_keras_deep_learning_model.h5'
        os.remove(keras_file_name)
    except:
        pass


    df_twitter_test_dictionaries = df_twitter_test.to_dict('records')

    # 1. make sure the accuracy is the same

    predictions = []
    for row in df_twitter_test_dictionaries:
        predictions.append(saved_ml_pipeline.predict(row))

    print('predictions')
    print(predictions)

    first_score = accuracy_score(df_twitter_test.airline_sentiment, predictions)
    print('first_score')
    print(first_score)
    # Make sure our score is good, but not unreasonably good
    lower_bound = 0.67
    if model_name == 'LGBMClassifier':
        lower_bound = 0.655
    assert lower_bound < first_score < 0.79

    # 2. make sure the speed is reasonable (do it a few extra times)
    data_length = len(df_twitter_test_dictionaries)
    start_time = datetime.datetime.now()
    for idx in range(1000):
        row_num = idx % data_length
        saved_ml_pipeline.predict(df_twitter_test_dictionaries[row_num])
    end_time = datetime.datetime.now()
    duration = end_time - start_time

    print('duration.total_seconds()')
    print(duration.total_seconds())

    # It's very difficult to set a benchmark for speed that will work across all machines.
    # On my 2013 bottom of the line 15" MacBook Pro, this runs in about 0.8 seconds for 1000 predictions
    # That's about 1 millisecond per prediction
    # Assuming we might be running on a test box that's pretty weak, multiply by 3
    # Also make sure we're not running unreasonably quickly
    # time_upper_bound = 10
    # if model_name == 'XGBClassifier':
    #     time_upper_bound = 4
    assert 0.2 < duration.total_seconds() < 15


    # 3. make sure we're not modifying the dictionaries (the score is the same after running a few experiments as it is the first time)

    predictions = []
    for row in df_twitter_test_dictionaries:
        predictions.append(saved_ml_pipeline.predict(row))

    print('predictions')
    print(predictions)
    print('df_twitter_test_dictionaries')
    print(df_twitter_test_dictionaries)
    second_score = accuracy_score(df_twitter_test.airline_sentiment, predictions)
    print('second_score')
    print(second_score)
    # Make sure our score is good, but not unreasonably good
    assert lower_bound < second_score < 0.79


def feature_learning_getting_single_predictions_classification(model_name=None):
    np.random.seed(0)

    df_titanic_train, df_titanic_test = utils.get_titanic_binary_classification_dataset()

    column_descriptions = {
        'survived': 'output'
        , 'embarked': 'categorical'
        , 'pclass': 'categorical'
    }

    ml_predictor = Predictor(type_of_estimator='classifier', column_descriptions=column_descriptions)

    # NOTE: this is bad practice to pass in our same training set as our fl_data set, but we don't have enough data to do it any other way
    df_titanic_train, fl_data = train_test_split(df_titanic_train, test_size=0.2)
    ml_predictor.train(df_titanic_train, model_names=model_name, feature_learning=True, fl_data=fl_data)

    file_name = ml_predictor.save(str(random.random()))


    # from auto_ml.utils_models import load_keras_model

    saved_ml_pipeline = load_ml_model(file_name)

    os.remove(file_name)
    try:
        keras_file_name = file_name[:-5] + '_keras_deep_learning_model.h5'
        os.remove(keras_file_name)
    except:
        pass


    df_titanic_test_dictionaries = df_titanic_test.to_dict('records')

    # 1. make sure the accuracy is the same

    predictions = []
    for row in df_titanic_test_dictionaries:
        predictions.append(saved_ml_pipeline.predict_proba(row)[1])

    print('predictions')
    print(predictions)

    first_score = utils.calculate_brier_score_loss(df_titanic_test.survived, predictions)
    print('first_score')
    print(first_score)
    # Make sure our score is good, but not unreasonably good

    lower_bound = -0.215
    if model_name == 'DeepLearningClassifier':
        lower_bound = -0.245
    if model_name == 'GradientBoostingClassifier' or model_name is None:
        lower_bound = -0.23
    if model_name == 'LGBMClassifier':
        lower_bound = -0.227
    if model_name == 'XGBClassifier':
        lower_bound = -0.245
    if model_name == 'CatBoostClassifier':
        lower_bound = -0.235


    assert lower_bound < first_score < -0.17

    # 2. make sure the speed is reasonable (do it a few extra times)
    data_length = len(df_titanic_test_dictionaries)
    start_time = datetime.datetime.now()
    for idx in range(1000):
        row_num = idx % data_length
        saved_ml_pipeline.predict(df_titanic_test_dictionaries[row_num])
    end_time = datetime.datetime.now()
    duration = end_time - start_time

    print('duration.total_seconds()')
    print(duration.total_seconds())

    # It's very difficult to set a benchmark for speed that will work across all machines.
    # On my 2013 bottom of the line 15" MacBook Pro, this runs in about 0.8 seconds for 1000 predictions
    # That's about 1 millisecond per prediction
    # Assuming we might be running on a test box that's pretty weak, multiply by 3
    # Also make sure we're not running unreasonably quickly
    assert 0.2 < duration.total_seconds() < 15


    # 3. make sure we're not modifying the dictionaries (the score is the same after running a few experiments as it is the first time)

    predictions = []
    for row in df_titanic_test_dictionaries:
        predictions.append(saved_ml_pipeline.predict_proba(row)[1])

    print('predictions')
    print(predictions)
    print('df_titanic_test_dictionaries')
    print(df_titanic_test_dictionaries)
    second_score = utils.calculate_brier_score_loss(df_titanic_test.survived, predictions)
    print('second_score')
    print(second_score)
    # Make sure our score is good, but not unreasonably good

    assert lower_bound < second_score < -0.17


def feature_learning_categorical_ensembling_getting_single_predictions_classification(model_name=None):
    np.random.seed(0)

    df_titanic_train, df_titanic_test = utils.get_titanic_binary_classification_dataset()

    column_descriptions = {
        'survived': 'output'
        , 'embarked': 'categorical'
        , 'pclass': 'categorical'
    }

    ml_predictor = Predictor(type_of_estimator='classifier', column_descriptions=column_descriptions)

    # NOTE: this is bad practice to pass in our same training set as our fl_data set, but we don't have enough data to do it any other way
    df_titanic_train, fl_data = train_test_split(df_titanic_train, test_size=0.2)
    ml_predictor.train_categorical_ensemble(df_titanic_train, model_names=model_name, feature_learning=False, fl_data=fl_data, categorical_column='embarked')

    file_name = ml_predictor.save(str(random.random()))

    # with open(file_name, 'rb') as read_file:
    #     saved_ml_pipeline = dill.load(read_file)
    from auto_ml.utils_models import load_ml_model

    saved_ml_pipeline = load_ml_model(file_name)

    os.remove(file_name)
    try:
        keras_file_name = file_name[:-5] + '_keras_deep_learning_model.h5'
        os.remove(keras_file_name)
    except:
        pass


    df_titanic_test_dictionaries = df_titanic_test.to_dict('records')

    # 1. make sure the accuracy is the same

    predictions = []
    for row in df_titanic_test_dictionaries:
        predictions.append(saved_ml_pipeline.predict_proba(row)[1])

    print('predictions')
    print(predictions)

    first_score = utils.calculate_brier_score_loss(df_titanic_test.survived, predictions)
    print('first_score')
    print(first_score)
    # Make sure our score is good, but not unreasonably good

    lower_bound = -0.215
    if model_name == 'DeepLearningClassifier':
        lower_bound = -0.24
    if model_name == 'GradientBoostingClassifier' or model_name is None:
        lower_bound = -0.25
    if model_name == 'LGBMClassifier':
        lower_bound = -0.23
    if model_name == 'XGBClassifier':
        lower_bound = -0.25
    if model_name == 'CatBoostClassifier':
        lower_bound = -0.265

    assert lower_bound < first_score < -0.17

    # 2. make sure the speed is reasonable (do it a few extra times)
    data_length = len(df_titanic_test_dictionaries)
    start_time = datetime.datetime.now()
    for idx in range(1000):
        row_num = idx % data_length
        saved_ml_pipeline.predict(df_titanic_test_dictionaries[row_num])
    end_time = datetime.datetime.now()
    duration = end_time - start_time

    print('duration.total_seconds()')
    print(duration.total_seconds())

    # It's very difficult to set a benchmark for speed that will work across all machines.
    # On my 2013 bottom of the line 15" MacBook Pro, this runs in about 0.8 seconds for 1000 predictions
    # That's about 1 millisecond per prediction
    # Assuming we might be running on a test box that's pretty weak, multiply by 3
    # Also make sure we're not running unreasonably quickly
    assert 0.2 < duration.total_seconds() < 15


    # 3. make sure we're not modifying the dictionaries (the score is the same after running a few experiments as it is the first time)

    predictions = []
    for row in df_titanic_test_dictionaries:
        predictions.append(saved_ml_pipeline.predict_proba(row)[1])

    print('predictions')
    print(predictions)
    print('df_titanic_test_dictionaries')
    print(df_titanic_test_dictionaries)
    second_score = utils.calculate_brier_score_loss(df_titanic_test.survived, predictions)
    print('second_score')
    print(second_score)
    # Make sure our score is good, but not unreasonably good

    assert lower_bound < second_score < -0.17

