import json
import subprocess as sh
from dataclasses import dataclass
from typing import cast


@dataclass
class Output:
    name: str
    make: str
    model: str
    width: str
    height: str
    refresh_rate: str


def focused_output() -> Output:
    result = sh.run(
        ['niri', 'msg', '-j', 'focused-output'],
        capture_output=True,
        text=True,
        check=True,
    )
    data: dict = json.loads(result.stdout)
    mode_id = cast(int, data.get('current_mode'))
    modes = cast(list[dict], data.get('modes'))
    mode = modes[mode_id]
    return Output(
        name=str(data.get('name', '')),
        make=str(data.get('make', '')),
        model=str(data.get('model', '')),
        width=str(mode.get('width')),
        height=str(mode.get('height')),
        refresh_rate=str(mode.get('refresh_rate')),
    )
