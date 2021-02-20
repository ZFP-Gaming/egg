import os
import discord

from os import path
from os import listdir
from dotenv import load_dotenv
from os.path import isfile, join
from discord.ext import commands

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
BOT_PREFIX = os.getenv('BOT_PREFIX')
SOUNDS_PATH = os.getenv('SOUNDS_PATH')

bot = commands.Bot(command_prefix=f'{BOT_PREFIX}')
bot.volume = 1.0

queue = []

def check_queue(voice_client):
    if queue != []:
        sound_effect = queue.pop(0)
        voice_client.play(discord.FFmpegPCMAudio(sound_effect), after=lambda x: check_queue(voice_client))
        voice_client.source = discord.PCMVolumeTransformer(voice_client.source)
        voice_client.source.volume = bot.volume

@bot.command(aliases = ['join'])
async def join_channel(ctx):
    try:
        channel = ctx.message.author.voice.channel
        await channel.connect()
    except Exception as e:
        print(e)
        print('Error al conectarse al canal de voz')

@bot.command()
async def leave(ctx):
    try:
        voice_client = ctx.guild.voice_client
        await voice_client.disconnect()
    except Exception as e:
        print(e)
        print('Error al desconectarse del canal de voz')

@bot.command()
async def stop(ctx):
    if ctx.author.voice and ctx.voice_client:
        vc = ctx.voice_client
        if vc.is_playing():
            queue = []
            vc.stop()

@bot.command(aliases=['s'])
async def sound(ctx, effect):
    sound_effect = f'{SOUNDS_PATH}/{effect}.mp3'
    try:
        if path.exists(sound_effect):
            voice_client = discord.utils.get(ctx.bot.voice_clients, guild=ctx.guild)
            if not voice_client:
                channel = ctx.message.author.voice.channel
                await channel.connect()
            if ctx.author.voice and ctx.voice_client:
                vc = ctx.voice_client
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

@bot.command(name='Lista de sonidos', aliases=['l'])
async def sound_list(ctx):
    sounds = '```Lista de sonidos disponibles:\n'
    files_path = f'{SOUNDS_PATH}/'
    files_directory = os.listdir(files_path)
    for file in sorted(files_directory):
        sounds += f'- {file.split(".")[0]}\n'
    sounds += '```'
    await ctx.send(sounds)

print('START')
bot.run(TOKEN)
