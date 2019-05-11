from global_config import syntax

from global_config.cfg import cfg
from global_config.syntax import (
    Is,
    Not,
    Any,
    All,
    Bypass,
)


cfg.add_bypass(syntax.SYSTEM_BYPASSES)
