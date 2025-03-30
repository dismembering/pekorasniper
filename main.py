import discord
import aiohttp
import re
import asyncio
import json
import time
import random

webhookurl = 'UR WEBHOOK'
discordtoken = 'UR DISCORD TOKEN'
pekoraCOOKIE = 'UR COOKIE'

itemreleasechannelid = 1307760060981579809
url_pattern = r'https?://(?:www\.)?\S+'
catalog_id_pattern = r'/catalog/(\d+)'

client = discord.Client()

async def fetch(session, url, headers, method="GET", json_data=None):
    async with session.request(method, url, headers=headers, json=json_data) as response:
        try:
            return await response.json()
        except:
            return None

async def purchase(session, asset_id, price):
    url = f'https://www.pekora.zip/apisite/economy/v1/purchases/products/{asset_id}'
    headers = {
        'cookie': f'.ROBLOSECURITY={pekoraCOOKIE}',
        'content-type': 'application/json',
        'user-agent': 'Mozilla/5.0'
    }
    data = {
        "assetId": asset_id,
        "expectedPrice": price,
        "expectedSellerId": 1,
        "userAssetId": None,
        "expectedCurrency": 1
    }

    async with session.post(url, headers=headers, json=data) as response:
        return response.status

async def getinfo(session, asset_id):
    url = f'https://www.pekora.zip/marketplace/productinfo?assetId={asset_id}'
    headers = {
        'cookie': f'.ROBLOSECURITY={pekoraCOOKIE}',
        'user-agent': 'Mozilla/5.0'
    }

    async with session.get(url, headers=headers) as response:
        return await response.json()

async def handle_message(message):
    if message.channel.id != itemreleasechannelid:
        return

    if "<@&1307760060470001668>" not in message.content:
        return

    links = re.findall(url_pattern, message.content)
    catalog_ids = [match.group(1) for link in links if (match := re.search(catalog_id_pattern, link))]

    if not catalog_ids:
        return

    connector = aiohttp.TCPConnector(limit=0
    async with aiohttp.ClientSession(connector=connector) as session:
        for catalog_id in catalog_ids:
            start_time = time.perf_counter()

            max_wait_time = 30
            item_info = None
            price = None

            while True:
                item_info = await getinfo(session, catalog_id)

                if not item_info:
                    print(f"cant get info on {catalog_id}")
                    break 

                if item_info.get("IsForSale"):
                    price = item_info["PriceInRobux"]
                    break 

                elapsed = time.perf_counter() - start_time
                if elapsed >= max_wait_time:
                    print(f"{catalog_id} never went on sale after {max_wait_time}s")
                    await send_webhook(f"@everyone item {catalog_id} never went on sale after {max_wait_time}s")
                    break

                print(f"Item {catalog_id} not for sale yet, retrying in 1sec...")
                await asyncio.sleep(1)

            purchase_start = time.perf_counter()
            await asyncio.sleep(random.uniform(1.6, 2.5)) # THIS IS UR DELAY, U CAN CHANGE TO WHATEVER U WANT OR REMOVE FULLY (THIS SHIT TAKES LIKE 300MS WITH NO DELAY LOL)
            status_code = await purchase(session, catalog_id, price)
            purchase_end = time.perf_counter()

            elapsed_time = round((purchase_end - purchase_start) * 1000, 2)

            message_content = {
                200: f"@everyone sniped dat hoe https://www.pekora.zip/catalog/{catalog_id}/-- {price} robux - took {elapsed_time}ms",
                403: f"@everyone unauthorized"
            }.get(
                status_code,
                f"@everyone idk WTF happened g {status_code}\n {item_info}"
            )

            await send_webhook(message_content)

async def send_webhook(content):
    async with aiohttp.ClientSession() as session:
        headers = {"Content-Type": "application/json"}
        data = json.dumps({"content": content})
        async with session.post(webhookurl, data=data, headers=headers) as response:
            return response.status

@client.event
async def on_ready():
    print(f'logged in as {client.user}')

@client.event
async def on_message(message):
    await handle_message(message)

client.run(discordtoken)
