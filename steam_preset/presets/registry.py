import importlib
import importlib.util
import os
import pkgutil
from pathlib import Path

from steam_preset.log import logger
from steam_preset.types import Preset


class Registry:
    def __init__(self, presets_dir: Path) -> None:
        #
        self._data: dict[str, Preset] = {}

        # iterate through all python modules in the presets package
        if not presets_dir.is_dir():
            return

        # convert Path to string for pkgutil
        for _, module_name, _ in pkgutil.iter_modules([str(presets_dir)]):
            file_path = presets_dir / f'{module_name}.py'

            # dynamically load the module from file path
            try:
                spec = importlib.util.spec_from_file_location(
                    f'presets.{module_name}', file_path
                )
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    logger.debug(f'Imported {module}')

                    # register module by its key attribute if defined
                    if isinstance(module, Preset):
                        self._data[str(module.key)] = module
                        logger.info(f'Discovered {module}')
            except ImportError as e:
                logger.error(f'Failed to import preset {file_path.name}: {e}')
            except Exception as e:
                logger.error(f'Unexpected error loading preset {file_path.name}: {e}')

    def get(self, preset_key: str | None) -> Preset | None:
        # parse key
        key = preset_key or os.environ.get('SteamAppId', 'default')
        logger.debug(f'{key=} (source: {"--key flag" if preset_key else "env SteamAppId"})')

        # load preset
        preset = self._data.get(key)
        if preset is None:
            logger.warning('No preset is loaded, steam-preset has no effect')
        else:
            logger.debug(f'Preset loaded from registry: {preset=}')

        #
        return preset
