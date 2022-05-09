import asyncio
import discord
from discord.ext import commands, tasks
from discord.voice_client import VoiceClient
import youtube_dl
import TOKEN as TOKEN_API

from random import choice

youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

def is_connected(ctx):
    voice_client = ctx.message.guild.voice_client
    return voice_client and voice_client.is_connected()




client = commands.Bot(command_prefix='!')

status = ["--!help--","--!help--"]
queue = []
loop = False


@client.event
async def on_ready():
	change_status.start()
	print("Bot is online!")

@client.event
async def on_member_join(member):
    channel = discord.utils.get(member.guild.channels, name='general')
    await channel.send(f'Welcome {member.mention}!  Ready to jam out? See `!help` command for details!')

@client.command(name= "ping" , help= "This command return's the latency")
async def ping(ctx):
	await ctx.send(f"**Pong!** Latency: {round(client.latency * 1000)}ms")

@client.command(name= "hello", help= "This command returns the welcome message")
async def hello(ctx):
	responses = ["Hii", "Leave me alone", "Why are you bothering me?", "Hello there!"]
	await ctx.send(choice(responses))


@client.command(name='join', help='This command makes the bot join the voice channel')
async def join(ctx):
    if not ctx.message.author.voice:
        await ctx.send("You are not connected to a voice channel")
        return
    
    else:
        channel = ctx.message.author.voice.channel

    await channel.connect()

@client.command(name='queue', help='This command adds a song to the queue')
async def queue_(ctx, url):
    global queue

    queue.append(url)
    await ctx.send(f'`{url}` added to queue!')

@client.command(name="remove", help= "This command removes a song from queue")
async def remove(ctx, number):
	global queue 

	try:
		del(queue[int (number)])
		await ctx.send(f"Your queue is now ‛{queue}!‛")

	except:
		await ctx.send("Your queue is either **empty** or the index **is out of range**")

@client.command(name="loop", help="This command toggle loop")
async def loop(ctx):
	global loop

	if loop:
		await ctx.send('Loop mode is‛False‛')
		loop = False

	else:
		await ctx.send('Loop mode is‛True‛')
		loop = True

@client.command(name='play', help='This command plays music')
async def play(ctx):
    global queue

    if not ctx.message.author.voice:
        await ctx.send("You are not connected to a voice channel")
        return
    
    else:
        channel = ctx.message.author.voice.channel

    try: await channel.connect()
    except: pass

    server = ctx.message.guild
    voice_channel = server.voice_client
    
    try:
        async with ctx.typing():
            player = await YTDLSource.from_url(queue[0], loop=client.loop)
            voice_channel.play(player, after=lambda e: print('Player error: %s' % e) if e else None)
            
            if loop:
                queue.append(queue[0])

            del(queue[0])
            
        await ctx.send('**Now playing:** {}'.format(player.title))

    except:
        await ctx.send('Nothing in your queue! Use `?queue` to add a song!')

@client.command(name='pause', help='This command pauses the song')
async def pause(ctx):
    server = ctx.message.guild

    voice_channel = server.voice_client

    voice_channel.pause()

@client.command(name='resume', help='This command resumes the song!')
async def resume(ctx):
    server = ctx.message.guild

    voice_channel = server.voice_client

    voice_channel.resume()

@client.command(name= "view" , help= "This command displays the queue list")
async def view(ctx):
	await ctx.send(f"Your queue is now ‛{queue}!‛")

@client.command(name='leave', help='This command stops the music and makes the bot leave the voice channel')
async def leave(ctx):
    voice_client = ctx.message.guild.voice_client
    await voice_client.disconnect()

@client.command(name='stop', help='This command stops the song!')
async def stop(ctx):
    server = ctx.message.guild
    voice_channel = server.voice_client

    voice_channel.stop()

@tasks.loop(hours=12)
async def change_status():
	await client.change_presence(activity=discord.Game(choice(status)))

client.run('import your token here')