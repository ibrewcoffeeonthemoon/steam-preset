import subprocess as sh
from pathlib import Path
from typing import Self

from steam_preset.game.spec import Spec
from steam_preset.log import logger
from steam_preset.presets.registry import Registry
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
        # discover presets dynamically and pick by matching key
        presets_dir = Path.home()/'.config/workspace/steam-preset/presets'
        registry = Registry(presets_dir)
        self._preset = registry.get(preset_key)
        self._spec = Spec(steam_cmd, self._preset)
        self._artwork_id = artwork_id

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
