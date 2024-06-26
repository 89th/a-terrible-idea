import discord
from discord.ext import commands
import subprocess
import logging

# Setup basic logging
logging.basicConfig(level=logging.INFO)

intents = discord.Intents.default()
intents.message_content = True  # Enable message content intent

TOKEN = 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    logging.info(f'Logged in as {bot.user.name}')
    channel_id = 1224502675148771348  # Change this to your desired channel ID
    channel = bot.get_channel(channel_id)
    if channel:
        await channel.send("I am online")

@bot.command(name='exec')
async def exec_command(ctx, *, command):
    logging.info(f'Executing command: {command}')
    try:
        output = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True, timeout=30, universal_newlines=True)
    except subprocess.CalledProcessError as e:
        error_message = f'Error:\n```\n{clean_up_output(e.output)}\n```'
        # Truncate the message to 1950 characters if it's too long
        if len(error_message) > 1950:
            await ctx.send(f'{clean_up_output(error_message)}...')
        else:
            await ctx.send(error_message)
        logging.error(f'Command error: {clean_up_output(e.output)}')
    except Exception as e:
        await ctx.send(f'An error occurred: {e}')
        logging.exception('Unexpected error')
    else:
        # If there's output, truncate if necessary and send it
        if output:
            message = f'Output:\n```\n{clean_up_output(output)}\n```'
            if len(message) > 1950:
                await ctx.send(f'{message}...')
            else:
                await ctx.send(message)
            logging.info(f'Command output: {clean_up_output(output)}')
        else:
            await ctx.send('Command executed successfully with no output.')
            logging.info('Command executed successfully with no output.')

def clean_up_output(input_string):
    return input_string.replace('`', "'").replace('',"")[:1947]

bot.run(TOKEN)