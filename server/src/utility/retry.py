import asyncio
import random
import psycopg

def transient_error(err):
    return isinstance(err, (psycopg.OperationalError, ConnectionError))

async def retry_async(fn, retries=3, base_delay=0.1):
    for i in range(retries):
        try:
            return await fn()
        except Exception as err:
            if not transient_error(err) or i == retries - 1:
                raise err

            delay = (base_delay + random.uniform(0, 0.1)) * (2 ** i)
            await asyncio.sleep(delay)