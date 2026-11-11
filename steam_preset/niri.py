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
        self.name = str(data.get('name', ''))
        self.make = str(data.get('make', ''))
        self.model = str(data.get('model', ''))
        mode_id = cast(int, data.get('current_mode'))
        modes = cast(list[dict], data.get('modes'))
        mode = modes[mode_id]
        self.width = str(mode.get('width'))
        self.height = str(mode.get('height'))
        self.refresh_rate = str(mode.get('refresh_rate'))
        #
        return self


def focused_screen() -> FocusedScreen:
    return FocusedScreen().update()
