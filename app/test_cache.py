import asyncio
from decimal import Decimal
from app.cache.price_cache import set_price, get_price

async def test():
    await set_price('AAPL', Decimal('189.42'))
    price = await get_price('AAPL')
    print(price)

asyncio.run(test())
