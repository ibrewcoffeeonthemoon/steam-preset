import json
import subprocess as sh
from typing import Self, cast


class FocusedScreen:
    def update(self) -> Self:
        result = sh.run(
            ['niri', 'msg', '-j', 'focused-output'],
            capture_output=True,
            text=True,
            check=True,
        )
        data: dict = json.loads(result.stdout)
        self.name = cast(str, data.get('name', ''))
        self.make = cast(str, data.get('make', ''))
        self.model = cast(str, data.get('model', ''))
        mode_id = cast(int, data.get('current_mode'))
        modes = cast(list[dict], data.get('modes'))
        mode = modes[mode_id]
        self.width = cast(int, mode.get('width'))
        self.height = cast(int, mode.get('height'))
        self.refresh_rate = cast(int, mode.get('refresh_rate'))
        #
        return self


def focused_screen() -> FocusedScreen:
    return FocusedScreen().update()
