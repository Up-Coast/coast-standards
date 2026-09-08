async def fetch(url):
    await asyncio.sleep(1)
    async with httpx.AsyncClient() as client:
        return (await client.get(url)).json()

def warm(url):
    time.sleep(1)
    return requests.get(url).json()
