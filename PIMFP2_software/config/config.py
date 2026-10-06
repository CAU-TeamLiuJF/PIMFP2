import os

from dynaconf import Dynaconf

config = Dynaconf(
    settings_files=[f"{os.environ.get('PROFILE', 'dev')}/config.toml"],
    envvar_prefix="PIMFP",
    root_path=os.path.abspath(__file__)
)
