import requests
from lxml import html
import discord
from discord.ext import commands, tasks
import json
import os
import traceback

TOKEN = ''
CHANNEL_ID = ''
URL = ''
HEADERS = {"User-Agent": ""}
DATA_FILE = ''

  #Prefix:
intents = discord.Intents.default()
intents.message_content = True  #message content intent

bot = commands.Bot(command_prefix='!', intents=intents)

  #Scrapping:
def get_amazon_price(URL, HEADERS):
    response = requests.get(URL, HEADERS)
    tree = html.fromstring(response.content)

  #XPath
    price_tag = tree.xpath('')

  #Error handling:
    if price_tag:
        price = price_tag[0].strip().replace('$', '').replace(',', '')
        try:
            return float(price)
        except ValueError:
            raise ValueError("Failed to convert price to float.")
    else:
        print(html.tostring(tree, pretty_print=True).decode())
        raise ValueError("Price not found on the page.")


def load_price_data(file_path):
    if not os.path.exists(file_path):
        return {}

    try:
        with open(file_path, 'r') as file:
            data = file.read().strip()
            if not data:
                return {}
            return json.loads(data)
    except json.JSONDecodeError as e:
        print(f"Error reading JSON data: {e}")
        return {}


def save_price_data(file_path, data):
    with open(file_path, 'w') as file:
        json.dump(data, file)


async def send_discord_message(message):
    channel = bot.get_channel(int(CHANNEL_ID))
    await channel.send(message)

  #Login:
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    try:
        track_price.start()  # Start the scheduled task
    except Exception as e:
        print(f'Error starting track_price: {e}')
        traceback.print_exc()

  #Price update:
@tasks.loop(hours=1)
async def track_price():
    try:
        price_data = load_price_data(DATA_FILE)
        current_price = get_amazon_price(URL, HEADERS)
        last_price = price_data.get('last_price', None)

        if last_price is None or current_price != last_price:
            price_data['last_price'] = current_price
            save_price_data(DATA_FILE, price_data)
            message = f'Price update: The price is now ${current_price:.2f}.'
            await send_discord_message(message)
    except Exception as e:
        print(f'Error in track_price: {e}')
        traceback.print_exc()


@bot.command()
async def price(ctx):
    try:
        current_price = get_amazon_price(URL, HEADERS)
        await ctx.send(f'The current price is ${current_price:.2f}.')
    except Exception as e:
        await ctx.send(f'Error retrieving price: {e}')
        print(f'Error in price command: {e}')
        traceback.print_exc()


@bot.command()
async def track(ctx):
    try:
        track_price.start()
        await ctx.send('Started price tracking.')
    except Exception as e:
        await ctx.send(f'Error starting price tracking: {e}')
        print(f'Error in track command: {e}')
        traceback.print_exc()


bot.run(TOKEN)
