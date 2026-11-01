import os
from typing import Annotated

import typer
from typer import Argument, Exit, Option

from steam_preset.game import Game

from . import artwork, inputs
from .log import logger
from .presets.discovery import discover_presets
from .types import (
    PresetInitializable,
    PresetWithKeyMapper,
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

    # run the game
    with Game(preset, steam_cmd) as game:
        game.run()
