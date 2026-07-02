import os
import threading
import time
from flask import Flask, jsonify, request
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Windows Audio Control Libraries / Windows Ses Kontrol Kütüphaneleri
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

# ── SPOTIFY API CREDENTIALS / SPOTIFY UYGULAMA BİLGİLERİ ──────────────────
# Replace these placeholders with your own Spotify Developer Dashboard credentials
# Bu alanları kendi Spotify Developer Dashboard bilgilerinizle doldurun
CLIENT_ID = "YOUR_SPOTIFY_CLIENT_ID"
CLIENT_SECRET = "YOUR_SPOTIFY_CLIENT_SECRET"
REDIRECT_URI = "http://127.0.0.1:8888/callback"

SCOPE = "user-read-playback-state user-read-currently-playing"

app = Flask(__name__)

# Initialize Spotipy / Spotipy Bağlantısını Başlatma
sp = spotipy.Spotify(
    auth_manager=SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE,
        cache_path=".spotify_cache",
    )
)

# Thread-safe global cache / İş parçacığı güvenli global önbellek
_lock = threading.Lock()
_cached = {
    "track": "---",
    "artist": "---",
    "album": "---",
    "progress": 0,
    "duration": 1,
    "is_playing": False,
    "track_id": None,
}


def set_pc_volume(volume_percentage):
    """
    Changes Windows Master Volume using Pycaw.
    Windows Ana Ses Seviyesini Pycaw kullanarak değiştirir.
    """
    try:
        import comtypes
        # Initialize COM library for the current Flask worker thread
        # Flask iş parçacığı (thread) için COM kütüphanesini başlatıyoruz
        comtypes.CoInitialize()

        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(
            IAudioEndpointVolume._iid_, CLSCTX_ALL, None
        )
        volume = interface.QueryInterface(IAudioEndpointVolume)

        # Map 0-100 to skaler 0.0-1.0 / Yüzdeyi 0.0 - 1.0 arasına eşitleme
        val = max(0.0, min(1.0, volume_percentage / 100.0))
        volume.SetMasterVolumeLevelScalar(val, None)

        # Uninitialize COM after task / İşlem bittiğinde kapatma
        comtypes.CoUninitialize()
    except Exception as e:
        print(f"[Volume Error] Details: {e}")


def _fetch_loop():
    """
    Background thread to poll Spotify API continuously.
    Spotify API'den verileri sürekli çeken arka plan döngüsü.
    """
    while True:
        try:
            pb = sp.current_playback()
            if pb and pb.get("item"):
                item = pb["item"]
                with _lock:
                    _cached.update(
                        {
                            "track": item["name"],
                            "artist": ", ".join(
                                a["name"] for a in item["artists"]
                            ),
                            "album": item["album"]["name"],
                            "progress": pb.get("progress_ms", 0),
                            "duration": item.get("duration_ms", 1),
                            "is_playing": pb.get("is_playing", False),
                            "track_id": item["id"],
                        }
                    )
            else:
                with _lock:
                    _cached["is_playing"] = False
        except Exception as e:
            print(f"[FetchLoop] Error: {e}")
        time.sleep(3)  # Fetch every 3 seconds / 3 saniyede bir güncelle


@app.route("/now-playing")
def now_playing():
    """Endpoint for ESP32 to fetch current Spotify state."""
    with _lock:
        data = dict(_cached)
    return jsonify(data)


@app.route("/set-volume", methods=["GET"])
def set_volume():
    """Endpoint for ESP32 to push hardware volume level."""
    vol = request.args.get("vol", type=int)
    if vol is not None and 0 <= vol <= 100:
        print(f"[Flask API] Volume requested from ESP32: %{vol}")
        set_pc_volume(vol)
        return jsonify({"status": "success", "volume": vol})
    return jsonify({"status": "error", "message": "Invalid value"}), 400


if __name__ == "__main__":
    # Start background Spotify listener / Arka plan dinleyicisini başlatma
    t = threading.Thread(target=_fetch_loop, daemon=True)
    t.start()
   print(" ╔═══════════════════════════════════╗")
    print("║  Spotify Bridge Çalışıyor         ║")
    print("║  If you have a questiıon          ║")
    print("║  Just Write                       ║")
    print("║  Enjoy Listening                  ║")
    print("║  Coder:Curly                      ║")
    print("║  http://0.0.0.0:5000/now-playing  ║")
    print("╚═══════════════════════════════════╝")
    app.run(host="0.0.0.0", port=5000, debug=False) 
