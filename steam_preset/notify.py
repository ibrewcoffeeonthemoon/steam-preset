import shutil
import subprocess as sh


def send(
    summary: str,
    body: str,
    icon: str = 'input-keyboard',
) -> None:
    if shutil.which('notify-send'):
        try:
            sh.Popen([
                'notify-send',
                '--app-name', 'steam-preset',
                '--icon', icon,
                '--urgency', 'low',
                summary,
                body,
            ])
        except OSError:
            pass
