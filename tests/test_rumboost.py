import pytest
import rumboost as rumb
from rumboost.rumboost import rum_train
from rumboost.datasets import prepare_dataset
import numpy as np
import pandas as pd
from lightgbm import Dataset, Booster

try:
    import torch

    TORCH_INSTALLED = True
except ImportError:
    TORCH_INSTALLED = False


@pytest.fixture
def toy_train_set():
    return Dataset(
        pd.DataFrame(
            {
                "0": [1, 2, 3, 2],
                "1": [4, 5, 6, 1],
                "2": [7, 8, 9, 5],
                "3": [4, 5, 6, 1],
                "4": [3, 1, 7, 3],
                "5": [6, 1, 3, 9],
            }
        ),
        label=pd.Series([0, 1, 2, 1], dtype=int),
        free_raw_data=False,
    )


@pytest.fixture
def toy_valid_set():
    return Dataset(
        pd.DataFrame(
            {
                "0": [2, 3, 4],
                "1": [5, 4, 3],
                "2": [8, 7, 6],
                "3": [1, 6, 8],
                "4": [7, 5, 4],
                "5": [3, 2, 1],
            }
        ),
        label=pd.Series([2, 1, 0], dtype=int),
        free_raw_data=False,
    )


@pytest.fixture
def toy_attributes():
    return {
        "best_iteration": 100,
        "best_score": 0.5,
        "best_score_train": 0.3,
        "alphas": np.array([[0.5, 0.5], [1, 0], [0, 1]]),
        "mu": np.array([1, 1]),
        "optimise_mu": [True, False],
        "optimise_alphas": np.array([[True, True], [False, False], [False, False]]),
        "optim_interval": 20,
        "nests": {0: [0, 1], 1: [2]},
        "nest_alt": np.array([0, 0, 1]),
        "num_classes": 3,
        "num_obs": [4, 3],
        "functional_effects": False,
        "shared_ensembles": {3: [0, 1, 2]},
        "shared_start_idx": 3,
        "labels": np.array([0, 1, 2, 1]),
        "labels_j": [
            np.array([1, 0, 0]),
            np.array([0, 1, 0]),
            np.array([0, 0, 1]),
            np.array([0, 1, 0]),
        ],
        "valid_labels": np.array([2, 1, 0]),
        "device": None,
        "torch_compile": False,
        "general_params": {
            "n_jobs": -1,
            "num_classes": 3,  # important
            "verbosity": 0,  # specific RUMBoost parameter
            "verbosity_interval": 1,
            "min_data_in_bin": 1,
            "num_iterations": 10,
            "early_stopping_round": None,
            "subsampling": 1.0,
            "subsampling_freq": 0,
            "subsample_valid": 1.0,
            "batch_size": 0,
            "max_booster_to_update": 3,
            "save_model_interval": 0,
        },
        "rum_structure": [
            {
                "utility": [0],
                "variables": ["0", "1"],
                "boosting_params": {
                    "monotone_constraints_method": "advanced",
                    "monotone_constraints": [1, -1],
                    "interaction_constraints": [[0], [1]],
                    "learning_rate": 0.1,
                    "max_depth": 1,
                    "min_data_in_leaf": 1,
                    "min_gain_to_split": 0,
                },
                "shared": False,
            },
            {
                "utility": [1],
                "variables": ["1", "2"],
                "boosting_params": {
                    "monotone_constraints_method": "advanced",
                    "monotone_constraints": [1, -1],
                    "interaction_constraints": [[0], [1]],
                    "learning_rate": 0.1,
                    "max_depth": 1,
                    "min_data_in_leaf": 1,
                    "min_gain_to_split": 0,
                },
                "shared": False,
            },
            {
                "utility": [2],
                "variables": ["0", "2"],
                "boosting_params": {
                    "monotone_constraints_method": "advanced",
                    "monotone_constraints": [1, -1],
                    "interaction_constraints": [[0], [1]],
                    "learning_rate": 0.1,
                    "max_depth": 1,
                    "min_data_in_leaf": 1,
                    "min_gain_to_split": 0,
                },
                "shared": False,
            },
            {
                "utility": [0, 1, 2],
                "variables": ["3", "4", "5"],
                "boosting_params": {
                    "monotone_constraints_method": "advanced",
                    "monotone_constraints": [1],
                    "interaction_constraints": [[0]],
                    "learning_rate": 0.1,
                    "max_depth": 1,
                    "min_data_in_leaf": 1,
                    "min_gain_to_split": 0,
                },
                "shared": True,
            },
        ],
    }


