import requests
from lxml import html
from bs4 import BeautifulSoup
import discord
from discord.ext import commands, tasks
import json
import os
import traceback

TOKEN = ''
CHANNEL_ID = ''
URL = 'https://www.amazon.com/Oculus-Quest-Advanced-All-One-Virtual/dp/B099VMT8VZ/ref=sr_1_2?crid=2YGWVUFDZLWGS&currency=AED&dib=eyJ2IjoiMSJ9.95famZUxpx3ASjQL-Xphs_51dKOB53WamjMeAmS0C0pufPSdOjt5wZ8VCFUiJHCneLTmAXcqB-mz4qpoMzTDaDbLO7GopwiZJd2RtIqMX_1stmdjrbFVIjg6G9O83ATKsPM_78tRyUYQiaPY3YegFUHZjJMEfytP0m42M_iIkh8Kesr8sE6oUQJJNC5NpV1UEwKkyak4FcZ0O0XWGNyiX8cr1cguZ7Y3uJEnyVLrgQc.DIC1xQVDBzBL-1R7Kt2UkFHHdlaX9Huj6kZSl4OMza8&dib_tag=se&keywords=meta%2Bquest%2B3&qid=1717853518&sprefix=meta%2Bq%2Caps%2C262&sr=8-2&th=1'
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0"}
DATA_FILE = 'C:/Users/GondalF/Desktop/testing/price_data.json'

intents = discord.Intents.default()
intents.message_content = True  # Enable the message content intent

bot = commands.Bot(command_prefix='!', intents=intents)


def get_amazon_price(url, headers):
    response = requests.get(url, headers=headers)

    # Use BeautifulSoup to parse the page
    soup = BeautifulSoup(response.content, 'html.parser')

    # Attempt to find the price using different methods
    price_tag = soup.select_one('span.aok-align-center:nth-child(3) > span:nth-child(2)')

    if not price_tag:
        # Try using lxml and XPath
        tree = html.fromstring(response.content)
        price_tag = tree.xpath(
            '/html/body/div[1]/div/div[10]/div[5]/div[4]/div[15]/div/div/div[3]/div[1]/span[3]/span[2]/text()')

        if price_tag:
            price_tag = price_tag[0]

    if not price_tag:
        price_tag = soup.find('span', {'id': 'priceblock_ourprice'})
    if not price_tag:
        price_tag = soup.find('span', {'id': 'priceblock_dealprice'})
    if not price_tag:
        price_tag = soup.find('span', {'class': 'a-price-whole'})

    if price_tag:
        price = price_tag.text.strip().replace('$', '').replace(',', '')
        try:
            return float(price)
        except ValueError:
            raise ValueError("Failed to convert price to float.")
    else:
        # Print the page content to help debug
        print(soup.prettify())
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


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    try:
        track_price.start()  # Start the scheduled task
    except Exception as e:
        print(f'Error starting track_price: {e}')
        traceback.print_exc()


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


bot.run(TOKEN)