"""

             S P O T I F Y  →  E S P 3 2   B R İ D G E                  
                    Python Flask Köprü Sunucusu                                
               Çalıştır: python spotify_bridge.py                              
    İlk çalıştırmada tarayıcı açılır, Spotify hesabını onayla.    
      Sonraki çalıştırmalarda .cache dosyası token'ı saklar.         

Gereksinimler:
    Spotify Premium Hesabı (Ücretsiz hesaplar için geçerli değildir)
    Python 3.7+ (https://www.python.org/downloads/)
    pip install flask spotipy
    daha sonra indirmenin ardından 
    pip install --upgrade pip

Spotify Developer Console'dan (developer.spotify.com/dashboard):
    1. Yeni uygulama oluştur
    2. Redirect URI olarak ekle: http://127.0.0.1:8888/callback
    (localhost spotify tarafından güvensiz olarak kabul edilir bu sebeple 127.0.0.1 kullanıyoruz)
    3. CLIENT_ID ve CLIENT_SECRET'ı aşağıya gir
"""

 
import time
import threading
from flask import Flask, jsonify
import spotipy
from spotipy.oauth2 import SpotifyOAuth
 
# ── Spotify Uygulama Bilgileri ───────────────────────────────────
CLIENT_ID     = "Buraya Spotify Client ID'nizi girin"
CLIENT_SECRET = "Buraya Spotify Client Secret'inizi girin" 
""" Kodunuzu paylaşmayın, gizli tutun! """
""" WEB API için spotify premium hesabı gereklidir. (Ücretsiz hesaplar için geçerli değildir.) """
REDIRECT_URI  = "http://127.0.0.1:8888/callback"
 
SCOPE = (
    "user-read-playback-state "
    "user-read-currently-playing"
)
 
# ── Flask & Spotipy 
app = Flask(__name__)
 
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope=SCOPE,
    cache_path=".spotify_cache"
))
 
# ── Paylaşılan veri (arka planda güncellenir) 
_lock = threading.Lock()
_cached = {
    "track":      "---",
    "artist":     "---",
    "album":      "---",
    "progress":   0,
    "duration":   1,
    "is_playing": False,
    "track_id":   None
}
 
def _fetch_loop():
    """Arka planda 3 saniyede bir Spotify'ı sorgular."""
    while True:
        try:
            pb = sp.current_playback()
            if pb and pb.get("item"):
                item = pb["item"]
 
                with _lock:
                    _cached.update({
                        "track":      item["name"],
                        "artist":     ", ".join(a["name"] for a in item["artists"]),
                        "album":      item["album"]["name"],
                        "progress":   pb.get("progress_ms", 0),
                        "duration":   item.get("duration_ms", 1),
                        "is_playing": pb.get("is_playing", False),
                        "track_id":   item["id"]
                    })
 
                print(f"[Spotify] {_cached['artist']} – {_cached['track']}")
            else:
                with _lock:
                    _cached["is_playing"] = False
 
        except Exception as e:
            print(f"[FetchLoop] Hata: {e}")
 
        time.sleep(3)
 
# ── Flask Endpoint'leri
 
@app.route("/now-playing")
def now_playing():
    """ESP32'nin çekeceği tek endpoint. Kompakt JSON döner."""
    with _lock:
        data = dict(_cached)
    return jsonify(data)
 
@app.route("/health")
def health():
    return jsonify({"status": "ok", "bridge": "cyberpunk-robot"})
 
# ── Başlat 
if __name__ == "__main__":
    t = threading.Thread(target=_fetch_loop, daemon=True)
    t.start()
    print("╔═══════════════════════════════════╗")
    print("║  Spotify Bridge Çalışıyor         ║")
    print("║  Bir Öneri Veya Hata varsa        ║")
    print("║  Yazmanız Yeterli                 ║")
    print("║  İyi Dinlemeler                   ║")
    print("║  Coder:Curly                      ║")
    print("║  http://0.0.0.0:5000/now-playing  ║")
    print("╚═══════════════════════════════════╝")
    app.run(host="0.0.0.0", port=5000, debug=False) 