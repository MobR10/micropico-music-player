from flask import Flask, request, jsonify
import os
import json

app = Flask(__name__)

SONGS_DIR = "songs"

# Global state
current_song_name = None
current_song_data = None
current_action = None
current_volume = None

@app.route("/set", methods=["GET"])
def set_value():
    global current_song_name, current_song_data, current_action, current_volume

    song_name = request.args.get("song")
    action = request.args.get("action")
    volume = request.args.get("volume")

    if song_name:
        filename = f"{song_name}.json"
        filepath = os.path.join(SONGS_DIR, filename)

        if not os.path.exists(filepath):
            return jsonify({"error": f"Song '{song_name}' not found"}), 404

        with open(filepath, "r") as f:
            current_song_data = json.load(f)
        current_song_name = song_name
        print(f"Current song set to: {song_name}")
        return jsonify({"status": "ok", "song": song_name})

    elif action:
        current_action = action
        print(f"Current action set to: {action}")
        return jsonify({"status": "ok", "action": action})

    elif volume:
        current_volume=int(volume)
        print(f"Volume set to: {current_volume}")
        return jsonify({"Status": "ok", "volume": current_volume})
    
    else:
        return jsonify({"error": "Missing 'song' or 'action' parameter"}), 400


@app.route("/get", methods=["GET"])
def get_value():
    global current_action, current_song_name, current_song_data, current_volume
    
    param = request.args.get("song")
    if param is not None:  # /get?song
        if current_song_data is None:
            return jsonify({"error": "No song selected"}), 404
        response = {
            "song": current_song_name,
            **current_song_data
        }
        return jsonify(response)

    param = request.args.get("action")
    if param is not None:  # /get?action
        action_to_return = current_action
        current_action = None  # reset after reading
        return jsonify({"action": action_to_return})
    
    param = request.args.get("list")
    if param is not None: # /get?list
        try:
            files = os.listdir(SONGS_DIR)
            # optionally, filter only .json
            songs = [f[:-5] for f in files if f.endswith(".json")]
            return jsonify({"songs": songs})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    param = request.args.get("volume")
    if param is not None: # /get?volume
        print(current_volume)
        return jsonify({"volume": current_volume})

    return jsonify({"error": "Invalid query"}), 400


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
