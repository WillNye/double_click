import os

width, height = os.get_terminal_size()
os.environ.setdefault('width', str(width))
os.environ.setdefault('LINES', str(height))

from double_click.utils import display_version, echo, update_package, ensure_latest_package
from double_click.request import GeneralSession, UserSession
from double_click.markdown import generate_md_bullet_str, generate_md_code_str, generate_md_table_str
from double_click.models import Model, ModelAuth
from double_click.user import User

