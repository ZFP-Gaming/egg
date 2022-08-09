import os
import glob
import discord

from os import path
from os import listdir
from dotenv import load_dotenv
from os.path import isfile, join

from pymongo import MongoClient
from discord.ext import commands
from discord_slash import SlashCommand, SlashContext
from discord_slash.utils.manage_commands import create_option

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
BOT_PREFIX = os.getenv('BOT_PREFIX')
SOUNDS_PATH = os.getenv('SOUNDS_PATH')
MONGO_URL = os.getenv('MONGO_URL')

db = MongoClient(MONGO_URL)
intros = db.bot.intros

bot = commands.Bot(command_prefix=f'{BOT_PREFIX}', intents=discord.Intents.all())
bot.volume = 0.6
slash = SlashCommand(bot, sync_commands=True)

guild_ids = [134687470733230080]
queue = []

def check_queue(voice_client):
    if queue != []:
        sound_effect = queue.pop(0)
        voice_client.play(discord.FFmpegPCMAudio(sound_effect), after=lambda x: check_queue(voice_client))
        voice_client.source = discord.PCMVolumeTransformer(voice_client.source)
        voice_client.source.volume = bot.volume

@slash.slash(
    name="join",
    options=[],
    description="Unirse a un canal de voz")
@bot.command()
async def join_channel(ctx: SlashContext):
    await ctx.send(hidden=True, content="✅")
    try:
        channel = ctx.author.voice.channel
        await channel.connect()
    except Exception as e:
        print(e)
        print('Error al conectarse al canal de voz')

@slash.slash(
    name="leave",
    options=[],
    description="Irse de un canal de voz")
@bot.command()
async def leave(ctx: SlashContext):
    await ctx.send(hidden=True, content="✅")
    try:
        voice_client = discord.utils.get(ctx.bot.voice_clients, guild=ctx.guild)
        await voice_client.disconnect()
    except Exception as e:
        print(e)
        print('Error al desconectarse del canal de voz')

@slash.slash(
    name="stop",
    options=[],
    description="Finalizar la reproducción")
@bot.command()
async def stop(ctx: SlashContext):
    await ctx.send(hidden=True, content="✅")
    if ctx.author.voice:
        vc = discord.utils.get(ctx.bot.voice_clients, guild=ctx.guild)
        if vc.is_playing():
            queue = []
            vc.stop()

@slash.slash(
    name="s",
    description="Reproducir efecto de sonido",
    options=[
        create_option(
            name="sound_effect",
            description="Nombre del sonido",
            option_type=3,
            required=True
        )
    ])

@bot.event
async def on_voice_state_update(member, before, after):
    try:
        voice_client = discord.utils.get(bot.voice_clients, guild=member.guild)
        if before.channel is None and after.channel is not None and member.bot == False:
            if voice_client and voice_client.channel == after.channel:
                id = member.id
                data = intros.find_one({'id': id})
                sound_effect = f'{SOUNDS_PATH}/{data["effect"]}.mp3'
                if data and data['effect'] != '' and path.exists(sound_effect):
                    voice_client.play(discord.FFmpegPCMAudio(sound_effect))
                    voice_client.source = discord.PCMVolumeTransformer(voice_client.source)
                    voice_client.source.volume = bot.volume
                else:
                    print(f'{member.name} no tiene un sonido registrado')
        if voice_client and voice_client.channel == before.channel:
            connected_users = voice_client.channel.members
            if len(connected_users) == 1 and connected_users[0].bot:
                print('Voice channel empty, leaving...')
                await voice_client.disconnect()
    except Exception as e:
        print(e)

@bot.command(aliases=['s'])
async def sound(ctx: SlashContext, sound_effect: str):
    await ctx.send(hidden=True, content="✅")
    sound_effect = list(glob.glob(f'{SOUNDS_PATH}/{sound_effect}*.mp3'))[0]
    try:
        if path.exists(sound_effect):
            voice_client = discord.utils.get(ctx.bot.voice_clients, guild=ctx.guild)
            if not voice_client:
                channel = ctx.author.voice.channel
                await channel.connect()
            if ctx.author.voice:
                vc = discord.utils.get(ctx.bot.voice_clients, guild=ctx.guild)
                if not vc.is_playing():
                    print('Empty queue, playing...')
                    vc.play(discord.FFmpegPCMAudio(sound_effect), after=lambda x: check_queue(vc))
                    vc.source = discord.PCMVolumeTransformer(vc.source)
                    vc.source.volume = bot.volume
                else:
                    print(f'Added to queue: {sound_effect}')
                    queue.append(sound_effect)
            else:
                await ctx.send('No estás conectado a un canal de audio')
        else:
            await ctx.send('No tengo ese sonido, peticiones en https://github.com/ZFP-Gaming/huevito-rey/issues')
    except Exception as e:
        print(e)

@slash.slash(
    name="list",
    options=[],
    description="Listar sonidos disponibles")
@bot.command(name='sonidos', aliases=['l'])
async def sound_list(ctx: SlashContext):
    files_path = f'{SOUNDS_PATH}/'
    files_directory = os.listdir(files_path)

    files = sorted(files_directory)
    page_size = 20

    pages = [files[i: i + page_size] for i in range(0, len(files), page_size)]
    paginated_content = []

    for page in pages:
        embed = discord.Embed()
        sounds_list = '```\n'
        for file in page:
            sounds_list += f'- {file.split(".")[0]}\n'
        sounds_list += '```'
        embed.add_field(name='🔈 Lista de sonidos disponibles', value=sounds_list, inline=False)
        paginated_content.append(embed)

    buttons = [u"\u23EA", u"\u2B05", u"\u27A1", u"\u23E9"]
    current = 0
    msg = await ctx.send(embed=paginated_content[current])

    for button in buttons:
        await msg.add_reaction(button)

    while True:
        try:
            reaction, user = await bot.wait_for("reaction_add", check=lambda reaction, user: user == ctx.author and reaction.emoji in buttons, timeout=60.0)

        except Exception as e:
            return print(e)

        else:
            previous_page = current
            if reaction.emoji == u"\u23EA":
                current = 0

            elif reaction.emoji == u"\u2B05":
                if current > 0:
                    current -= 1

            elif reaction.emoji == u"\u27A1":
                if current < len(paginated_content)-1:
                    current += 1

            elif reaction.emoji == u"\u23E9":
                current = len(paginated_content)-1

            for button in buttons:
                await msg.remove_reaction(button, ctx.author)

            if current != previous_page:
                await msg.edit(embed=paginated_content[current])

@slash.slash(
    name="volume",
    description="Cambiar el volumen",
    options=[
        create_option(
            name="amount",
            description="Número entre 1 y 100",
            option_type=4,
            required=True
        )
    ])
@bot.command()
async def volume(ctx: SlashContext, amount: int):
    try:
        bot.volume = int(amount)/100
        await ctx.send(f'El volumen actual es {amount}%')
    except Exception as e:
        print(e)
        await ctx.send('')

print('START')
bot.run(TOKEN)
