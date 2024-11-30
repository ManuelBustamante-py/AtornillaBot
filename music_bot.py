import discord
from discord.ext import commands
import yt_dlp as youtube_dl
import asyncio
from collections import deque
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# Configuración del bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Configuración de yt-dlp y FFmpeg
FFMPEG_OPTIONS = {
    'options': '-vn -filter:a "volume=1.0"'  # Volumen por defecto al 100%
}

YDL_OPTIONS = {
    'format': 'bestaudio/best',  # Mejor calidad de audio disponible
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',  # Calidad de 192kbps
    }],
    'quiet': True,  # Silenciar la salida de yt-dlp
}

# Cola para almacenar las canciones
queue = deque()
is_playing = False  # Variable para saber si ya estamos reproduciendo música
is_looping = False  # Variable para saber si el bucle está activado
current_song = None  # Variable para almacenar la canción que se está reproduciendo actualmente

# Volumen por defecto
current_volume = 1.0  # Valor inicial del volumen (1.0 es el 100%)
current_speed = 1.0  # Velocidad de la canción por defecto (1.0 es velocidad normal)

# Comando para reproducir música
async def play_next(ctx):
    global is_playing, current_song, is_looping
    if is_looping and current_song:
        # Si el bucle está activado, reproducimos la misma canción
        await play(ctx, current_song)
    elif queue:
        song_url = queue.popleft()  # Sacamos la siguiente canción de la cola
        await play(ctx, song_url)
    else:
        is_playing = False  # Si no hay canciones en la cola, marcamos que no estamos reproduciendo

@bot.command(name="play")
async def play(ctx, url: str):
    global is_playing, current_song
    try:
        voice_channel = ctx.author.voice.channel
        if not voice_channel:
            await ctx.send("¡Debes estar en un canal de voz para usar este comando!")
            return

        # Conectarse al canal de voz si no está conectado
        voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
        if not voice_client:
            voice_client = await voice_channel.connect()
        elif voice_client.is_playing():
            await ctx.send("⚠️ Ya se está reproduciendo música. Se añadirá a la cola.")
            queue.append(url)  # Añadimos la canción a la cola
            return

        # Descargar la información del audio usando yt-dlp
        with youtube_dl.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(url, download=False)
            # Filtrar formatos de audio válidos (que no sean 'none' en acodec)
            audio_formats = [f for f in info['formats'] if f.get('acodec') != 'none']
            
            if not audio_formats:
                await ctx.send("❌ No se encontró un formato de audio válido para reproducir.")
                return

            # Obtener el primer formato válido
            audio_url = audio_formats[0]['url']
            title = info.get('title', 'Audio desconocido')

        # Reproducir el audio con el filtro de velocidad
        voice_client.play(discord.FFmpegPCMAudio(audio_url, **FFMPEG_OPTIONS), after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop))
        is_playing = True
        current_song = url  # Guardamos la canción que se está reproduciendo actualmente
        await ctx.send(f"🎶 Reproduciendo: **{title}**")

    except AttributeError:
        await ctx.send("¡Debes estar conectado a un canal de voz para usar este comando!")
    except Exception as e:
        await ctx.send(f"❌ Ocurrió un error al intentar reproducir música: {str(e)}")

# Comando para activar/desactivar el bucle
@bot.command(name="loop")
async def loop(ctx):
    global is_looping
    if is_looping:
        is_looping = False
        await ctx.send("🔁 El bucle de la canción ha sido desactivado.")
    else:
        is_looping = True
        await ctx.send("🔁 El bucle de la canción ha sido activado.")

# Comando para detener la música y desconectar el bot
@bot.command(name="stop")
async def stop(ctx):
    global is_playing
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_client and voice_client.is_connected():
        voice_client.stop()  # Detenemos la música
        await voice_client.disconnect()
        is_playing = False
        await ctx.send("🎵 andate a la chucha embarao conchetumadre, nos vimos giles culiaos.")
    else:
        await ctx.send("¡El bot no está conectado a un canal de voz!")

