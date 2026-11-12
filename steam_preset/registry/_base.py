import importlib
import importlib.util
import os
import pkgutil
from pathlib import Path

from steam_preset.log import logger

from .preset import Preset

__all__ = ['Registry']


class Registry:
    def __init__(self, presets_dir: Path) -> None:
        self.presets_dir = presets_dir

    def get(self, preset_key: str | None) -> Preset:
        # parse key
        if not (key := preset_key or os.environ.get('SteamAppId')):
            raise ValueError('No key could be use to locate a preset, provide it via the --key flag')
        logger.debug(f'{key=} (source: {"--key flag" if preset_key else "env SteamAppId"})')

        # loop through the presets dir for python files
        for _, module_name, _ in pkgutil.iter_modules([str(self.presets_dir)]):
            # import the python file if it match the key
            file_path = self.presets_dir / f'{module_name}.py'
            # using double underscore as delimiter and look for key match in the filename directly
            if key in module_name.split('__'):
                spec = importlib.util.spec_from_file_location(f'presets.{module_name}', file_path)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    logger.debug(f'Imported {module}')
                    preset = Preset.model_validate(vars(module))
                    return preset

        # if no preset is found, steam-preset launcher will crash and the game won't run
        raise ImportError(f'Failed to import any preset for the key `{key}`')