@pytest.fixture
def create_model_spec(model_type="MNL", toy_attributes=toy_attributes):
    """
    Create a model specification for the RUMBoost object
    Model_type can be "MNL", "Nested Logit" or "Cross Nested Logit"
    """
    if "num_classes" not in toy_attributes["general_params"]:
        toy_attributes["general_params"]["num_classes"] = 3
    model_specification = {
        "general_params": toy_attributes["general_params"],
        "rum_structure": toy_attributes["rum_structure"],
    }
    if model_type == "Nested Logit":
        model_specification["nested_logit"] = {
            "mu": toy_attributes["mu"],
            "nests": toy_attributes["nests"],
            "optimise_mu": toy_attributes["optimise_mu"],
            "optim_interval": toy_attributes["optim_interval"],
        }
        return model_specification
    elif model_type == "Cross Nested Logit":
        model_specification["cross_nested_logit"] = {
            "mu": toy_attributes["mu"],
            "alphas": toy_attributes["alphas"],
            "optimise_mu": toy_attributes["optimise_mu"],
            "optimise_alphas": toy_attributes["optimise_alphas"],
            "optim_interval": toy_attributes["optim_interval"],
        }
        return model_specification
    return model_specification


@pytest.fixture
def create_torch_tensors(use_torch=False, toy_attributes=toy_attributes):
    """
    Create torch tensors for the RUMBoost object
    """
    if not TORCH_INSTALLED or not use_torch:
        return None
    torch_tensors = {
        "device": toy_attributes["device"],
        "torch_compile": toy_attributes["torch_compile"],
    }
    return torch_tensors


def test_rumboost_object(toy_train_set, toy_valid_set, toy_attributes):

    # create a rumboost object
    model = rumb.RUMBoost(model_file=None, **toy_attributes)
    num_classes = toy_attributes["general_params"].pop("num_classes")
    toy_train_set._update_params(toy_attributes["general_params"])._set_predictor(
        None
    ).set_feature_name(None).set_categorical_feature([])
    reduced_valid_sets, _, _, _ = model._preprocess_valids(
        toy_train_set, toy_attributes["general_params"], [toy_valid_set]
    )  # prepare validation sets
    model._preprocess_data(toy_train_set, reduced_valid_sets)
    model.boosters = [
        Booster(
            train_set=model.train_set[0],
            params=toy_attributes["rum_structure"][0]["boosting_params"],
        ),
        Booster(
            train_set=model.train_set[1],
            params=toy_attributes["rum_structure"][1]["boosting_params"],
        ),
        Booster(
            train_set=model.train_set[2],
            params=toy_attributes["rum_structure"][2]["boosting_params"],
        ),
        Booster(
            train_set=model.train_set[3],
            params=toy_attributes["rum_structure"][3]["boosting_params"],
        ),
    ]

    # check if the object is created with correct attributes
    assert model is not None
    assert isinstance(model.boosters, list)
    assert model.num_classes == 3
    assert model.shared_start_idx == 3
    assert model.shared_ensembles == {3: [0, 1, 2]}
    assert model.num_obs == [4, 3]
    assert model.nests == {0: [0, 1], 1: [2]}
    assert np.array_equal(model.nest_alt, np.array([0, 0, 1]))
    assert np.array_equal(model.mu, np.array([1, 1]))
    assert np.array_equal(model.alphas, np.array([[0.5, 0.5], [1, 0], [0, 1]]))
    assert np.array_equal(model.labels, np.array([0, 1, 2, 1]))
    assert np.array_equal(
        model.labels_j,
        [
            np.array([1, 0, 0]),
            np.array([0, 1, 0]),
            np.array([0, 0, 1]),
            np.array([0, 1, 0]),
        ],
    )
    assert np.array_equal(model.valid_labels, [np.array([2, 1, 0])])
    assert model.rum_structure == toy_attributes["rum_structure"]
    assert model.device == None
    assert model.torch_compile == False


