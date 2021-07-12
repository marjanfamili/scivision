import importlib
import os
from urllib.parse import urljoin

import fsspec
import yaml

from .wrapper import PretrainedModel

SCIVISION_YAML_CONFIG = ".scivision-config.yaml"


def _parse_config(path: os.PathLike) -> dict:
    """Parse the `scivision` config file."""
    file = fsspec.open(path)
    with file as config_file:
        stream = config_file.read()
        config = yaml.safe_load(stream)

    # make sure we at least have an input to the function
    assert "X" in config["prediction_fn"]["args"].keys()

    return config


def _package_exists(config: dict) -> bool:
    """Check to see whether a package exists."""
    try:
        importlib.import_module(config["import"])
    except ModuleNotFoundError:
        return False

    return True


def load_pretrained_model(
    path: os.PathLike, allow_install: bool = False, *args, **kwargs
) -> PretrainedModel:
    """Load a pre-trained model.

    Parameters
    ----------
    path : PathLike
        The filename, path or URL of a pretrained model description.
    allow_install : bool
        Allow installation of remote package via pip.

    Returns
    -------
    pretrained_model : scivision.PretrainedModel
        The instantiated pre-trained model.
    """

    # we first need to parse the yaml file if it exists
    # NOTE(arl): this assumes we're grabbing a model from github, but it should
    # also work with a local config file with a reference to a github repo
    config_url = urljoin(
        f"https://raw.githubusercontent.com/{path}/main/",
        SCIVISION_YAML_CONFIG,
    )

    config = _parse_config(config_url)

    # now check to see whether the package exists
    if not _package_exists(config):
        # NOTE(arl), here is where we could grab the repo and install it
        install_str = config["url"]
        if install_str.endswith(".git"):
            install_str = install_str[:-4]

        raise Exception(
            "Package does not exist. Try installing it with: \n"
            f"`!pip install -e git+{install_str}@main#egg={config['import']}`"
        )

    return PretrainedModel(config)
