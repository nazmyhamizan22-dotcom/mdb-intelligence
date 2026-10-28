#!/usr/bin/env python3
"""
mdb_server.py  |  Hosting lokal MDB Intelligence + Gemini Copilot

Fungsi:
  1. Menyajikan dashboard HTML di http://127.0.0.1:8000
  2. Endpoint POST /api/ask untuk panel Copilot di dashboard:
       konteks dashboard  +  Google Search grounding  +  pengetahuan umum Gemini
  3. Mode Autopilot (brainstorming dua tahap: rencana, lalu eksekusi dengan web)
  4. Mode chat di terminal:  python3 mdb_server.py --chat

Hanya pustaka standar Python 3.8+. Kunci API dibaca dari variabel lingkungan
GEMINI_API_KEY dan tidak pernah dikirim ke browser.

Contoh:
  export GEMINI_API_KEY="kunci_anda"
  python3 mdb_server.py                       # server, buka http://127.0.0.1:8000
  python3 mdb_server.py --open                # sekaligus membuka browser
  python3 mdb_server.py --chat                # tanya jawab langsung di terminal
  python3 mdb_server.py --refresh-market      # jalankan update_market.py dulu
"""
import argparse, glob, json, mimetypes, os, re, sys, threading, time, urllib.error, urllib.request, webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

API_BASE = "https://generativelanguage.googleapis.com/v1beta"
DEFAULT_MODEL = os.environ.get("GEMINI_MODEL", "gemini-flash-latest")
MAX_CONTEXT_CHARS = 50_000
STR_LIMIT = 2500
LIST_LIMIT = 25
STATE = {"model": DEFAULT_MODEL, "html": None, "root": os.getcwd(), "fallbacks": [], "dead": set(), "last_errors": [], "search_off_until": 0, "pinned": False}


import ssl
def _ssl_ctx():
    """Konteks SSL: Keychain macOS (truststore), lalu certifi, lalu bawaan sistem."""
    try:
        import truststore
        return truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    except Exception:
        pass
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()
SSL_CTX = _ssl_ctx()

SYSTEM_PROMPT = """Anda adalah MDB Intelligence Copilot: rekan analis yang membantu tim Kementerian Keuangan memahami pembiayaan World Bank, ADB, AIIB, dan IsDB. Bicaralah seperti analis senior yang menjelaskan kepada kolega: hangat, jelas, langsung ke inti, tanpa basa basi.

GAYA
Mulai dengan jawaban inti dalam satu atau dua kalimat, baru rinciannya.
Sesuaikan panjang dengan pertanyaan. Pertanyaan faktual cukup satu paragraf pendek tanpa judul. Pertanyaan analitis boleh memakai sub judul singkat (###) dan poin, tetapi jangan membuat struktur laporan formal kecuali diminta.
Tulis kalimat utuh yang mengalir. Hindari daftar poin untuk hal yang bisa dijelaskan dalam satu paragraf.
Jangan memakai garis pemisah (---), jangan memakai judul bertingkat lebih dari ###, dan jangan menulis tanda bintang yang di escape.
Jangan gunakan em dash atau en dash; gunakan koma, titik dua, atau kalimat baru.
Akhiri analisis panjang dengan satu kalimat saran langkah berikutnya bila relevan, bukan ringkasan ulang.

SUMBER
Data dashboard (DASHBOARD_CONTEXT) adalah sumber utama untuk angka proyek, pembiayaan, lokasi, Green Book 2026, simulasi, dan profil MDB (mdb_profiles). Patuhi data_definitions: nilai pembiayaan di dashboard adalah nilai proyek tercatat, bukan portofolio aktif atau outstanding.
Pencarian web dipakai untuk fakta terkini di luar dashboard bila tersedia. Pengetahuan umum dipakai untuk konsep dan pertanyaan bebas.
Beri penanda sumber secukupnya: satu penanda [Dashboard], [Web], atau [Umum] di akhir paragraf atau poin yang memuat angka atau klaim penting, bukan di setiap kalimat.
Angka simulasi selalu disebut hasil model, bukan kuotasi resmi. Bila ada selisih antara pengetahuan umum dan dashboard, utamakan dashboard dan sebutkan selisihnya.
Bila data tidak ada, katakan terus terang dalam satu kalimat, lalu bantu dengan yang tersedia."""

