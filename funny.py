import re
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

running_processes = {}  # Store processes per channel


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

    process = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    running_processes[channel.id] = process

    output = []

    async def read_stream(stream, output_list):
        while True:
            line = await stream.readline()
            if not line:
                break
            cleaned_line = clean_up_output(line.decode())
            output_list.append(cleaned_line)
            # Show last 20 lines
            await message.edit(content=f"Output:\n```\n{''.join(output_list[-20:])}\n```")

    stdout_task = asyncio.create_task(read_stream(process.stdout, output))
    stderr_task = asyncio.create_task(read_stream(process.stderr, output))

    await asyncio.gather(stdout_task, stderr_task)
    await process.wait()

    running_processes.pop(channel.id, None)

    final_output = "\n".join(output) or "No output."
    await message.edit(content=f"Final Output:\n```\n{final_output[:1947]}\n```")


@bot.command(name='execstop')
async def exec_stop(ctx):
    process = running_processes.pop(ctx.channel.id, None)

    if process:
        try:
            process.kill()
            await ctx.send("The command has been forcefully stopped.")
            logging.info(f'Process {process.pid} forcefully stopped.')
        except Exception as e:
            await ctx.send(f"Error while stopping process: {e}")
            logging.error(f"Error while stopping process {process.pid}: {e}")
    else:
        await ctx.send("No running command found to stop.")


def clean_up_output(input_string):
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    clean_output = ansi_escape.sub('', input_string)
    return clean_output.replace('`', "'").replace('\x03', "")[:1947]


bot.run(TOKEN)
