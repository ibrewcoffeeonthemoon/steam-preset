import importlib
import importlib.util
import logging
import pkgutil
from pathlib import Path

from steam_preset.types import Preset

Registry = dict[str, Preset]

logger = logging.getLogger('steam-preset')


def discover_presets() -> Registry:
    #
    registry: Registry = {}

    # iterate through all python modules in the presets package
    presets_dir = Path.home() / '.config/workspace/steam-preset/presets'
    if not presets_dir.is_dir():
        return registry

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
                    registry[str(module.key)] = module
                    logger.info(f'Discovered {module}')
        except ImportError as e:
            logger.error(f'Failed to import preset {file_path.name}: {e}')
        except Exception as e:
            logger.error(f'Unexpected error loading preset {file_path.name}: {e}')
    #
    return registry
