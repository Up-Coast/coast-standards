async def fetch(url):
    time.sleep(1)
    return requests.get(url).json()
