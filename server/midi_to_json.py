import mido
import json
import sys
import os

def midi_to_buzzer_json(midi_file_path, json_file_path, track_index=None):
    mid = mido.MidiFile(midi_file_path)

    # Default: pick the first track with at least one note_on
    if track_index is None:
        for i, t in enumerate(mid.tracks):
            if any(msg.type == 'note_on' for msg in t if not msg.is_meta):
                track_index = i
                break
        if track_index is None:
            raise ValueError("No track with notes found in this MIDI file.")

    if track_index < 0 or track_index >= len(mid.tracks):
        raise ValueError(f"Invalid track index {track_index}. This MIDI file has {len(mid.tracks)} tracks.")

    track = mid.tracks[track_index]
    frequencies = []
    durations = []

    tempo = 500000  # Default MIDI tempo (µs per beat)
    ticks_per_beat = mid.ticks_per_beat
    current_time = 0

    for msg in track:
        if msg.type == 'set_tempo':
            tempo = msg.tempo
        current_time += mido.tick2second(msg.time, ticks_per_beat, tempo)
        if not msg.is_meta and msg.type == 'note_on' and msg.velocity > 0:
            freq = 440 * 2 ** ((msg.note - 69) / 12)
            if round(current_time, 2) != 0:
                frequencies.append(int(freq))
                durations.append(round(current_time, 2))
            current_time = 0

    content = {
        "frequencies": frequencies,
        "durations": durations
    }

    with open(json_file_path, "w") as f:
        json.dump(content, f)

    print(f"JSON file created for track {track_index}: {json_file_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python midi_to_json.py <file.mid> [track_index]")
        sys.exit(1)

    # Always load from ./midi_songs/
    midi_name = sys.argv[1]
    midi_file = os.path.join("midi_songs", midi_name)

    if not os.path.exists(midi_file):
        print(f"Error: File {midi_file} not found.")
        sys.exit(1)

    # Parse optional track index
    track_index = int(sys.argv[2]) if len(sys.argv) > 2 else None

    # Auto-generate output filename in ./songs/
    base = os.path.splitext(os.path.basename(midi_name))[0]
    out_file = os.path.join("songs", base + ".json")

    # Ensure output dir exists
    os.makedirs("songs", exist_ok=True)

    midi_to_buzzer_json(midi_file, out_file, track_index)
