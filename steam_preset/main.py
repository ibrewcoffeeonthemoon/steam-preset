import os
import subprocess as sh
from typing import Annotated

import typer
from typer import Argument, Exit, Option

from . import artwork, inputs
from .log import logger
from .presets import default as default_preset
from .presets.discovery import discover_presets
from .types import (
    Arg,
    Arg_,
    Env,
    Env_,
    PresetConfigurable,
    PresetInitializable,
    PresetWithArg,
    PresetWithEnv,
    PresetWithKeyMapper,
    PresetWithWrapper,
    Wrapper,
    Wrapper_,
)

app = typer.Typer(
    name='steam-preset',
    help='Intercept and modify Steam game launches with custom presets.',
)


# command with context settings
# - docs: https://click.palletsprojects.com/en/stable/api/#context
@app.command(context_settings=dict(
    # preserve all %command% expansion
    allow_extra_args=True,
    # prevent %command% expansion crashing typer or click
    ignore_unknown_options=True,
    # after seeing the first non-option str, treat all remaining str as args, this preserves the end of options '--' marks in %command%
    allow_interspersed_args=False,
))
def main(
    steam_cmd: Annotated[list[str] | None, Argument(help="The target command vector passed by Steam's %command% expansion.",), ] = None,
    preset_key: Annotated[str | None, Option('--key', help='Custom preset key to match against registry entries, overrides Steam app-id matching.',), ] = None,
    artwork_id: Annotated[str | None, Option('--artwork', help='The app-id used to fetch artwork and icon')] = None,
) -> None:
    # extract %command%
    if steam_cmd is None:
        logger.error('No %command% detected. Use `steam-preset %command%` as launch options.')
        raise Exit(code=1)

    # parse key
    key = preset_key or os.environ.get('SteamAppId', 'default')
    logger.debug(f'{key=} (source: {"--key flag" if preset_key else "env SteamAppId"})')

    # discover presets dynamically and pick by matching key
    registry = discover_presets()
    preset = registry.get(key)
    if preset is None:
        logger.warning('No preset is loaded, steam-preset has no effect')
    else:
        logger.debug(f'Preset loaded from registry: {preset=}')

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
        env, cmd = preset.config(steam_env, steam_cmd, preset_env, preset_wrapper, preset_arg)
    else:
        env = os.environ | preset_env
        cmd = preset_wrapper + steam_cmd + preset_arg
    logger.debug(f'{env=}')
    logger.info(f'{cmd=}')

    # run the key mapper if exists
    if isinstance(preset, PresetWithKeyMapper):
        inputs.remap(preset.key_mapper)
        logger.info(f'{preset.key_mapper=}')

    # run the init script if exists
    if isinstance(preset, PresetInitializable):
        logger.info(f'running preset init function ...')
        preset.init()

    # download artwork if necessary
    artwork.download_if_necessary(artwork_id)

    # run the game in subprocess
    game_proc = sh.Popen(cmd, env=env)
    game_proc.wait()