def test_simple_train(
    create_model_spec, create_torch_tensors, toy_train_set, toy_valid_set
):
    print(toy_train_set.data)
    model_specification = create_model_spec
    torch_tensors = create_torch_tensors
    model_trained = rum_train(
        toy_train_set,
        model_specification,
        valid_sets=[toy_valid_set],
        torch_tensors=torch_tensors,
    )
    assert model_trained.best_iteration == 10
    assert np.allclose(model_trained.best_score, 0.9971296557418077, atol=1e-5)
    assert np.allclose(model_trained.best_score_train, 0.6433719740056012, atol=1e-5)
    if torch_tensors:
        assert np.allclose(
            model_trained.predict(toy_valid_set),
            np.array(
                [
                    [0.32716662, 0.53836168, 0.1344717],
                    [0.16751941, 0.27565781, 0.55682278],
                    [0.16751941, 0.27565781, 0.55682278],
                ]
            ),
            rtol=1e-5,
        )
    else:
        assert np.allclose(
            model_trained.predict(toy_valid_set),
            np.array(
                [
                    [0.32716662, 0.53836168, 0.1344717],
                    [0.16751941, 0.27565781, 0.55682278],
                    [0.16751941, 0.27565781, 0.55682278],
                ]
            ),
            rtol=1e-5,
        )