AUTOPILOT_ONE = """Mode AUTOPILOT untuk brainstorming. Bila permintaan ternyata pertanyaan faktual sederhana, jawab langsung seperti biasa tanpa rencana.
Untuk permintaan analitis, tulis dua bagian dengan judul persis:
### Rencana
Tiga sampai lima poin singkat: tujuan, pertanyaan kunci, dan data yang dipakai.
### Hasil
Buka dengan inti jawaban dalam dua atau tiga kalimat. Lalu uraikan analisis dengan sub judul singkat (####), tawarkan tiga opsi atau gagasan beserta kelebihan dan risikonya, dan tutup dengan rekomendasi langkah berikutnya serta asumsi penting. Tulis mengalir dan manusiawi, bukan seperti formulir."""

AUTOPILOT_PLAN = """Anda sedang dalam mode AUTOPILOT (brainstorming analitis). Tahap 1: susun RENCANA ANALISIS ringkas untuk permintaan pengguna, berisi:
1. Tujuan analisis dalam satu kalimat.
2. Tiga sampai enam sub pertanyaan kunci.
3. Data dashboard yang relevan (sebutkan bagian konteks yang akan dipakai).
4. Informasi eksternal yang perlu dicari di web.
5. Bentuk keluaran akhir yang paling berguna.
Jangan menjawab permintaan dulu. Tulis rencana dalam poin singkat."""

AUTOPILOT_EXEC = """Anda sedang dalam mode AUTOPILOT tahap 2. Laksanakan RENCANA di bawah secara menyeluruh: gunakan DASHBOARD_CONTEXT, lakukan pencarian web bila diperlukan, lalu hasilkan dokumen kerja dengan struktur:
Ringkasan eksekutif
Analisis per sub pertanyaan
Opsi atau gagasan (minimal tiga, dengan kelebihan dan risiko)
Rekomendasi dan langkah berikutnya
Asumsi dan keterbatasan
Tandai sumber [Dashboard], [Web], atau [Umum]."""

# ---------------------------------------------------------------- Gemini REST
def _key():
    k = re.sub(r"\s+", "", os.environ.get("GEMINI_API_KEY", "")).strip("\"'")
    if not k:
        raise RuntimeError("GEMINI_API_KEY belum diset. Jalankan: export GEMINI_API_KEY=\"kunci_anda\"")
    return k

def _post(url, payload, timeout=120):
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), method="POST",
                                 headers={"Content-Type": "application/json", "x-goog-api-key": _key()})
    with urllib.request.urlopen(req, timeout=timeout, context=SSL_CTX) as r:
        return json.loads(r.read().decode("utf-8"))

def _get(url, timeout=30):
    req = urllib.request.Request(url, headers={"x-goog-api-key": _key()})
    with urllib.request.urlopen(req, timeout=timeout, context=SSL_CTX) as r:
        return json.loads(r.read().decode("utf-8"))

def _err_text(e):
    try:
        err = json.loads(e.read().decode("utf-8")).get("error", {})
        msg = err.get("message", str(e))
        for d in err.get("details", []) or []:
            if d.get("retryDelay"):
                msg += f' retryDelay: "{d["retryDelay"]}"'
        return msg
    except Exception:
        return str(e)

def resolve_model():
    """Pilih model Flash terbaru yang tersedia untuk kunci ini."""
    data, names, token = None, [], ""
    for _ in range(5):
        data = _get(f"{API_BASE}/models?pageSize=100" + (f"&pageToken={token}" if token else ""))
        for m in data.get("models", []):
            if "generateContent" in m.get("supportedGenerationMethods", []):
                names.append(m["name"].split("/")[-1])
        token = data.get("nextPageToken", "")
        if not token:
            break
    def rank(n):
        bad = any(x in n for x in ("lite", "image", "tts", "audio", "live", "embedding", "vision", "learnlm", "thinking-exp"))
        ver = [float(v) for v in re.findall(r"gemini-(\d+(?:\.\d+)?)", n)] or [0]
        return (0 if bad else 1, 1 if "flash" in n else 0, ver[0], 0 if "preview" in n or "exp" in n else 1)
    cands = sorted(names, key=rank, reverse=True)
    if not cands:
        raise RuntimeError("Tidak ada model Gemini yang mendukung generateContent untuk kunci ini.")
    STATE["fallbacks"] = [c for c in cands if not any(x in c for x in ("image", "tts", "audio", "live", "embedding", "vision", "omni", "transcribe"))][:10]
    return cands[0]

