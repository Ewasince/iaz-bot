import asyncio
from typing import NoReturn

from aiogram import Bot, Dispatcher

from handlers import main_router, slider_router


async def main() -> NoReturn:
    dp = Dispatcher()

    dp.include_routers(
        main_router,
        slider_router
    )

    bot = Bot('YOUR_TOKEN', parse_mode="HTML")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
