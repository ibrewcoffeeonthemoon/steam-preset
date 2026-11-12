import os

from typer import Exit

from steam_preset.log import logger
from steam_preset.registry import default as default_preset
from steam_preset.registry.types import (
    Preset,
    PresetConfigurable,
    PresetWithArg,
    PresetWithEnv,
    PresetWithWrapper,
)


class Spec:
    def __init__(
        self,
        steam_cmd: list[str] | None,
        preset: Preset | None,
    ) -> None:
        # extract %command%
        if steam_cmd is None:
            logger.error('No %command% detected. Use `steam-preset %command%` as launch options.')
            raise Exit(code=1)

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