def _retry_delay(e_msg, attempt):
    m = re.search(r'"?retryDelay"?\s*:\s*"?(\d+(?:\.\d+)?)s', e_msg)
    d = float(m.group(1)) if m else 2 ** attempt * 2
    return min(d, 30)

def _call(model, payload):
    return _post(f"{API_BASE}/models/{model}:generateContent", payload)

TIME_BUDGET = 25   # detik, batas total satu permintaan

def _classify(code, msg):
    m = msg.lower()
    if code == 429:
        if "limit: 0" in m or "limit:0" in m:
            return "no_quota"
        if "per day" in m or "perday" in m or "daily" in m:
            return "daily"
        if "search" in m or "grounding" in m:
            return "search_quota"
        return "rpm"
    if code in (500, 503):
        return "busy"
    if code == 401 or (code in (400, 403) and ("api key" in m or "api_key" in m or "authentication" in m or "permission" in m)):
        return "auth"
    return "other"

def gemini(contents, system, use_search=True, temperature=0.4, max_tokens=8192):
    payload = {"systemInstruction": {"parts": [{"text": system}]}, "contents": contents,
               "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens}}
    if use_search and time.time() >= STATE["search_off_until"]:
        payload["tools"] = [{"google_search": {}}]
    if not STATE["fallbacks"]:
        try:
            resolve_model()
        except Exception:
            pass
    PREFER = ("gemini-3.5-flash", "gemini-3.6-flash", "gemini-3-flash-preview")
    rest = sorted([m for m in STATE["fallbacks"] if m != STATE["model"]], key=lambda m: (0 if m in PREFER else 1, PREFER.index(m) if m in PREFER else 0))
    order = [STATE["model"]] + rest
    order = [m for m in order if m not in STATE["dead"]] or order
    t0, last = time.time(), ""
    for model in order:
        retried = False
        while time.time() - t0 < TIME_BUDGET:
            try:
                data = _call(model, payload)
                if not STATE["pinned"]:
                    STATE["model"] = model
                res = _parse(data); res["model_used"] = model
                return res
            except urllib.error.HTTPError as e:
                msg = _err_text(e); kind = _classify(e.code, msg)
                last = f"{model}: HTTP {e.code} {kind}: {msg[:220]}"
                STATE["last_errors"] = (STATE["last_errors"] + [last])[-20:]
                sys.stderr.write(f"  Gemini {e.code} [{kind}] {model}: {msg[:160]}\n")
                if e.code == 429 and "tools" in payload:
                    payload.pop("tools"); STATE["search_off_until"] = time.time() + 600
                    sys.stderr.write("  Google Search ditolak (kuota), lanjut tanpa search selama 10 menit\n")
                    continue
                if kind == "auth":
                    raise RuntimeError(AUTH_HELP)
                if e.code == 404:
                    STATE["dead"].add(model); break
                if e.code == 400 and "tools" in payload and ("search" in msg.lower() or "tool" in msg.lower()):
                    payload.pop("tools"); continue
                if kind in ("no_quota", "daily"):
                    STATE["dead"].add(model); break
                if kind == "search_quota" and "tools" in payload:
                    payload.pop("tools"); continue
                if kind in ("rpm", "busy") and not retried:
                    retried = True
                    wait = min(_retry_delay(msg, 0), 8 if kind == "rpm" else 2)
                    if time.time() - t0 + wait < TIME_BUDGET:
                        time.sleep(wait); continue
                break
            except urllib.error.URLError as e:
                last = f"{model}: {e}"; break
        if time.time() - t0 >= TIME_BUDGET:
            break
    if "no_quota" in last or "daily" in last:
        raise RuntimeError("Kuota Gemini untuk kunci ini habis atau bernilai nol pada model yang tersedia. Jalankan: python3 mdb_server.py --diagnose")
    if "429" in last:
        raise RuntimeError("Batas permintaan per menit Gemini tercapai. Tunggu sekitar 1 menit lalu coba lagi.")
    if "503" in last or "500" in last:
        raise RuntimeError("Server Gemini sedang padat. Coba lagi beberapa saat lagi.")
    raise RuntimeError(f"Gemini gagal: {last[:200]}")

AUTH_HELP = ("Kunci Gemini ditolak Google (autentikasi gagal). Kunci berawalan AQ. sering ditolak oleh Gemini API. "
             "Buat kunci berformat AIza lewat console.cloud.google.com > APIs & Services > Credentials > Create credentials > API key "
             "pada proyek yang mengaktifkan Generative Language API, lalu jalankan ulang: unset GEMINI_API_KEY; bash jalankan.sh")

def key_warning():
    k = re.sub(r"\s+", "", os.environ.get("GEMINI_API_KEY", "")).strip("\"'")
    if k.startswith("AIza") and len(k) != 39:
        return f"PERINGATAN: panjang kunci {len(k)} karakter, seharusnya 39. Kunci kemungkinan terpotong saat ditempel."
    if k and not k.startswith("AIza"):
        return "PERINGATAN: kunci tidak berawalan AIza; kunci AQ. sering ditolak Gemini API (galat 401)."
    return ""

SEARCH_OFF_NOTE = ("\nCatatan sistem: pencarian web sedang tidak tersedia. Untuk fakta terkini di luar dashboard, jawab dari pengetahuan "
                   "Anda, tandai [Umum], sebutkan bahwa informasi mungkin tidak mutakhir, dan sarankan verifikasi ke situs resmi.")

def _parse(data):
    cand = (data.get("candidates") or [{}])[0]
    parts = cand.get("content", {}).get("parts", [])
    text = "".join(p.get("text", "") for p in parts if not p.get("thought"))
    gm = cand.get("groundingMetadata", {}) or {}
    sources, seen = [], set()
    for ch in gm.get("groundingChunks", []) or []:
        w = ch.get("web") or {}
        if w.get("uri") and w["uri"] not in seen:
            seen.add(w["uri"]); sources.append({"uri": w["uri"], "title": w.get("title", w["uri"])})
    if not text:
        text = f"Model tidak menghasilkan teks (finishReason: {cand.get('finishReason', 'tidak diketahui')})."
    return {"text": text, "sources": sources, "grounded": bool(sources or gm.get("webSearchQueries")),
            "queries": gm.get("webSearchQueries", [])}

KEY_LIMITS = {"mdb_profiles": 7000, "financing_terms": 4500, "output": 4500, "output_text": 3500,
              "calibration": 2500, "methodology": 2500}

def slim(obj, depth=0, key=""):
    """Pangkas konteks: string panjang dipotong (batas per bagian), daftar panjang diringkas."""
    if isinstance(obj, str):
        lim = KEY_LIMITS.get(key, STR_LIMIT)
        return obj if len(obj) <= lim else obj[:lim] + " ...[dipotong]"
    if isinstance(obj, list):
        out = [slim(x, depth + 1) for x in obj[:LIST_LIMIT]]
        if len(obj) > LIST_LIMIT:
            out.append(f"...[{len(obj) - LIST_LIMIT} item lain tidak dikirim]")
        return out
    if isinstance(obj, dict):
        return {k: slim(v, depth + 1, k) for k, v in obj.items() if v not in (None, "", [], {})}
    return obj

LIGHT = re.compile(r"^(hai|halo|hi|hello|pagi|siang|sore|malam|terima kasih|makasih|thanks|ok|oke|siapa (kamu|namamu|nama kamu)|nama kamu siapa|kamu siapa)[\s!?.]*$", re.I)

def _history(hist):
    out = []
    for h in (hist or [])[-10:]:
        role = "model" if h.get("role") in ("assistant", "model") else "user"
        txt = str(h.get("text", ""))[:6000]
        if txt:
            out.append({"role": role, "parts": [{"text": txt}]})
    return out

def answer(question, context, history=None, mode="auto"):
    if mode != "autopilot" and LIGHT.match(question.strip()):
        r = gemini(_history(history) + [{"role": "user", "parts": [{"text": question}]}],
                   SYSTEM_PROMPT + "\nIni sapaan ringan. Jawab singkat dan ramah, perkenalkan diri sebagai MDB Intelligence Copilot, dan tawarkan bantuan.",
                   use_search=False, temperature=0.6, max_tokens=512)
        return {"answer": r["text"], "sources": [], "web_grounding": False, "queries": [], "model": r.get("model_used", STATE["model"]), "mode": "light"}
    ctx = json.dumps(slim(context or {}), ensure_ascii=False)
    if len(ctx) > MAX_CONTEXT_CHARS:
        ctx = ctx[:MAX_CONTEXT_CHARS] + " ...[konteks dipotong]"
    user_turn = f"DASHBOARD_CONTEXT (JSON):\n{ctx}\n\nPERTANYAAN PENGGUNA:\n{question}"
    base = _history(history)
    if mode == "autopilot":
        r = gemini(base + [{"role": "user", "parts": [{"text": user_turn}]}],
                   SYSTEM_PROMPT + (SEARCH_OFF_NOTE if time.time() < STATE["search_off_until"] else "") + "\n\n" + AUTOPILOT_ONE, use_search=True, temperature=0.6, max_tokens=4096)
        txt = r["text"]; plan = ""
        m = re.search(r"(?is)#+\s*rencana.*?\n(.*?)(?=\n#+\s*hasil)", txt)
        if m:
            plan = m.group(1).strip()
            txt = re.sub(r"(?is)^.*?\n#+\s*hasil[^\n]*\n", "", txt, count=1).strip()
        return {"answer": txt, "plan": plan, "sources": r["sources"], "web_grounding": r["grounded"],
                "queries": r["queries"], "model": r.get("model_used", STATE["model"]), "mode": "autopilot"}
    sysp = SYSTEM_PROMPT + (SEARCH_OFF_NOTE if time.time() < STATE["search_off_until"] else "")
    r = gemini(base + [{"role": "user", "parts": [{"text": user_turn}]}], sysp, use_search=True)
    return {"answer": r["text"], "sources": r["sources"], "web_grounding": r["grounded"],
            "queries": r["queries"], "model": r.get("model_used", STATE["model"]), "mode": "auto"}

# ---------------------------------------------------------------- HTTP server
class Handler(BaseHTTPRequestHandler):
    server_version = "MDBIntelligence/1.0"

    def log_message(self, fmt, *args):
        sys.stderr.write("  %s  %s\n" % (time.strftime("%H:%M:%S"), fmt % args))

    def _json(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/api/health":
            return self._json(200, {"ok": True, "model": STATE["model"],
                                    "api_key_set": bool(os.environ.get("GEMINI_API_KEY")),
                                    "dashboard": os.path.basename(STATE["html"] or ""), "dead_models": sorted(STATE["dead"]), "web_search": "nonaktif sementara" if time.time() < STATE["search_off_until"] else "aktif", "last_errors": STATE["last_errors"][-5:]})
        target = STATE["html"] if path in ("/", "/index.html") else os.path.normpath(os.path.join(STATE["root"], path.lstrip("/")))
        if not target.startswith(STATE["root"]) or not os.path.isfile(target):
            return self._json(404, {"error": "Tidak ditemukan"})
        ctype = mimetypes.guess_type(target)[0] or "application/octet-stream"
        with open(target, "rb") as f:
            data = f.read()
        self.send_response(200)
        self.send_header("Content-Type", ctype + ("; charset=utf-8" if ctype.startswith("text") or ctype.endswith("json") else ""))
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store" if target.endswith(".json") else "no-cache")
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        if self.path.split("?")[0] != "/api/ask":
            return self._json(404, {"error": "Endpoint tidak dikenal"})
        try:
            n = int(self.headers.get("Content-Length", "0"))
            req = json.loads(self.rfile.read(n).decode("utf-8") or "{}")
            q = str(req.get("question", "")).strip()
            if not q:
                return self._json(400, {"error": "Pertanyaan kosong"})
            res = answer(q, req.get("context"), req.get("history"), req.get("mode", "auto"))
            return self._json(200, res)
        except RuntimeError as e:
            return self._json(502, {"error": str(e)})
        except Exception as e:
            return self._json(500, {"error": f"Kesalahan server: {e}"})

# ---------------------------------------------------------------- Konteks untuk mode terminal
def load_dashboard_db(html_path):
    t = open(html_path, encoding="utf-8", errors="ignore").read()
    s = t.find("const DB=")
    if s < 0:
        return {}
    s += len("const DB="); d = 0; i = s
    while i < len(t):
        c = t[i]
        if c == "{": d += 1
        elif c == "}":
            d -= 1
            if d == 0: break
        i += 1
    try:
        return json.loads(t[s:i + 1])
    except Exception:
        return {}

def terminal_context(db, question, market):
    P, L = db.get("projects", []), db.get("locations", [])
    by_mdb, fin, sec = {}, {}, {}
    for p in P:
        m = p.get("mdb", "?"); by_mdb[m] = by_mdb.get(m, 0) + 1
        try: fin[m] = fin.get(m, 0) + float(p.get("financing_amount_usd") or 0)
        except Exception: pass
        s = p.get("sector_final") or p.get("sector_class") or p.get("sector_harmonized") or "Lainnya"
        sec[s] = sec.get(s, 0) + 1
    prov = {}
    for l in L:
        if l.get("province"): prov[l["province"]] = prov.get(l["province"], 0) + 1
    ql = question.lower()
    stop = {"proyek", "project", "yang", "dari", "untuk", "dengan", "apa", "saja", "berapa", "bagaimana", "jelaskan", "tentang"}
    terms = [w for w in re.findall(r"\w+", ql) if len(w) > 3 and w not in stop]
    mdbs = [m for m in ("world bank", "adb", "aiib", "isdb") if m in ql]
    provs = [pv for pv in prov if pv.lower() in ql]
    loc_ids = {l.get("master_project_id") for l in L if l.get("province") in provs} if provs else set()
    scored = []
    for p in P:
        if mdbs and p.get("mdb", "").lower() not in mdbs:
            continue
        if provs and p.get("master_project_id") not in loc_ids:
            continue
        h = json.dumps(p, ensure_ascii=False).lower()
        sc = sum(1 for w in terms if w in h) + (5 if provs else 0) + (2 if mdbs else 0)
        if sc: scored.append((sc, p))
    scored.sort(key=lambda x: -x[0])
    return {"sumber": "Database tertanam dashboard (mode terminal, tanpa status UI)",
            "jumlah_proyek": len(P), "jumlah_titik_lokasi": len(L),
            "proyek_per_mdb": by_mdb, "pembiayaan_usd_tersedia_per_mdb": fin,
            "sektor_teratas": dict(sorted(sec.items(), key=lambda x: -x[1])[:15]),
            "provinsi_teratas": dict(sorted(prov.items(), key=lambda x: -x[1])[:15]),
            "filter_terdeteksi": {"mdb": mdbs, "provinsi": provs},
            "jumlah_proyek_cocok": len(scored),
            "proyek_relevan": [{k: p.get(k) for k in ("project_id", "mdb", "project_name", "sector_final",
                                "status", "approval_year", "financing_amount_usd", "location_raw", "source_url")}
                               for _, p in scored[:40]],
            "market_json": market}

def chat(html_path):
    db = load_dashboard_db(html_path)
    market = None
    mp = os.path.join(os.path.dirname(os.path.abspath(html_path)), "market.json")
    if os.path.isfile(mp):
        market = json.load(open(mp, encoding="utf-8"))
    print(f"\nMDB Intelligence Copilot (terminal) | model {STATE['model']} | {len(db.get('projects', []))} proyek dimuat")
    print("Perintah: /autopilot <permintaan>, /reset, /keluar\n")
    hist = []
    while True:
        try:
            q = input("Anda > ").strip()
        except (EOFError, KeyboardInterrupt):
            print(); break
        if not q: continue
        if q in ("/keluar", "/exit", "/quit"): break
        if q == "/reset":
            hist = []; print("Riwayat dihapus.\n"); continue
        mode = "autopilot" if q.startswith("/autopilot") else "auto"
        q2 = q[len("/autopilot"):].strip() if mode == "autopilot" else q
        print("  ...menganalisis" + (" (autopilot: rencana dan hasil dalam satu langkah)" if mode == "autopilot" else ""))
        try:
            r = answer(q2, terminal_context(db, q2, market), hist, mode)
        except RuntimeError as e:
            print(f"  Galat: {e}\n"); continue
        if r.get("plan"):
            print("\n=== Rencana autopilot ===\n" + r["plan"].strip())
        print("\n=== Jawaban ===\n" + r["answer"].strip())
        if r.get("sources"):
            print("\nSumber web:")
            for s in r["sources"][:8]:
                print(f"  - {s['title']}: {s['uri']}")
        print(f"\n[model {r['model']} | web grounding {'aktif' if r['web_grounding'] else 'tidak dipakai'}]\n")
        hist += [{"role": "user", "text": q2}, {"role": "model", "text": r["answer"]}]


def diagnose():
    print("\nDiagnosa Gemini")
    try:
        best = resolve_model()
    except Exception as e:
        print("  Gagal membaca daftar model:", e); return
    print(f"  Model tersedia (urutan prioritas): {', '.join(STATE['fallbacks'])}\n")
    tiny = [{"role": "user", "parts": [{"text": "Balas satu kata: siap"}]}]
    for m in STATE["fallbacks"][:6]:
        for tools in (False, True):
            p = {"contents": tiny, "generationConfig": {"maxOutputTokens": 16}}
            if tools: p["tools"] = [{"google_search": {}}]
            try:
                _call(m, p); res = "OK"
            except urllib.error.HTTPError as e:
                msg = _err_text(e); res = f"HTTP {e.code} [{_classify(e.code, msg)}] {msg[:150]}"
            except Exception as e:
                res = f"galat: {e}"
            print(f"  {m:28} {'dengan search' if tools else 'tanpa search '}  {res}")
            time.sleep(1)
    print("\nArti hasil: OK = siap dipakai; no_quota = kuota tier gratis nol untuk model itu; daily = kuota harian habis;")
    print("rpm = batas per menit; search_quota = kuota Google Search habis. Bila semua no_quota, aktifkan billing di aistudio.google.com.\n")

# ---------------------------------------------------------------- Utama
def pick_html(arg):
    here = os.getcwd()
    files = sorted(glob.glob("MDB_INTELLIGENCE_DASHBOARD*.html"), key=os.path.getmtime, reverse=True)
    if arg:
        p = os.path.abspath(os.path.expanduser(arg))
        if os.path.isfile(p):
            return p
        print(f"\nPERINGATAN: file '{arg}' tidak ada di folder {here}")
        dl = os.path.expanduser(os.path.join("~/Downloads", os.path.basename(arg)))
        if os.path.isfile(dl):
            print(f"File ditemukan di Downloads. Pindahkan dulu dengan perintah:\n  mv \"{dl}\" \"{here}/\"")
        if not files:
            sys.exit("Tidak ada file dashboard lain di folder ini. Server dihentikan.")
        print(f"Server memakai file dashboard terbaru yang ada: {files[0]}\n")
    if not files:
        sys.exit(f"File dashboard tidak ditemukan di folder {here}. Pindahkan file MDB_INTELLIGENCE_DASHBOARD_V56.html ke folder ini.")
    return os.path.abspath(files[0])

def main():
    ap = argparse.ArgumentParser(description="Hosting lokal MDB Intelligence + Gemini Copilot")
    ap.add_argument("--html", help="Path file dashboard HTML (default: file MDB_INTELLIGENCE_DASHBOARD*.html terbaru)")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--model", help="Nama model Gemini (default otomatis)")
    ap.add_argument("--chat", action="store_true", help="Mode tanya jawab di terminal")
    ap.add_argument("--open", action="store_true", help="Buka browser otomatis")
    ap.add_argument("--diagnose", action="store_true", help="Uji kuota dan ketersediaan tiap model Gemini")
    ap.add_argument("--refresh-market", action="store_true", help="Jalankan update_market.py sebelum server mulai")
    a = ap.parse_args()
    STATE["html"] = pick_html(a.html)
    STATE["root"] = os.path.dirname(STATE["html"])
    if a.model:
        STATE["model"] = a.model; STATE["pinned"] = True
    if a.refresh_market and os.path.isfile(os.path.join(STATE["root"], "update_market.py")):
        os.system(f'cd "{STATE["root"]}" && "{sys.executable}" update_market.py')
    key_ok = bool(os.environ.get("GEMINI_API_KEY"))
    if a.diagnose:
        if not key_ok: sys.exit("GEMINI_API_KEY belum diset.")
        return diagnose()
    if a.chat:
        if not key_ok:
            sys.exit("GEMINI_API_KEY belum diset.")
        return chat(STATE["html"])
    srv = ThreadingHTTPServer((a.host, a.port), Handler)
    url = f"http://{a.host}:{a.port}"
    print("\nMDB Intelligence berjalan")
    print(f"  Dashboard : {os.path.basename(STATE['html'])}")
    print(f"  Alamat    : {url}")
    print(f"  Gemini    : {'kunci terdeteksi' if key_ok else 'KUNCI BELUM DISET (Copilot memakai mode offline)'} | model {STATE['model']}")
    if key_warning():
        print("  " + key_warning())
    print("  Hentikan  : Ctrl+C\n")
    if a.open:
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nServer dihentikan.")

if __name__ == "__main__":
    main()
