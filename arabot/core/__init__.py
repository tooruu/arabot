from importlib.util import find_spec

from arabot.core.bot import (
    Ara,
)
from arabot.core.config import (
    Config,
)
from arabot.core.database import (
    get_db_session,
)
from arabot.core.enums import (
    Category,
    Color,
    CustomEmoji,
    SettingKey,
)
from arabot.core.errors import (
    StopCommand,
)
from arabot.core.patches import (
    Cog,
    Context,
    LocalizationStore,
)
from arabot.core.pfxless import (
    pfxless,
    PfxlessOnCooldown,
)

if find_spec("uvloop"):
    from uvloop import new_event_loop
elif find_spec("winloop"):
    from winloop import new_event_loop
else:
    from asyncio import new_event_loop
