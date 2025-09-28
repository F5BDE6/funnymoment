from dataclasses import dataclass
from shutil import rmtree
from tempfile import mkdtemp, mkstemp
import discord
from discord import Interaction
import os
import uuid

import yt_dlp
from discord import  app_commands

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

discord_guild = os.environ["DISCORD_GUILD"]
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

@dataclass
class Voices:
    client: discord.VoiceClient

def download_audio(id: str) -> str:
    _, video_filename = mkstemp()
    os.remove(video_filename)

    ydl_opts = {
        'outtmpl': f'{video_filename}',
        'format': 'bestaudio/best',
        'merge_output_format': 'opus',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([f"https://www.youtube.com/watch?v={id}"])

    return video_filename

async def connect_to_voice(voice_id: int):
    ch = await client.fetch_channel(voice_id)
    connection = await ch.connect()

    global state
    state.client = connection

global state
state = Voices(None)

@tree.command(
    name="hello",
    description="says hi",
    guild=discord.Object(id=discord_guild)
)
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message("Hello!")

@tree.command(
    name="connect",
    description="connects to vc",
    guild=discord.Object(id=discord_guild)
)
async def connect(interaction: discord.Interaction):
    voice: discord.VoiceState = await interaction.user.fetch_voice()

    await connect_to_voice(voice.channel.id)

    await interaction.response.send_message("Successfully connected to voice channel")

@tree.command(
    name="play",
    description="plays funny id",
    guild=discord.Object(id=discord_guild)
)
async def play(interaction: Interaction, id: str):
    voice: discord.VoiceState = await interaction.user.fetch_voice()

    if state.client is None:
        await connect_to_voice(voice.channel.id)

    state.client.stop()
    await interaction.response.send_message(f"Trying to play {id}")
    filename = download_audio(id)
    source = discord.FFmpegOpusAudio(filename)
    state.client.play(source, after=lambda e: print(f'Player error: {e}') if e else None)

@tree.command(
    name="resume",
    description="Resumes",
    guild=discord.Object(id=discord_guild)
)
async def resume(interaction: Interaction):
    if state.client.is_playing():
        await interaction.response.send_message("It is already playing")
        return

    state.client.resume()
    await interaction.response.send_message("Resumed")

@tree.command(
    name="pause",
    description="pauses",
    guild=discord.Object(id=discord_guild)
)
async def pause(interaction: Interaction):
    if state.client is None or not state.client.is_playing():
        await interaction.response.send_message("Nothing playing")
        return

    state.client.pause()
    await interaction.response.send_message(f"Paused")

@tree.command(
    name="stop",
    description="Stops",
    guild=discord.Object(id=discord_guild)
)
async def stop(interaction: Interaction):
    if state.client is None or not state.client.is_playing():
        await interaction.response.send_message("Nothing playing")
        return

    state.client.stop()
    await interaction.response.send_message("Stopped")

# @tree.command(
#     name="hellnaw",
#     description="hell naw",
#     guild=discord.Object(id=discord_guild)
# )
# async def play(interaction: Interaction):
#     interaction.message.author

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message: discord.message.Message):
    if message.author == client.user:
        return

@client.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=discord_guild))
    print ("Log : "+str(client.user))

if __name__ == "__main__":
    client.run(os.environ["DISCORD_TOKEN"])
