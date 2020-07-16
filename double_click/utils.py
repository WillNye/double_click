import asyncio
import json
import os
import pkg_resources
import re
import subprocess
import sys
from configparser import ConfigParser
from dateutil.parser import parse as date_parse
from datetime import datetime as dt, timedelta
from typing import NewType
from pathlib import Path

try:
    from distutils import sysconfig_get_python_lib as get_python_lib
except ImportError:
    # There doesn't seem to be any consistency on this import so have to handle both import types.
    from distutils.sysconfig import get_python_lib

from mdv.markdownviewer import main as mdv
from requests import Response

CLI_THEME = float(os.getenv('CLI_THEME', 1057.4342))
URL_PATTERN = re.compile('^(http:\/\/|https:\/\/)[a-z0-9]+([\-\.]{1}[a-z0-9]+)*\.[a-z]{2,5}(:[0-9]{1,5})?(\/.*)?$')
EventLoop = NewType('Eventloop', asyncio.windows_events._WindowsSelectorEventLoop) \
        if sys.platform == 'win32' else NewType('Eventloop', asyncio.unix_events._UnixSelectorEventLoop)


def is_valid_url(url: str, raises=True) -> bool:
    if URL_PATTERN.match(url):
        return True
    elif raises:
        raise ValueError(f'Invalid URL {url}')
    else:
        return False


class Config(ConfigParser):
    def __init__(self, config_path, *args, **kwargs):
        self._config_path = Path(os.path.expanduser(config_path))

        if not os.path.exists(self._config_path):
            path_as_list = str(self._config_path).split('/')
            os.makedirs(Path("/".join(path_as_list[:-1])), exist_ok=True)

        super(ConfigParser, self).__init__(*args, **kwargs)
        self.read(self.path)

    @property
    def path(self):
        return self._config_path

    def save(self):
        with open(self._config_path, 'w') as fout:
            self.write(fout)


def echo(output):
    """Formats and displays the provided output

    :param output: Supports int, str, dict, list(dict()), list, & Response
    :return:
    """
    if isinstance(output, dict) or isinstance(output, list):
        try:
            print(json.dumps(output, indent=2))
        except (TypeError, ValueError):
            print(str(output))
    elif isinstance(output, Response):
        if output.status_code is None:
            err = f"#Server Error \n" \
                f"> {output.url} - {output.text}"
            print(mdv(md=err, theme=CLI_THEME, c_theme=CLI_THEME))
        elif output.status_code in [200, 201]:
            try:
                print(json.dumps(output.json(), indent=4))
            except json.decoder.JSONDecodeError:
                print(output.text)
        elif output.status_code in [401, 403]:
            print(mdv(md="#You do not have permissions to view this resource", theme=CLI_THEME, c_theme=CLI_THEME))
        elif output.status_code == 404:
            print(mdv(md="#Unable to find the requested resource", theme=CLI_THEME, c_theme=CLI_THEME))
        elif output.status_code >= 500:
            err = f"#Server Error \n" \
                f"> {output.url} - {output.status_code} - {output.text}"
            print(mdv(md=err, theme=CLI_THEME, c_theme=CLI_THEME))
        else:
            print(output.text)
    elif isinstance(output, str) and output.startswith('#'):
        print(mdv(md=output, theme=CLI_THEME, c_theme=CLI_THEME))
    else:
        print(str(output))


def display_version(package_name: str, md_file: str = 'VERSION.md'):
    md_path = Path(os.path.join(os.path.join(get_python_lib(), package_name), md_file))
    if os.path.exists(md_path):
        echo(mdv(filename=md_path))


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
    stdout = proc.stdout.read().decode('utf-8')
    stderr = proc.stderr.read().decode('utf-8')
    return f"{stdout}\n{stderr}" if stdout else stderr


def ensure_latest_package(package_name: str, pip_args=[], md_file: str = 'VERSION.md', update_pkg_pip_args=[]):
    """Toss this in main to perform a check that the user is always running latest

    pip_args will be passed as a list to add things like trusted-host or extra-index-url.

    Example:
        pip_args = ['--extra-index-url', 'https://artifactory.com/api/pypi/eg/simple',
                    '--trusted-host', 'artifactory.com']

    :param package_name:
    :param pip_args:
    :param md_file: Display this file if the package was updated
    :param update_pkg_pip_args: pip args pass to update_package on out of date package e.g. --extra-index-url
    :return:
    """
    config = Config('~/.double_click/package_versions.ini')

    if not config.has_section(package_name):
        config.add_section(package_name)
        last_checked = None
    else:
        last_checked = config.get(package_name, 'last_checked')

    if not last_checked or date_parse(last_checked) < dt.utcnow() - timedelta(hours=1):
        try:
            latest_version = None
            current_version = pkg_resources.get_distribution(package_name).version
            version_output = update_package(f'{package_name}==DoesNotExist', pip_args=update_pkg_pip_args)
            version_output = [line for line in version_output.split('\n') if 'DoesNotExist (from versions:' in line]
            if version_output:
                versions = re.findall(r'([0-9][^,)]+)', version_output[0])
                latest_version = versions[-1]

            if latest_version and current_version != latest_version:
                update_pkg_pip_args = update_pkg_pip_args if update_pkg_pip_args else pip_args
                update_package(package_name, pip_args=update_pkg_pip_args)
                config.set(package_name, 'last_checked', str(dt.utcnow()))
                update_msg = f'#An update to {package_name} was retrieved that prevented your command from running.'
                if md_file:
                    display_version(package_name, md_file)
                    update_msg += f'\nPlease review changes and re-run your command.'
                else:
                    update_msg += f'\nPlease re-run your command.'
                echo(update_msg)
                sys.exit(0)
        except pkg_resources.DistributionNotFound:
            # This should only occur during testing
            echo(f'{package_name} not found')

        config.set(package_name, 'last_checked', str(dt.utcnow()))
        config.save()
