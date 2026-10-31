import importlib
import importlib.util
import logging
import os
import pkgutil
import subprocess as sh
from pathlib import Path
from typing import Annotated

import typer
from typer import Argument, Exit, Option

from . import artwork, default_preset, inputs
from .types import (
    Arg,
    Arg_,
    Env,
    Env_,
    Preset,
    PresetConfigurable,
    PresetInitializable,
    PresetWithArg,
    PresetWithEnv,
    PresetWithKeyMapper,
    PresetWithWrapper,
    Wrapper,
    Wrapper_,
)

Registry = dict[str, Preset]

logging.basicConfig(level=logging.INFO, format='[ %(name)s ]: %(levelname)s: %(message)s')
logger = logging.getLogger('steam-preset')

app = typer.Typer(
    name='steam-preset',
    help='Intercept and modify Steam game launches with custom presets.',
)


def discover_presets() -> Registry:
    #
    registry: Registry = {}

    # iterate through all python modules in the presets package
    presets_dir = Path.home() / '.config/workspace/steam-preset/presets'
    if not presets_dir.is_dir():
        return registry

    # convert Path to string for pkgutil
    for _, module_name, _ in pkgutil.iter_modules([str(presets_dir)]):
        file_path = presets_dir / f'{module_name}.py'

        # dynamically load the module from file path
        try:
            spec = importlib.util.spec_from_file_location(
                f'presets.{module_name}', file_path
            )
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                logger.debug(f'Imported {module}')

                # register module by its key attribute if defined
                if isinstance(module, Preset):
                    registry[str(module.key)] = module
                    logger.info(f'Discovered {module}')
        except ImportError as e:
            logger.error(f'Failed to import preset {file_path.name}: {e}')
        except Exception as e:
            logger.error(f'Unexpected error loading preset {file_path.name}: {e}')
    #
    return registry


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
