import os
import subprocess as sh
from typing import Self

from typer import Exit

from steam_preset.log import logger
from steam_preset.presets import default as default_preset
from steam_preset.presets.discovery import discover_presets
from steam_preset.types import (
    PresetConfigurable,
    PresetInitializable,
    PresetWithArg,
    PresetWithEnv,
    PresetWithKeyMapper,
    PresetWithWrapper,
)

from . import artwork, inputs


class Game:
    def __init__(
        self,
        steam_cmd: list[str] | None,
        preset_key: str | None,
        artwork_id: str | None,
    ) -> None:
        self._artwork_id = artwork_id

        # extract %command%
        if steam_cmd is None:
            logger.error('No %command% detected. Use `steam-preset %command%` as launch options.')
            raise Exit(code=1)

        # parse key
        key = preset_key or os.environ.get('SteamAppId', 'default')
        logger.debug(f'{key=} (source: {"--key flag" if preset_key else "env SteamAppId"})')

        # discover presets dynamically and pick by matching key
        registry = discover_presets()
        self._preset = preset = registry.get(key)
        if preset is None:
            logger.warning('No preset is loaded, steam-preset has no effect')
        else:
            logger.debug(f'Preset loaded from registry: {preset=}')

        # load preset extras
        preset_env_ = preset.env.copy() if isinstance(preset, PresetWithEnv) else default_preset.env
        preset_env = {str(k): str(v) for k, v in preset_env_.items()}
        preset_wrapper_ = preset.wrapper.copy() if isinstance(preset, PresetWithWrapper) else default_preset.wrapper
        preset_wrapper = [str(v) for v in preset_wrapper_]
        preset_arg_ = preset.arg.copy() if isinstance(preset, PresetWithArg) else default_preset.arg
        preset_arg = [str(v) for v in preset_arg_]
        logger.info(f'{preset_env=}')
        logger.info(f'{preset_wrapper=}')
        logger.info(f'{preset_arg=}')

        # construct the final version of cmd and env
        if isinstance(preset, PresetConfigurable):
            steam_env = os.environ.copy()
            self.env, self.cmd = preset.config(steam_env, steam_cmd, preset_env, preset_wrapper, preset_arg)
        else:
            self.env = os.environ | preset_env
            self.cmd = preset_wrapper + steam_cmd + preset_arg
        logger.debug(f'{self.env=}')
        logger.info(f'{self.cmd=}')

    def _run_key_mapper(self) -> None:
        # run the key mapper if exists
        if isinstance(self._preset, PresetWithKeyMapper):
            inputs.remap(self._preset.key_mapper)
            logger.info(f'{self._preset.key_mapper=}')

    def _run_init(self) -> None:
        # run the init script if exists
        if isinstance(self._preset, PresetInitializable):
            logger.info(f'running preset init function ...')
            self._preset.init()

    def _download_artwork(self) -> None:
        # download artwork if necessary
        artwork.download_if_necessary(self._artwork_id)

    def __enter__(self) -> Self:
        self._download_artwork()
        self._run_key_mapper()
        self._run_init()
        return self

    def __exit__(self, *_) -> None:
        pass

    def run(self) -> None:
        game_proc = sh.Popen(self.cmd, env=self.env)
        game_proc.wait()
