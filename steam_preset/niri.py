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
    # use niri msg to fetch info of the focused output, fail on shell exit non zero
    cmd = ['niri', 'msg', '-j', 'focused-output']
    stdout = sh.run(cmd, capture_output=True, check=True).stdout

    # return Output as a validated model
    output = Output.model_validate_json(stdout)
    return output
