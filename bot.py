import discord
import responses
from discord.ext import tasks, commands
import feel_it
from transformers import pipeline
from feel_it import EmotionClassifier, SentimentClassifier
import requests
import rawgpy
import requests
import random
from typing import Optional
import datetime
import matplotlib.pyplot as plt
import numpy as np
from scipy.io import wavfile
from pydub import AudioSegment
import glob
import os
import pandas as pd
from scipy import signal
import math


def switch_on_bot():

    emotion_classifier = EmotionClassifier()
    token_bot = 'AAAAAAAA'

    intents = discord.Intents.default()
    intents.message_content = True

    client = commands.Bot(command_prefix='/', intents=intents)

    client.FLAG_USER_TO_PURSUIT = ''
    client.SYNTH_WAVE = 'sine'
    client.SYNTH_SMOOTH = False

    @client.event
    async def on_ready():
        print(f'{client.user} is now running')

    @client.event
    async def on_message(message):

        if client.user == message.author:
            return

        if str(message.author) == client.FLAG_USER_TO_PURSUIT:

            prediction = emotion_classifier.predict([message.content])
            print(prediction)

            if prediction[0] == 'anger':
                await message.add_reaction('😢')

        await send_message(message)

        await client.process_commands(message)

    @client.command()
    async def set_synth_wave(ctx, shape):
        if str(shape) != 'sine' and str(shape) != 'square' and str(shape) != 'triangle' and str(shape) != 'sawtooth' and str(shape) != 'chirp':
            await ctx.send('Funzione non prevista')
            return

        client.SYNTH_WAVE = shape

        await ctx.send(f"Synth settato con funzione d'onda {shape}")

    @client.command()
    async def set_synth_smooth(ctx, smooth_flag):
        if str(smooth_flag) != 'on' and str(smooth_flag) != 'off':
            await ctx.send('Funzione non prevista')
            return

        client.SYNTH_SMOOTH = True if smooth_flag == 'on' else False

        await ctx.send(f"Smoothing impostato a {smooth_flag}")

    @client.command()
    async def play_synth(ctx, *args):

        if len(args) > 50:
            await ctx.send('Troppe note scusa')
            return

        df_notes = pd.read_csv('notes.csv')

        note_list = []
        sampleRate = 44100

        amplitude = 0.4  # ampiezza dell'onda default

        for arg in args:
            note = arg
            note_list.append(arg)

        try:
            freq_list = []
            for note in note_list:
                if note.__contains__('('):
                    frequency = df_notes.loc[df_notes['note']
                                             == note.split('(')[0]]['frequency'].values[0]

                    try:
                        # Per ora 1 secondo
                        duration = note.split('(')[1].strip(')')

                        if client.SYNTH_SMOOTH == True and frequency != 0:
                            n_cycles = math.floor(frequency*float(duration))
                            print(n_cycles)

                            duration = n_cycles/frequency

                        frames = sampleRate * float(duration)
                        print(int(frames))

                        linspace = np.linspace(0, float(duration), int(frames))

                        freq_list.append(
                            [frequency, duration, linspace])

                    except Exception as e:
                        print(e)
                        await ctx.send('La durata deve essere un numero')
                        return

                else:
                    frequency = df_notes.loc[df_notes['note']
                                             == note]['frequency'].values[0]
                    frames = sampleRate * 1  # Per ora 1 secondo
                    freq_list.append([frequency, 1, np.linspace(0, 1, frames)])

        except Exception as e:
            await ctx.send('Nota non trovata.')
            return

        # Dato samplerate fissato e frequenza, creiamo la nota usando la funzione seno (2pifx). Avremo bisogno di uno spazio lineare e di un frame.
        # Il frame contiene durata*samplerate in quanto in un secondo abbiamo 44100 samples. in durata secondi ne abbiamo durata*samplerate.
        # Il linspace parte da 0, arriva a 1 e spazia linearmente tutti i frames. In questo caso stiamo spaziando i nostri samples.

        note_array_list = np.empty((0))
        for frequency_record in freq_list:
            if client.SYNTH_WAVE == 'sine':
                note_array = amplitude * \
                    np.cos(2*np.pi*frequency_record[0]*frequency_record[2])

            elif client.SYNTH_WAVE == 'square':
                note_array = amplitude * \
                    np.heaviside(
                        np.sin(2*np.pi*frequency_record[0]*frequency_record[2]), 1.0)

            elif client.SYNTH_WAVE == 'triangle':
                note_array = amplitude * \
                    signal.sawtooth(
                        2*np.pi*frequency_record[0]*frequency_record[2], 0.5)

            elif client.SYNTH_WAVE == 'sawtooth':
                note_array = amplitude * \
                    signal.sawtooth(
                        2*np.pi*frequency_record[0]*frequency_record[2], 1.0)

            elif client.SYNTH_WAVE == 'chirp':
                note_array = amplitude * \
                    signal.chirp(
                        frequency_record[2], frequency_record[0], float(duration)/2, frequency_record[0]*1.059463094359)

            note_array_list = np.append(note_array_list, note_array, axis=0)

        note_sound = np.asarray(
            [32767*note_array_list, 32767*note_array_list]).T.astype(np.int16)  # 32767 è usato poichè il file è formato da interi a 16 bit  e lo stiamo denormalizzando (altrimenti sarenne compreso tra -1 ed 1)

        wavfile.write(f'{ctx.author}_output.wav', 44100, note_sound)

        await ctx.send(file=discord.File(f"{ctx.author}_output.wav"))

        os.remove(f"{ctx.author}_output.wav")

    if False:
        @client.command()
        async def plotter(ctx, function):

            def f(x):
                f = compiler.parse(function)
                return f

            x = np.linspace(-5, 5, 1000)
            y = f(x)

            plt.plot(x, y)
            plt.savefig('plot.png')

            await ctx.send(file=discord.File('plot.png'))

            os.remove('plot.png')

    @client.command()
    async def mock_tilting(ctx, username):

        client.FLAG_USER_TO_PURSUIT = username
        await ctx.send(f"L'utente {username} sente i suoi peccati arrampicarsi sulla schiena")

    @client.command()
    async def stop_tilting(ctx):

        old_user = client.FLAG_USER_TO_PURSUIT
        client.FLAG_USER_TO_PURSUIT = ''
        await ctx.send(f"L'utente {old_user} si sente più leggero")

    @client.command()
    async def library_roulette(ctx, username):

        steam_api_key = 'AAAAAAAAAAAA'

        url = f'http://api.steampowered.com/ISteamUser/ResolveVanityURL/v0001/?key={steam_api_key}&vanityurl={username}'

        response = requests.get(url).json()

        try:
            steam_id = response['response']['steamid']
        except Exception as e:
            await ctx.send(f"Errore: utente non esistente o altro errore strano.")

        url = f'http://api.steampowered.com/IPlayerService/GetOwnedGames/v1/?key={steam_api_key}&steamid={steam_id}'

        response = requests.get(url + '').json()

        app_id_list = []

        for game in response['response']['games']:
            app_id_list.append(game['appid'])

        chosen_game = random.choice(app_id_list)

        url = f"http://store.steampowered.com/api/appdetails?key={steam_api_key}&appids={str(chosen_game)}"
        response = requests.get(url).json()

        chosen_name = response[str(chosen_game)]['data']['name']
        chosen_link = f'https://store.steampowered.com/app/{chosen_game}'

        await ctx.send(f"Il gioco scelto dalla tua libreria è {chosen_name}\n{chosen_link}")

    @client.command()
    async def game_roulette(ctx, store: Optional[str]):

        chosen_link = ''
        chosen_page = random.randint(0, 500)
        chosen_element = random.randint(0, 19)

        url = "https://api.rawg.io/api/games?key="
        rawg_api_key = 'AAAAAAAAAAAAAAAA'

        if store is not None:

            if store.lower() == 'steam':

                response = requests.get(
                    url + f"&page={chosen_page}&stores=1").json()
                chosen_slug = response['results'][chosen_element]['slug']

                response2 = requests.get(
                    f"https://api.rawg.io/api/games/{chosen_slug}/stores?key={rawg_api_key}").json()

                for result in response2['results']:
                    if result['store_id'] == 1:
                        chosen_link = result['url']
                        break

            if store != 'steam':
                await ctx.send(f"E che negozio è?")
                return
        else:
            # A GET request to the API
            response = requests.get(url + f"&page={chosen_page}").json()

        chosen_game = response['results'][chosen_element]['name']
        chosen_image = response['results'][chosen_element]['background_image']

        if chosen_link == '':
            await ctx.send(f"Il gioco scelto è {chosen_game}\n{chosen_image}")
        else:
            await ctx.send(f"Il gioco scelto è {chosen_game}\n{chosen_link}")

    @client.command()
    async def kannahashimoto(ctx):

        await ctx.send('https://tenor.com/view/kanna-hashimoto-gif-20245292')

    client.run(token_bot)


async def send_message(message):
    try:
        response = responses.handle_response(message.content)

        if response != '':
            await message.channel.send(response)
        else:
            return
    except Exception as e:
        print(e)
