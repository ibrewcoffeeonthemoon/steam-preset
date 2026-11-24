from pathlib import Path
from typing import Annotated, Any, NotRequired, Protocol, TypedDict, runtime_checkable

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

__all__ = ['Env', 'Wrapper', 'Arg', 'Cmd', 'Env_', 'Wrapper_', 'Arg_', 'Cmd_', 'KeyMap', 'KeyMapper', 'Preset']

# raw types
Env = dict[str, str | int | Path]
Wrapper = list[str | int | Path]
Arg = list[str | int | Path]
Cmd = list[str]
KeyMap = dict[int, int]


class KeyMapper(TypedDict):
    source: str
    target: NotRequired[str]
    key_map: KeyMap


# validated types
Env_ = dict[str, str]
Wrapper_ = list[str]
Arg_ = list[str]
Cmd_ = Cmd


def str_dict(d: dict[Any, Any]) -> dict[str, str]:
    return {str(k): str(v) for k, v in d.items()}


def str_list(l: list[Any]) -> list[str]:
    return [str(v) for v in l]


class Preset(BaseModel):
    # allow input to be a ModuleType
    model_config = ConfigDict(
        from_attributes=True,
        arbitrary_types_allowed=True,
    )

    # env to be set, usually comes before %command%
    env: Annotated[Env_, BeforeValidator(str_dict)] = Field(default_factory=dict)

    # wrapper to be set, usually comes before %command%
    wrapper: Annotated[Wrapper_, BeforeValidator(str_list)] = Field(default_factory=list)

    # arg to be set, usually comes after %command%
    arg: Annotated[Arg_, BeforeValidator(str_list)] = Field(default_factory=list)

    key_mapper: KeyMapper | None = None

    @runtime_checkable
    class ConfigFunc(Protocol):
        # function receives everything needed to understand the current launch environment
        # use these infos to construct the final env and cmd to run the game
        def __call__(
            self,
            steam_env: Env_,
            steam_cmd: Cmd_,
            preset_env: Env_,
            preset_wrapper: Wrapper_,
            preset_arg: Arg_,
        ) -> tuple[Env_, Cmd_]:
            ...
    config: ConfigFunc | None = None

    @runtime_checkable
    class InitFunc(Protocol):
        def __call__(self) -> None:
            ...
    init: InitFunc | None = None
