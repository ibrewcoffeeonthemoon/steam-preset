import importlib
import importlib.util
import os
import pkgutil
from pathlib import Path

from steam_preset.log import logger
from steam_preset.types import Preset


class Registry:
    def __init__(self, presets_dir: Path) -> None:
        self.presets_dir = presets_dir

    def _load_preset(self, key: str) -> Preset | None:
        # loop through the presets dir for python files
        for _, module_name, _ in pkgutil.iter_modules([str(self.presets_dir)]):
            file_path = self.presets_dir / f'{module_name}.py'

            # import the python file if it match the key
            try:
                # using double underscore as delimiter and look for key match in the filename directly
                if key in module_name.split('__'):
                    spec = importlib.util.spec_from_file_location(
                        f'presets.{module_name}', file_path
                    )
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        logger.debug(f'Imported {module}')
                        return module

            except ImportError as e:
                logger.error(f'Failed to import preset {file_path.name}: {e}')
            except Exception as e:
                logger.error(f'Unexpected error loading preset {file_path.name}: {e}')

        return None

    def get(self, preset_key: str | None) -> Preset | None:
        # parse key
        key = preset_key or os.environ.get('SteamAppId', 'default')
        logger.debug(f'{key=} (source: {"--key flag" if preset_key else "env SteamAppId"})')

        # load preset
        preset = self._load_preset(key)
        if preset is None:
            logger.warning('No preset is loaded, using the default preset')
        else:
            logger.info(f'Preset loaded from registry: {preset=}')

        #
        return preset
