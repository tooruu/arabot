import asyncio
import logging
from traceback import format_exc

from dotenv import load_dotenv

load_dotenv()
from .core import Ara


def main():
    logging.basicConfig(
        format="%(asctime)s|%(levelname)s|%(module)s|%(lineno)s|%(message)s",
        level=logging.INFO,
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    ara = Ara(loop=loop)
    try:
        loop.run_until_complete(ara.start())
    except (KeyboardInterrupt, SystemExit, asyncio.CancelledError):
        loop.run_until_complete(ara.close())
    except Exception:
        logging.critical(f"Bot has crashed: {format_exc()}")
        loop.run_until_complete(ara.close())
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.run_until_complete(asyncio.sleep(1))  # fixes RuntimeError on Windows w/ Proactor loop
        asyncio.set_event_loop(None)
        loop.stop()
        loop.close()


if __name__ == "__main__":
    main()
