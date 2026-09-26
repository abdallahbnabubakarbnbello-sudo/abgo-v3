import os, math, requests
from datetime import datetime, date
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)
TIMEOUT = 15

def get_json(url, params=None):
    r = requests.get(url, params=params, timeout=TIMEOUT, headers={"User-Agent":"ABGO-Islam/3.0"})
    r.raise_for_status()
    return r.json()

@app.get("/")
def index():
    return render_template("index.html")

@app.get("/api/prayer")
def prayer():
    lat=request.args.get("lat", type=float)
    lon=request.args.get("lon", type=float)
    method=request.args.get("method", default="3", type=str)
    if lat is None or lon is None:
        return jsonify({"error":"Location is required"}),400
    try:
        data=get_json("https://api.aladhan.com/v1/timings", {
            "latitude":lat,"longitude":lon,"method":method
        })
        return jsonify(data)
    except Exception as e:
        return jsonify({"error":f"Prayer service unavailable: {e}"}),502

@app.get("/api/qibla")
def qibla():
    lat=request.args.get("lat", type=float); lon=request.args.get("lon", type=float)
    if lat is None or lon is None: return jsonify({"error":"Location is required"}),400
    try:
        return jsonify(get_json(f"https://api.aladhan.com/v1/qibla/{lat}/{lon}"))
    except Exception as e:
        return jsonify({"error":f"Qibla service unavailable: {e}"}),502

@app.get("/api/hijri")
def hijri():
    lat=request.args.get("lat", type=float); lon=request.args.get("lon", type=float)
    if lat is None or lon is None: return jsonify({"error":"Location is required"}),400
    try:
        d=get_json("https://api.aladhan.com/v1/timings", {"latitude":lat,"longitude":lon})
        return jsonify({"date":d.get("data",{}).get("date",{})})
    except Exception as e:
        return jsonify({"error":f"Calendar service unavailable: {e}"}),502

@app.get("/api/calendar")
def calendar():
    lat=request.args.get("lat", type=float); lon=request.args.get("lon", type=float)
    year=request.args.get("year", type=int, default=datetime.now().year)
    month=request.args.get("month", type=int, default=datetime.now().month)
    if lat is None or lon is None: return jsonify({"error":"Location is required"}),400
    try:
        return jsonify(get_json(f"https://api.aladhan.com/v1/calendar/{year}/{month}", {
            "latitude":lat,"longitude":lon,"method":3
        }))
    except Exception as e:
        return jsonify({"error":f"Calendar service unavailable: {e}"}),502

@app.get("/api/quran/surahs")
def quran_surahs():
    try:
        return jsonify(get_json("https://api.alquran.cloud/v1/surah"))
    except Exception as e:
        return jsonify({"error":f"Quran service unavailable: {e}"}),502

@app.get("/api/quran/surah/<int:number>")
def quran_surah(number):
    if not 1 <= number <= 114: return jsonify({"error":"Invalid surah"}),400
    edition=request.args.get("edition","en.sahih")
    try:
        arabic=get_json(f"https://api.alquran.cloud/v1/surah/{number}/quran-uthmani")
        trans=get_json(f"https://api.alquran.cloud/v1/surah/{number}/{edition}")
        audio=get_json(f"https://api.alquran.cloud/v1/surah/{number}/ar.alafasy")
        return jsonify({"arabic":arabic.get("data"),"translation":trans.get("data"),"audio":audio.get("data")})
    except Exception as e:
        return jsonify({"error":f"Quran service unavailable: {e}"}),502

@app.get("/api/quran/search")
def quran_search():
    q=request.args.get("q","").strip()
    edition=request.args.get("edition","en.sahih")
    if len(q)<2: return jsonify({"data":[]})
    try:
        return jsonify(get_json("https://api.alquran.cloud/v1/search/"+requests.utils.quote(q)+"/all/"+edition))
    except Exception as e:
        return jsonify({"error":f"Quran search unavailable: {e}"}),502

@app.get("/api/names")
def names():
    try:
        return jsonify(get_json("https://api.aladhan.com/v1/asmaAlHusna"))
    except Exception as e:
        return jsonify({"error":f"Names service unavailable: {e}"}),502

@app.get("/api/mosques")
def mosques():
    lat=request.args.get("lat", type=float); lon=request.args.get("lon", type=float)
    radius=min(request.args.get("radius", type=int, default=5000),20000)
    if lat is None or lon is None: return jsonify({"error":"Location is required"}),400
    q=f"""[out:json][timeout:20];(nwr["amenity"="place_of_worship"]["religion"="muslim"](around:{radius},{lat},{lon});nwr["amenity"="place_of_worship"]["name"~"mosque|masjid",i](around:{radius},{lat},{lon}););out center tags;"""
    try:
        r=requests.post("https://overpass-api.de/api/interpreter", data=q, timeout=25,
                        headers={"User-Agent":"ABGO-Islam/3.0"})
        r.raise_for_status()
        return jsonify(r.json())
    except Exception as e:
        return jsonify({"error":f"Mosque search unavailable: {e}"}),502

@app.get("/api/health")
def health():
    return jsonify({"ok":True,"version":"ABGO Islam Real V3","time":datetime.utcnow().isoformat()+"Z"})

if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",5000)),debug=False)
