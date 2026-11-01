import multiprocessing as mp
import subprocess as sh
from pathlib import Path
from typing import Self

from steam_preset import notify
from steam_preset.log import logger
from steam_preset.presets.registry import Registry
from steam_preset.types import (
    PresetInitializable,
    PresetWithKeyMapper,
)

from . import artwork, inputs
from .spec import Spec


class Game:
    def __init__(
        self,
        steam_cmd: list[str] | None,
        preset_key: str | None,
        artwork_id: str | None,
        presets_dir: Path,
    ) -> None:
        # discover presets dynamically and pick by matching key
        registry = Registry(presets_dir)
        self._preset = registry.get(preset_key)
        self._spec = Spec(steam_cmd, self._preset)
        self._artwork_id = artwork_id
        # proc
        self._key_mapper_proc: mp.Process | None = None
        self._game_proc: sh.Popen | None = None

    def _run_key_mapper(self) -> None:
        # run the key mapper if exists
        if isinstance(self._preset, PresetWithKeyMapper):
            self._key_mapper_proc = inputs.remap(self._preset.key_mapper)
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
        # quit the game proc gracefully
        if self._game_proc:
            logger.warning('terminating game process ...')
            self._game_proc.terminate()
            self._game_proc.wait()
            logger.info('terminated game process')
        # quit the key mapper proc gracefully
        if self._key_mapper_proc:
            logger.warning('terminating key mapper process ...')
            self._key_mapper_proc.terminate()
            self._key_mapper_proc.join()
            logger.info('terminated key mapper process')
            notify.send('Disabled Key Mapper', 'steam-preset key mapper restored input device')

    def run(self) -> None:
        self._game_proc = sh.Popen(self._spec.cmd, env=self._spec.env)
        self._game_proc.wait()
