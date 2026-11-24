from pathlib import Path

__all__ = ['HOME', 'XDG_CONFIG_HOME']

HOME = Path.home()
XDG_CONFIG_HOME = HOME/'.config'
