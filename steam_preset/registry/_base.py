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

    def _load(self, module_name: str) -> Preset | None:
        file_path = self.presets_dir / f'{module_name}.py'
        spec = importlib.util.spec_from_file_location(f'presets.{module_name}', file_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            logger.info(f'Imported {module}')
            preset = Preset.model_validate(vars(module))
            return preset
        return None

    def _search_for(self, key: str, *, delimiter: str = '__') -> Preset | None:
        for _, module_name, _ in pkgutil.iter_modules([str(self.presets_dir)]):
            if key in module_name.split(delimiter):
                if (preset := self._load(module_name)):
                    return preset
        return None

    def get(self, preset_key: str | None) -> Preset:
        # parse key
        key = preset_key or os.environ.get('SteamAppId')
        logger.debug(f'{key=} (source: {"--key flag" if preset_key else "env SteamAppId"})')

        # try with primary key first
        if key:
            if (preset := self._search_for(key)):
                return preset

        # fallback to 'default' preset if primary key didn't match anything or is None
        if key != 'default':
            logger.warning(f'No preset found for {key=}, falling back to `default`')
            if (preset := self._search_for('default')):
                return preset

        # if no preset is found, steam-preset launcher will crash and the game won't run
        raise ImportError(f'Failed to import any preset for the key `{key}`')
