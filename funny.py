import discord
from discord.ext import commands
from dotenv import load_dotenv
import subprocess
import logging
import asyncio
import os
import signal

logging.basicConfig(level=logging.INFO)

intents = discord.Intents.default()
intents.message_content = True
load_dotenv()
TOKEN = os.getenv('TOKEN_DISCORD_BOT')

bot = commands.Bot(command_prefix='', intents=intents)

running_processes = {}


@bot.event
async def on_ready():
    logging.info(f'Logged in as {bot.user.name}')
    # Dont Ask Channel
    channel_id = 1224502675148771348
    channel = bot.get_channel(channel_id)
    if channel:
        await channel.send("I am online. Pleae kill me.")


@bot.command(name='exec')
async def exec_command(ctx, *, command):
    logging.info(f'Executing command: {command}')

    channel = ctx.channel
    message = await channel.send("Executing command...")

    process = subprocess.Popen(command, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, shell=True, universal_newlines=True)

    try:
        # Use communicate() and wait for the process to finish
        output, error = await asyncio.to_thread(process.communicate)

        # Handle the output
        if output:
            await message.edit(content=f"Output:\n```\n{clean_up_output(output)}\n```")
        if error:
            await message.edit(content=f"Error:\n```\n{clean_up_output(error)}\n```")

    except asyncio.TimeoutError:
        process.kill()
        await message.edit(content="Command timed out and was terminated.")
        logging.warning("Command timed out and was terminated.")
    except Exception as e:
        await message.edit(content=f"An error occurred: {e}")
        logging.exception("Error while executing command")


@bot.command(name='execstop')
async def exec_stop(ctx):
    process = running_processes.pop(ctx.message.id, None)

    if process:
        try:
            os.kill(process.pid, signal.SIGKILL)
            await ctx.send("The command has been forcefully stopped.")
            logging.info(
                f'Process {process.pid} forcefully stopped with SIGKILL.')
        except Exception as e:
            await ctx.send(f"Error while stopping process: {e}")
            logging.error(f"Error while stopping process {process.pid}: {e}")
    else:
        await ctx.send("No running command found to stop.")


def clean_up_output(input_string):
    return input_string.replace('`', "'").replace('', "")[:1947]


bot.run(TOKEN)
