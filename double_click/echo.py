import json
import os

import click
from mdv.markdownviewer import main as mdv
from requests import Response

CLI_THEME = float(os.getenv('CLI_THEME', 1057.4342))


def echo(output):
    """Formats and displays the provided output

    :param output: Supports int, str, dict, list(dict()), list, & Response
    :return:
    """
    if isinstance(output, dict) or isinstance(output, list):
        try:
            click.echo(json.dumps(output, indent=2))
        except (TypeError, ValueError):
            click.echo(str(output))
    elif isinstance(output, Response):
        if output.status_code is None:
            err = f"#Server Error \n" \
                f"> {output.url} - {output.text}"
            click.echo(mdv(md=err, theme=CLI_THEME, c_theme=CLI_THEME))
        elif output.status_code in [200, 201]:
            click.echo(json.dumps(output.json(), indent=4))
        elif output.status_code in [401, 403]:
            click.echo(mdv(md="#You do not have permissions to view this resource", theme=CLI_THEME, c_theme=CLI_THEME))
        elif output.status_code == 404:
            click.echo(mdv(md="#Unable to find the requested resource", theme=CLI_THEME, c_theme=CLI_THEME))
        elif output.status_code >= 500:
            err = f"#Server Error \n" \
                f"> {output.url} - {output.status_code} - {output.text}"
            click.echo(mdv(md=err, theme=CLI_THEME, c_theme=CLI_THEME))
        else:
            click.echo(output.text)
    elif isinstance(output, str) and output.startswith('#'):
        click.echo(mdv(md=output, theme=CLI_THEME, c_theme=CLI_THEME))
    else:
        click.echo(str(output))
