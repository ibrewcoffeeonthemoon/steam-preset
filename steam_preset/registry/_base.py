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
        # explicit --key flag: fail fast if invalid, never fall back to default
        if preset_key:
            logger.debug(f'{preset_key=} (source: --key flag)')
            if preset := self._search_for(preset_key):
                return preset
            raise ImportError(f'Invalid {preset_key=}: no matching preset found')

        # automatic SteamAppId lookup: fall back to 'default' on miss (e.g. non-steam games)
        if steam_app_id := os.environ.get('SteamAppId'):
            logger.debug(f'{steam_app_id=} (source: env SteamAppId)')
            if preset := self._search_for(steam_app_id):
                return preset
            logger.warning(f'No preset found for {steam_app_id=}, falling back to `default`')

        # fallback to 'default' preset
        if preset := self._search_for('default'):
            return preset

        raise ImportError('Failed to import any preset (and no `default` preset found)')
