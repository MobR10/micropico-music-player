from machine import Pin, PWM
from time import sleep
import json
# --- Buzzer ---
pwm = PWM(Pin(0))
def tone(freq_hz, duty=1500):
    if freq_hz and freq_hz > 0:
        pwm.freq(int(freq_hz))
        pwm.duty_u16(duty)
    else:
        pwm.duty_u16(0)

def silence():
    pwm.duty_u16(0)

SONGS_DIR = "songs"   # your directory

# pick one file
filename = "bagatella fur elise"

with open(f"{filename}.json", "r") as f:
    data = json.load(f)

frequencies = data.get("frequencies")
durations = data.get("durations")

for freq, dur in zip(frequencies, durations):
    tone(freq)
    sleep(dur*0.9)
    silence()
    sleep(dur*0.1)