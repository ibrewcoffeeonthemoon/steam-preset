import subprocess as sh

from pydantic import BaseModel


class Output(BaseModel):
    name: str
    make: str
    model: str
    current_mode: int

    class Mode(BaseModel):
        width: int
        height: int
        refresh_rate: int
    modes: list[Mode]

    @property
    def width(self) -> str:
        return str(self.modes[self.current_mode].width)

    @property
    def height(self) -> str:
        return str(self.modes[self.current_mode].height)

    @property
    def refresh_rate(self) -> str:
        return str(self.modes[self.current_mode].refresh_rate)


def focused_output() -> Output:
    result = sh.run(
        ['niri', 'msg', '-j', 'focused-output'],
        capture_output=True,
        text=True,
        check=True,
    )

    output = Output.model_validate_json(result.stdout)

    return output
