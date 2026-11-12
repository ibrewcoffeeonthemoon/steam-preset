import os

from typer import Exit

from steam_preset.log import logger
from steam_preset.registry import Preset


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

        # load preset
        if preset is None:
            logger.error('No preset is loaded.')
            raise Exit(code=1)
        logger.info(f'{preset.env=}')
        logger.info(f'{preset.wrapper=}')
        logger.info(f'{preset.arg=}')

        # construct the final version of cmd and env
        if preset.config is not None:
            steam_env = os.environ.copy()
            self.env, self.cmd = preset.config(steam_env, steam_cmd, preset.env, preset.wrapper, preset.arg)
        else:
            self.env = os.environ | preset.env
            self.cmd = preset.wrapper + steam_cmd + preset.arg
        logger.debug(f'{self.env=}')
        logger.info(f'{self.cmd=}')
