import os
import subprocess as sh
from typing import Self

from .log import logger
from .presets import default as default_preset
from .types import *
from .types import PresetConfigurable, PresetWithArg, PresetWithEnv, PresetWithWrapper


class Game:
    def __init__(
        self,
        preset: Preset | None,
        steam_cmd: list[str],
    ) -> None:
        # load preset extras
        preset_env_: Env_ = preset.env.copy() if isinstance(preset, PresetWithEnv) else default_preset.env
        preset_env: Env = {str(k): str(v) for k, v in preset_env_.items()}
        preset_wrapper_: Wrapper_ = preset.wrapper.copy() if isinstance(preset, PresetWithWrapper) else default_preset.wrapper
        preset_wrapper: Wrapper = [str(v) for v in preset_wrapper_]
        preset_arg_: Arg_ = preset.arg.copy() if isinstance(preset, PresetWithArg) else default_preset.arg
        preset_arg: Arg = [str(v) for v in preset_arg_]
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

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_) -> None:
        pass

    def run(self) -> None:
        game_proc = sh.Popen(self.cmd, env=self.env)
        game_proc.wait()
