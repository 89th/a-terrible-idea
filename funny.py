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

running_processes = {}


@bot.event
async def on_ready():
    logging.info(f'Logged in as {bot.user.name}')
    channel_id = 1224502675148771348
    channel = bot.get_channel(channel_id)
    if channel:
        await channel.send("I am online. Please kill me.")


@bot.command(name='exec')
async def exec_command(ctx, *, command):
    logging.info(f'Executing command: {command}')

    channel = ctx.channel
    message = await channel.send("Executing command...")

    env = os.environ.copy()
    env['TERM'] = 'xterm'

    if not command.startswith("stdbuf"):
        command = f"stdbuf -oL {command}"

    process = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        preexec_fn=os.setsid,
        env=env
    )

    if channel.id not in running_processes:
        running_processes[channel.id] = []

    running_processes[channel.id].append(process)

    output = []

    async def read_stream(stream, output_list):
        while True:
            line = await stream.readline()
            if not line:
                break
            cleaned_line = clean_up_output(line.decode())
            output_list.append(cleaned_line)
            await message.edit(content=f"Output:\n```\n{''.join(output_list[-20:])}\n```")

    stdout_task = asyncio.create_task(read_stream(process.stdout, output))
    stderr_task = asyncio.create_task(read_stream(process.stderr, output))

    await asyncio.gather(stdout_task, stderr_task)
    await process.wait()

    running_processes[channel.id].remove(process)

    final_output = "\n".join(output) or "No output."
    await message.edit(content=f"Final Output:\n```\n{final_output[:1947]}\n```")


@bot.command(name='execstop')
async def exec_stop(ctx):
    if ctx.channel.id not in running_processes or not running_processes[ctx.channel.id]:
        await ctx.send("No running command found to stop.")
        return

    processes = running_processes.pop(ctx.channel.id, [])

    for process in processes:
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            await ctx.send(f"Process {process.pid} and its children have been stopped.")
            logging.info(
                f"Process {process.pid} and its group forcefully stopped.")
        except Exception as e:
            await ctx.send(f"Error stopping process {process.pid}: {e}")
            logging.error(f"Error stopping process {process.pid}: {e}")


def clean_up_output(input_string):
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    clean_output = ansi_escape.sub('', input_string)
    return clean_output.replace('`', "'").replace('\x03', "")[:1947]


bot.run(TOKEN)
