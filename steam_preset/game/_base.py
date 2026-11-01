import os
import subprocess as sh
from typing import Self

from typer import Exit

from steam_preset.game.spec import Spec
from steam_preset.log import logger
from steam_preset.presets import registry
from steam_preset.types import (
    PresetInitializable,
    PresetWithKeyMapper,
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
        self._preset = preset = registry.scan().get(key)
        if preset is None:
            logger.warning('No preset is loaded, steam-preset has no effect')
        else:
            logger.debug(f'Preset loaded from registry: {preset=}')

        # spec
        self._spec = Spec(steam_cmd, preset)

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
        game_proc = sh.Popen(self._spec.cmd, env=self._spec.env)
        game_proc.wait()
