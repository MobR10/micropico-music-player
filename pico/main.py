from machine import Pin, PWM
import uasyncio as asyncio
import network
import urequests
import json
import time

# --- Wi-Fi ---
SSID = "IPW-Users-2025"
PASSWORD = "ipwusers"

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(SSID, PASSWORD)
while not wlan.isconnected():
    time.sleep_ms(500)
print("Connected:", wlan.ifconfig())

# --- Buzzer ---
buzzer = PWM(Pin(0))
volume = 1500  # default volume

def tone(freq_hz):
    buzzer.freq(int(freq_hz))
    buzzer.duty_u16(volume)

def silence():
    buzzer.duty_u16(0)

# --- Server ---
SERVER_IP = "172.20.20.42"
SERVER_URL_SONG = f"http://{SERVER_IP}/get?song"
SERVER_URL_ACTION = f"http://{SERVER_IP}/get?action"
SERVER_URL_VOLUME = f"http://{SERVER_IP}/get?volume"

# --- Playback state ---
current_song = None
current_song_fingerprint = None
index = 0
playing = False
paused = True

# --- Helpers ---
def fingerprint(song_dict):
    return json.dumps(song_dict)

def safe_get(url):
    try:
        r = urequests.get(url, timeout=2)
        if r.status_code == 200:
            data = r.json()
        else:
            data = None
        r.close()
        return data
    except Exception as e:
        print(f"safe_get error for {url}: {e}")
        return None

# --- Playback functions ---
async def load_song():
    global current_song, current_song_fingerprint, index
    data = safe_get(SERVER_URL_SONG)
    if not data:
        return
    new_song = {
        "frequencies": data.get("frequencies", []),
        "durations": data.get("durations", [])
    }
    new_fp = fingerprint(new_song)
    if new_fp != current_song_fingerprint:
        current_song = new_song
        current_song_fingerprint = new_fp
        index = 0

def play_song():
    global playing, paused
    if current_song:
        playing = True
        paused = False

def pause_song():
    global playing, paused
    playing = False
    paused = True
    silence()

def repeat_song():
    global index
    index = 0

def stop_song():
    global playing, paused, index
    playing = False
    paused = True
    index = 0
    silence()

# --- Async tasks ---
async def poll_server_actions():
    global playing, paused
    while True:
        data = safe_get(SERVER_URL_ACTION)
        if data:
            action = data.get("action")
            if action == "play":
                await load_song()
                play_song()
            elif action == "pause":
                pause_song()
            elif action == "repeat":
                repeat_song()
                play_song()
        await asyncio.sleep_ms(500)

async def poll_server_volume():
    global volume
    while True:
        data = safe_get(SERVER_URL_VOLUME)
        if data:
            v = data.get("volume")
            if v is not None:
                try:
                    volume = max(0, min(65535, int(float(v))))
                except:
                    pass
        await asyncio.sleep_ms(500)

async def playback_loop():
    global index, playing, paused
    while True:
        if playing and not paused and current_song:
            freq = current_song["frequencies"][index]
            dur = current_song["durations"][index]  # in seconds

            if freq > 0:
                tone(freq)
            else:
                silence()

            # --- accurate sleep using absolute ticks ---
            start = time.ticks_ms()
            end = start + int(dur * 1000)
            while time.ticks_ms() < end:
                if paused or not playing:
                    silence()
                    break
                await asyncio.sleep_ms(5)

            silence()
            index += 1
            if index >= len(current_song["frequencies"]):
                # end of song
                playing = False
                paused = True
                index = 0
                silence()
        else:
            await asyncio.sleep_ms(50)

# --- Main ---
async def main():
    await load_song()  # load initial song
    await asyncio.gather(
        poll_server_actions(),
        poll_server_volume(),
        playback_loop()
    )

asyncio.run(main())
