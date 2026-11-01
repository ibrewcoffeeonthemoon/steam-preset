from pathlib import Path
from typing import Annotated

import typer
from typer import Argument, Option

from steam_preset.game import Game

DEFAULT_PRESETS_DIR = Path.home() / '.config/workspace/steam-preset/presets'

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
    presets_dir: Annotated[Path, Option('--presets-dir', help='Directory path containing presets')] = DEFAULT_PRESETS_DIR,
) -> None:
    # Game
    with Game(steam_cmd, preset_key, artwork_id, presets_dir) as game:
        # run the game
        game.run()
