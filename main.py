from dataclasses import dataclass
import discord
from discord import Interaction, Member, VoiceChannel
import os

import yt_dlp
from discord import app_commands
from discord.member import VocalGuildChannel

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

discord_guild = os.environ["DISCORD_GUILD"]
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


@dataclass
class State:
    client: discord.VoiceClient | None = None


async def connect_to_voice(channel: VocalGuildChannel|None) -> bool:
    if isinstance(channel, VoiceChannel):
        connection = await channel.connect()
        global state
        state.client = connection
        return True
    else:
        return False


global state
state = State()


@tree.command(
    name="hello", description="says hi", guild=discord.Object(id=discord_guild)
)
async def hello(interaction: discord.Interaction):
    _ = await interaction.response.send_message("Hello!")


@tree.command(
    name="connect", description="connects to vc", guild=discord.Object(id=discord_guild)
)
async def connect(interaction: discord.Interaction):
    if isinstance(interaction.user, Member)
        voice: discord.VoiceState = await interaction.user.fetch_voice()

        if await connect_to_voice(voice.channel):
            _ = await interaction.response.send_message(
                "Successfully connected to voice channel"
            )
        else:
            _ = await interaction.response.send_message(
                "Failed to connected to voice channel"
            )
    else:
        print("Interaction user is not a insteanceof Member")

def get_play_url(id: str)->str|None:
    ydl_opts = {
            'format': 'bestaudio/best',
            'merge_output_format': 'opus',
        }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info=ydl.extract_info(f"https://www.youtube.com/watch?v={id}")
        return info.get("url")

@tree.command(
    name="play", description="plays funny id", guild=discord.Object(id=discord_guild)
)
async def play(interaction: Interaction, id: str):
    if not isinstance(interaction.user, Member) and state.client is None:
        _ = await interaction.response.send_message(f"Failed to play {id}")
    elif isinstance(interaction.user, Member) :
        voice: discord.VoiceState = await interaction.user.fetch_voice()

        if state.client is None:
            if isinstance(voice, VocalGuildChannel):
                if await connect_to_voice(voice.channel):
                    _ = await interaction.response.send_message(
                        "Successfully connected to voice channel"
                    )
                else:
                    _ = await interaction.response.send_message(
                        "Failed to connected to voice channel"
                    )
    assert state.client is not None
    state.client.stop()
    _ = await interaction.response.send_message(f"Trying to play {id}")
    url=get_play_url(id)
    if url is not None:
        source = discord.FFmpegOpusAudio(url, options="-vn")
        state.client.play(
            source, after=lambda e: print(f"Player error: {e}") if e else None
        )
    else:
         _ = await interaction.response.send_message(f"Invalid id: {id}")


@tree.command(
    name="resume", description="Resumes", guild=discord.Object(id=discord_guild)
)
async def resume(interaction: Interaction):
    if state.client is not None:
        if state.client.is_playing():
            _ = await interaction.response.send_message("It is already playing")
            return

        state.client.resume()
        _ = await interaction.response.send_message("Resumed")
    else:
        _ = await interaction.response.send_message("Bot is not in a VC")


@tree.command(
    name="pause", description="pauses", guild=discord.Object(id=discord_guild)
)
async def pause(interaction: Interaction):
    if state.client is None or not state.client.is_playing():
        _ = await interaction.response.send_message("Nothing playing")
        return

    state.client.pause()
    _ = await interaction.response.send_message(f"Paused")


@tree.command(name="stop", description="Stops", guild=discord.Object(id=discord_guild))
async def stop(interaction: Interaction):
    if state.client is None or not state.client.is_playing():
        _=await interaction.response.send_message("Nothing playing")
        return

    state.client.stop()
    _ = await interaction.response.send_message("Stopped")


@client.event
async def on_message(message: discord.message.Message):
    if message.author == client.user:
        return


@client.event
async def on_ready():
    _ = await tree.sync(guild=discord.Object(id=discord_guild))
    print("Log : " + str(client.user))


if __name__ == "__main__":
    client.run(os.environ["DISCORD_TOKEN"])
