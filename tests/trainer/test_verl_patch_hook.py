from rllm.patches.verl_patch_hook import _pop_regularization_kwargs


def test_pop_regularization_kwargs_extracts_chi_square_and_gr_fields() -> None:
    kwargs = {
        "lr": 1e-6,
        "use_chi_square_loss": True,
        "chi_square_loss_coef": 0.0008,
        "use_gr": True,
        "gr_gamma": 0.01,
        "gr_epsilon": 0.001,
        "gr_disturbance_clip": 10.0,
        "gr_perturbed_clip": 10.0,
    }

    extracted = _pop_regularization_kwargs(kwargs)

    assert extracted == {
        "use_chi_square_loss": True,
        "chi_square_loss_coef": 0.0008,
        "use_gr": True,
        "gr_gamma": 0.01,
        "gr_epsilon": 0.001,
        "gr_disturbance_clip": 10.0,
        "gr_perturbed_clip": 10.0,
    }
    assert kwargs == {"lr": 1e-6}


def test_pop_regularization_kwargs_leaves_standard_actor_config_untouched() -> None:
    kwargs = {"lr": 1e-6, "use_kl_loss": False}

    assert _pop_regularization_kwargs(kwargs) == {}
    assert kwargs == {"lr": 1e-6, "use_kl_loss": False}