# Comando para ver la cola de canciones
@bot.command(name="q")
async def queue_list(ctx):
    if not queue:
        await ctx.send("❌ La cola está vacía.")
    else:
        queue_message = "🎶 **Cola de Canciones:**\n"
        for idx, url in enumerate(queue, 1):
            queue_message += f"{idx}. {url}\n"
        await ctx.send(queue_message)

# Comando para reproducir la canción 'Atornillame' con el nombre !Atornillame
@bot.command(name="Atornillame")
async def atornillame(ctx):
    song_url = "https://www.youtube.com/watch?v=H7xGr31fU5U"  # URL de la canción específica
    await play(ctx, song_url)  # Llamamos al comando de reproducción con esta URL

# Comando para unirse a un canal de voz
@bot.command(name="join")
async def join(ctx):
    try:
        voice_channel = ctx.author.voice.channel
        if not voice_channel:
            await ctx.send("¡Debes estar en un canal de voz para usar este comando!")
            return
        
        # Conectar al canal de voz
        voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
        if not voice_client:
            await voice_channel.connect()
            await ctx.send(f"✅ wena atornillados culiaos, una vez más acá en: {voice_channel.name}")
        else:
            await ctx.send("El bot ya está conectado a un canal de voz.")
    except Exception as e:
        await ctx.send(f"❌ Ocurrió un error al intentar unirme al canal: {str(e)}")

# Comando para saltar la canción y pasar a la siguiente
@bot.command(name="skib")
async def skip(ctx):
    global is_playing
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    
    if not voice_client:
        await ctx.send("❌ El bot no está conectado a un canal de voz.")
        return

    if voice_client.is_playing():
        voice_client.stop()  # Detenemos la canción actual
        await ctx.send("⏭️ Se saltó la canción.")
        
        # Reproducir la siguiente canción si hay una en la cola
        await play_next(ctx)
    else:
        await ctx.send("❌ No se está reproduciendo música en este momento.")

# Comando para ajustar el volumen
@bot.command(name="volumen")
async def volumen(ctx, percentage: int):
    global current_volume, FFMPEG_OPTIONS
    if 0 <= percentage <= 300:  # Permitimos valores entre 0 y 300
        # Convertir el porcentaje a un valor de multiplicación (100% -> 1.0, 50% -> 0.5, etc.)
        current_volume = percentage / 100
        FFMPEG_OPTIONS = {
            'options': f'-vn -filter:a "volume={current_volume}"'
        }
        await ctx.send(f"🔊 El volumen se ha ajustado al {percentage}%")
    else:
        await ctx.send("❌ El valor debe estar entre 0 y 300.")

# Comando para ajustar la velocidad de la canción
@bot.command(name="velocidad")
async def velocidad(ctx, speed: float):
    global current_speed, FFMPEG_OPTIONS
    if 0.5 <= speed <= 2.0:  # Permitimos valores entre 0.5x y 2x
        current_speed = speed
        FFMPEG_OPTIONS = {
            'options': f'-vn -filter:a "atempo={current_speed},volume={current_volume}"'
        }
        await ctx.send(f"⚡ La velocidad de la canción se ha ajustado a {current_speed}x")
    else:
        await ctx.send("❌ La velocidad debe estar entre 0.5x y 2x.")

# Evento de inicio
@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user}")

# Evento para detectar "Hola" en el chat
@bot.event
async def on_message(message):
    if "Quien-Nos-Cagó?" in message.content:
        await message.channel.send("Fue el @syltharis_ ")
    await bot.process_commands(message)  # Procesamos comandos además de los eventos

# Ejecutamos el bot
bot.run('MTMxMjIzODk2OTkyNDM1ODE0NQ.GN3j1k.zjjFHUcbNQz_nunUmc_Ld2jAgcOqM758JiK1Is')  # Sustituye 'YOUR_BOT_TOKEN' con el token de tu bot
