import json
import os
import subprocess
import sys
from pathlib import Path
from distutils import sysconfig_get_python_lib

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
            try:
                click.echo(json.dumps(output.json(), indent=4))
            except json.decoder.JSONDecodeError:
                click.echo(output.text)
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


def display_version(package_name: str, md_file: str = 'VERSION.md'):
    md_path = Path(os.path.join(os.path.join(sysconfig_get_python_lib(), package_name), md_file))
    if os.path.exists(md_path):
        echo(mdv(filename=md_path))
    else:
        echo("#Unable to find version info.")


def update_package(package_name: str, force: bool = False, pip_args: list = []):
    """Use this to expose a command to update your CLI.

    pip_args will be passed as a list to add things like trusted-host or extra-index-url.

    Example:
        pip_args = ['--extra-index-url', 'https://artifactory.com/api/pypi/eg/simple',
                    '--trusted-host', 'artifactory.com']

    :param package_name:
    :param force:
    :param pip_args:
    :return:
    """
    if force:
        proc = subprocess.Popen(
            ['pip3', 'uninstall', '-y', package_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        output = proc.stdout.read().decode('utf-8')

    proc = subprocess.Popen(
        ['pip3', 'install', '--upgrade', package_name] + pip_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

    return proc.stdout.read().decode('utf-8')


def ensure_latest_package(package_name: str, pip_args: list = [], md_file: str = 'VERSION.md'):
    """Toss this in main to perform a check that the user is always running latest

    pip_args will be passed as a list to add things like trusted-host or extra-index-url.

    Example:
        pip_args = ['--extra-index-url', 'https://artifactory.com/api/pypi/eg/simple',
                    '--trusted-host', 'artifactory.com']

    :param package_name:
    :param pip_args:
    :param md_file:
    :return:
    """
    proc = subprocess.Popen(
        ['pip3', 'search', package_name] + pip_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output = proc.stdout.read().decode('utf-8')

    if 'INSTALLED' in output:
        version_info = output.replace(' ', '').split('\n')
        install_version = [info.replace('INSTALLED:', '') for info in version_info if 'INSTALLED' in info]
        latest_version = [info.replace('LATEST:', '') for info in version_info if 'LATEST' in info]

        if len(latest_version) > 0 and install_version != latest_version:
            update_package(package_name, pip_args=pip_args)
            display_version(package_name, md_file)
            echo('An update was retrieved that prevented your command from running.')
            echo('Please review changes and re-run your command.')
            sys.exit(0)
