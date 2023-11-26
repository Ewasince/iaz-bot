import asyncio
import os
from typing import NoReturn

from aiogram import Bot, Dispatcher

from handlers import main_router, slider_router
from queue_maker import SECRETS_DIR


async def main() -> NoReturn:
    dp = Dispatcher()

    dp.include_routers(main_router, slider_router)
    with open(os.path.join(SECRETS_DIR, "bot_token.txt")) as f:
        token = f.read()

    bot = Bot(token, parse_mode="HTML")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