#
# def test_f_obj():
#    # create a RUMBoost object
#    rumboost = rumb.RUMBoost()
#
#    # assign some values to the object
#    rumboost._preds = np.array([[0.5], [0.5], [0.5]])
#    rumboost._current_j = 0
#    rumboost.num_classes = 2
#
#    # create a dummy dataset
#    train_data = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
#    train_labels = np.array([0, 1, 0])
#    train_set = Dataset(train_data, label=train_labels)
#
#    # call the f_obj method
#    grad, hess = rumboost.f_obj(None, train_set)
#
#    # perform assertions
#    assert np.array_equal(grad, np.array([0.5, -0.5, 0.5]))
#    assert np.array_equal(hess, np.array([0.5, 0.5, 0.5]))
#
#    # assign some values to the object
#    rumboost._preds = np.array([[0.1, 0.2, 0.3], [0.5, 0.2, 0.3], [0.7, 0.1, 0.2]])
#    rumboost._current_j = 2
#    rumboost.num_classes = 3
#
#    # call the f_obj method
#    grad, hess = rumboost.f_obj(None, train_set)
#
#    # perform assertions
#    assert np.array_equal(grad, np.array([0.3, -0.7, 0.2]))
#    assert np.allclose(
#        hess, np.array([0.315, 0.315, 0.24])
#    )  # allclose is used because of floating point precision
#
#    rumboost._current_j = 1
#
#    # call the f_obj method
#    grad, hess = rumboost.f_obj(None, train_set)
#
#    # perform assertions
#    assert np.array_equal(grad, np.array([0.2, -0.8, 0.1]))
#    assert np.allclose(
#        hess, np.array([0.24, 0.24, 0.135])
#    )  # allclose is used because of floating point precision
#
#
# def test_f_obj_nest():
#    # create a RUMBoost object
#    rumboost = rumb.RUMBoost()
#
#    # assign some values to the object
#    rumboost._current_j = 2
#    rumboost.preds_i_m = np.array([[0.5, 1, 0.5], [0.3, 1, 0.7], [0.2, 1, 0.8]])
#    rumboost.preds_m = np.array([[0.4, 0.6], [0.3, 0.7], [0.5, 0.5]])
#    rumboost.nests = {0: 0, 1: 1, 2: 0}
#    rumboost.num_classes = 3
#    rumboost.mu = np.array([1.5, 1])
#    rumboost.labels = np.array([0, 1, 2])
#    rumboost.labels_nest = np.array([0, 1, 0])
#
#    # create a dummy dataset
#    train_data = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
#    train_labels = np.array([0, 0, 1])
#    train_set = Dataset(train_data, label=train_labels)
#
#    # call the f_obj_nest method
#    grad, hess = rumboost.f_obj_nest(None, train_set)
#
#    # perform assertions
#    assert np.allclose(
#        grad, np.array([0.45, 0.21, -0.7])
#    )  # allclose is used because of floating point precision
#    assert np.allclose(
#        hess, np.array([0.59625, 0.2961, 0.6])
#    )  # allclose is used because of floating point precision
#
#    # if no nests, should be the same than f_obj
#    rumboost.nests = {0: 0, 1: 1, 2: 2}
#    rumboost.preds_i_m = np.array([[1, 1, 1], [1, 1, 1], [1, 1, 1]])
#    rumboost.preds_m = np.array([[0.2, 0.6, 0.2], [0.3, 0.3, 0.4], [0.5, 0.4, 0.1]])
#    rumboost.mu = np.array([1, 1, 1])
#    rumboost.labels = np.array([0, 1, 2])
#    rumboost.labels_nest = np.array([0, 1, 2])
#
#    grad_n, hess_n = rumboost.f_obj_nest(None, train_set)
#
#    rumboost._preds = np.array([[0.2, 0.6, 0.2], [0.3, 0.3, 0.4], [0.5, 0.4, 0.1]])
#
#    grad, hess = rumboost.f_obj(None, train_set)
#
#    assert np.allclose(
#        grad, grad_n
#    )  # allclose is used because of floating point precision
#    assert np.allclose(
#        hess, hess_n
#    )  # allclose is used because of floating point precision
#
#
# def test_f_obj_cross_nested():
#    # create a RUMBoost object
#    rumboost = rumb.RUMBoost()
#
#    # assign some values to the object
#    rumboost._current_j = 2
#    rumboost.preds_i_m = np.array(
#        [
#            [[1, 0], [0.3, 0.2], [0, 0.8]],
#            [[0.4, 0], [0.6, 0.5], [0, 0.5]],
#            [[0.2, 0], [0.8, 0.5], [0, 0.5]],
#        ]
#    )
#    rumboost.preds_m = np.array(
#        [
#            [[0.4, 0.6], [0.4, 0.6], [0.4, 0.6]],
#            [[0.3, 0.7], [0.3, 0.7], [0.3, 0.7]],
#            [[0.2, 0.8], [0.2, 0.8], [0.2, 0.8]],
#        ]
#    )
#    rumboost._preds = np.sum(rumboost.preds_i_m * rumboost.preds_m, axis=2)
#    rumboost.mu = np.array([1.5, 1.25])
#    rumboost.labels = np.array([0, 1, 2])
#    rumboost.alphas = np.array([[1, 0], [0.5, 0.5], [0, 1]])
#    rumboost.num_classes = 3
#
#    # create a dummy dataset
#    train_data = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
#    train_labels = np.array([0, 0, 1])
#    train_set = Dataset(train_data, label=train_labels)
#
#    # call the f_obj_cross_nested method
#    grad, hess = rumboost.f_obj_cross_nested(None, train_set)
#
#    # perform assertions
#    assert np.allclose(
#        grad, np.array([0.48, 0.43254717, -0.725])
#    )  # allclose is used because of floating point precision
#    assert np.allclose(
#        hess, (3 / 2) * np.array([0.2736, 0.71143668, 0.368125])
#    )  # allclose is used because of floating point precision
#
#    # if excluding nests, should be the same than f_obj_nested
#    rumboost.alphas = np.array([[1, 0], [0, 1], [1, 0]])
#    rumboost.preds_i_m = np.array(
#        [
#            [[0.5, 0], [0, 1], [0.5, 0]],
#            [[0.3, 0], [0, 1], [0.7, 0]],
#            [[0.2, 0], [0, 1], [0.8, 0]],
#        ]
#    )
#    rumboost.preds_m = np.array(
#        [
#            [[0.4, 0.6], [0.4, 0.6], [0.4, 0.6]],
#            [[0.3, 0.7], [0.3, 0.7], [0.3, 0.7]],
#            [[0.5, 0.5], [0.5, 0.5], [0.5, 0.5]],
#        ]
#    )
#    rumboost.mu = np.array([1.5, 1])
#    rumboost.labels = np.array([0, 1, 2])
#    rumboost._preds = np.sum(rumboost.preds_i_m * rumboost.preds_m, axis=2)
#
#    grad, hess = rumboost.f_obj_cross_nested(None, train_set)
#
#    assert np.allclose(
#        grad, np.array([0.45, 0.21, -0.7])
#    )  # allclose is used because of floating point precision
#    assert np.allclose(
#        hess, np.array([0.59625, 0.2961, 0.6])
#    )  # allclose is used because of floating point precision
#
#    # if no nests, should be the same than f_obj
#    rumboost.alphas = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]])
#    rumboost.preds_i_m = np.array(
#        [
#            [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
#            [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
#            [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
#        ]
#    )
#    rumboost.preds_m = np.array(
#        [
#            [[0.2, 0.6, 0.2], [0.2, 0.6, 0.2], [0.2, 0.6, 0.2]],
#            [[0.3, 0.3, 0.4], [0.3, 0.3, 0.4], [0.3, 0.3, 0.4]],
#            [[0.5, 0.4, 0.1], [0.5, 0.4, 0.1], [0.5, 0.4, 0.1]],
#        ]
#    )
#    rumboost.mu = np.array([1, 1, 1])
#    rumboost.labels = np.array([0, 1, 2])
#    rumboost._preds = np.sum(rumboost.preds_i_m * rumboost.preds_m, axis=2)
#
#    grad_cnl, hess_cnl = rumboost.f_obj_cross_nested(None, train_set)
#
#    rumboost._preds = np.array([[0.2, 0.6, 0.2], [0.3, 0.3, 0.4], [0.5, 0.4, 0.1]])
#
#    grad, hess = rumboost.f_obj(None, train_set)
#
#    assert np.allclose(
#        grad, grad_cnl
#    )  # allclose is used because of floating point precision
#    assert np.allclose(
#        hess, hess_cnl
#    )  # allclose is used because of floating point precision
#
#
# def test_predict():
#    # create a RUMBoost object
#    rumboost = rumb.RUMBoost()
#
#    # set up the necessary attributes
#    rumboost.boosters = [
#        Booster(),
#        Booster(),
#        Booster(),
#        Booster(),
#    ]  # replace with actual booster objects
#    rumboost.num_classes = 4
#    rumboost.functional_effects = False
#
#    # set up the input data
#    data = np.array([[1, 2, 3, 10], [4, 5, 6, 9], [7, 8, 9, 1], [10, 11, 12, 0]])
#    labels = [0, 1, 2, 3]
#    train_set = Dataset(data, label=labels, free_raw_data=False)
#
#    # call the predict method
#    preds = rumboost.predict(train_set)
#    raw_preds = rumboost.predict(utilities=True)
#
#    # perform assertions
#    assert np.allclose(
#        preds,
#        np.array(
#            [
#                [0.25, 0.25, 0.25, 0.25],
#                [0.25, 0.25, 0.25, 0.25],
#                [0.25, 0.25, 0.25, 0.25],
#                [0.25, 0.25, 0.25, 0.25],
#            ]
#        ),
#    )  # replace with the expected shapr
#    assert np.allclose(
#        preds, np.array([[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]])
#    )  # replace with the expected shape
#
#    # test the nested probabilities case
#    nests = {0: 0, 1: 1, 2: 0, 3: 1}
#    mu = [1.5, 1.3]
#    preds, pred_i_m, pred_m = rumboost.predict(data, nests=nests, mu=mu)
#    assert preds.shape == (3, 3)  # replace with the expected shape
#    assert pred_i_m.shape == (3, 3)  # replace with the expected shape
#    assert pred_m.shape == (3, 2)  # replace with the expected shape
#
#    # test the cross-nested probabilities case
#    alphas = np.array([[1, 0], [0.5, 0.5], [0, 1]])
#    preds, pred_i_m, pred_m = rumboost.predict(data, alphas=alphas)
#    assert preds.shape == (3, 3)  # replace with the expected shape
#    assert pred_i_m.shape == (3, 3)  # replace with the expected shape
#    assert pred_m.shape == (3, 2)  # replace with the expected shape
#
#    # test the softmax case
#    utilities = False
#    preds = rumboost.predict(data, utilities=utilities)
#    assert preds.shape == (3, 3)  # replace with the expected shape
#
#    # test the raw utilities case
#    utilities = True
#    raw_preds = rumboost.predict(data, utilities=utilities)
#    assert raw_preds.shape == (3, 3)  # replace with the expected shape
#
#
# def test_construct_boosters():
#    # create a RUMBoost object
#    rumboost = rumb.RUMBoost()
#
#    # set up the necessary attributes
#    train_data_name = "Training"
#    is_valid_contain_train = False
#    name_valid_sets = ["Valid_0"]
#
#    # create mock parameters and datasets
#    params_J = [{"param1": 1}, {"param2": 2}]
#    train_set_J = [Dataset(), Dataset()]
#    reduced_valid_sets_J = [Dataset(), Dataset()]
#
#    # assign mock parameters and datasets to RUMBoost object
#    rumboost.params = params_J
#    rumboost.train_set = train_set_J
#    rumboost.valid_sets = reduced_valid_sets_J
#
#    # call the _construct_boosters method
#    rumboost._construct_boosters(
#        train_data_name=train_data_name,
#        is_valid_contain_train=is_valid_contain_train,
#        name_valid_sets=name_valid_sets,
#    )
#
#    # perform assertions
#    assert len(rumboost.boosters) == 2
#    assert rumboost.boosters[0].params == params_J[0]
#    assert rumboost.boosters[1].params == params_J[1]
#    assert rumboost.boosters[0].train_set == train_set_J[0]
#    assert rumboost.boosters[1].train_set == train_set_J[1]
#    assert rumboost.boosters[0].valid_sets[0] == reduced_valid_sets_J[0]
#    assert rumboost.boosters[1].valid_sets[0] == reduced_valid_sets_J[1]
#    assert rumboost.boosters[0].train_data_name == train_data_name
#    assert rumboost.boosters[1].train_data_name == train_data_name
#    assert rumboost.boosters[0].best_iteration == 0
#    assert rumboost.boosters[1].best_iteration == 0
#
#
# def test_preprocess_params():
#    # Create a RUMBoost object
#    rumboost = rumb.RUMBoost()
#
#    # Set up the parameters
#    params = {
#        "learning_rate": 0.1,
#        "verbosity": -1,
#        "objective": "binary",
#        "num_classes": 1,
#        "monotone_constraints": [1, -1],
#        "interaction_constraints": [(0, 1)],
#    }
#
#    # Set up the rum_structure
#    rumboost.rum_structure = [
#        {"monotone_constraints": [1, -1], "interaction_constraints": [(0, 1)]},
#        {"monotone_constraints": [1, -1], "interaction_constraints": [(0, 1)]},
#    ]
#
#    # Call the _preprocess_params method
#    params_J = rumboost._preprocess_params(params, return_params=True)
#
#    # Perform assertions
#    assert len(params_J) == 2
#    assert params_J[0]["learning_rate"] == 0.05
#    assert params_J[0]["monotone_constraints"] == [1, -1]
#    assert params_J[0]["interaction_constraints"] == [(0, 1)]
#    assert params_J[1]["learning_rate"] == 0.05
#    assert params_J[1]["monotone_constraints"] == [1, -1]
#    assert params_J[1]["interaction_constraints"] == [(0, 1)]
#
#
# @pytest.mark.parametrize(
#    "num_classes, rum_structure, shared_parameters",
#    [
#        (3, [{"columns": [0, 1]}, {"columns": [1, 2]}, {"columns": [0, 2]}], None),
#        (
#            3,
#            [{"columns": [0, 1]}, {"columns": [1, 2]}, {"columns": [0, 2]}],
#            {2: [0, 1]},
#        ),
#    ],
# )
# def test_preprocess_data(num_classes, rum_structure, shared_parameters):
#    # Create a RUMBoost object
#    rumboost = rumb.RUMBoost(
#        num_classes=num_classes,
#        rum_structure=rum_structure,
#        shared_parameters=shared_parameters,
#    )
#
#    rumboost.shared_start_idx = [*shared_parameters][0]
#    rumboost.params_J = [
#        {
#            "learning_rate": 0.1,
#            "verbosity": -1,
#            "objective": "binary",
#            "num_classes": 1,
#            "monotone_constraints": [1, -1],
#            "interaction_constraints": [(0, 1)],
#        }
#    ] * len(rum_structure)
#    # Create a dummy dataset
#    data = Dataset(
#        np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]]),
#        label=np.array([0, 1, 2]),
#        free_raw_data=False,
#    )
#
#    # Call the _preprocess_data method
#    train_set_J, reduced_valid_sets_J = rumboost._preprocess_data(
#        data, reduced_valid_set=[data]
#    )
#
#    # Perform assertions
#    assert len(train_set_J) == len(rum_structure)
#    assert len(reduced_valid_sets_J) == 1
#    assert len(reduced_valid_sets_J[0]) == len(rum_structure)
#    assert rumboost.labels.shape == (3,)
#    assert rumboost.labels_j.shape == (3, num_classes)
#    assert isinstance(train_set_J[0], Dataset)
#    assert isinstance(reduced_valid_sets_J[0][0], Dataset)
#
