from typing import Annotated, Any, NotRequired, Protocol, TypedDict, runtime_checkable

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

from . import default

Env = dict[str, str]
Wrapper = list[str]
Arg = list[str]
Cmd = list[str]
KeyMap = dict[int, int]


class KeyMapper(TypedDict):
    source: str
    target: NotRequired[str]
    key_map: KeyMap


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
    env: Annotated[Env, BeforeValidator(str_dict)] = Field(
        default_factory=lambda: str_dict(default.env)
    )

    # wrapper to be set, usually comes before %command%
    wrapper: Annotated[Wrapper, BeforeValidator(str_list)] = Field(
        default_factory=lambda: str_list(default.wrapper)
    )

    # arg to be set, usually comes after %command%
    arg: Annotated[Arg, BeforeValidator(str_list)] = Field(
        default_factory=lambda: str_list(default.arg)
    )

    key_mapper: KeyMapper | None = None

    @runtime_checkable
    class ConfigFunc(Protocol):
        # function receives everything needed to understand the current launch environment
        # use these infos to construct the final env and cmd to run the game
        def __call__(
            self,
            steam_env: Env,
            steam_cmd: Cmd,
            preset_env: Env,
            preset_wrapper: Wrapper,
            preset_arg: Arg,
        ) -> tuple[Env, Cmd]:
            ...
    config: ConfigFunc | None = None

    @runtime_checkable
    class InitFunc(Protocol):
        def __call__(self) -> None:
            ...
    init: InitFunc | None = None
