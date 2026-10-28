#!/usr/bin/env python3
"""
update_market.py  |  MDB Intelligence: pembaruan data pasar dan kalibrasi harian

Menulis market.json di folder yang sama dengan dashboard. Jalankan sekali sehari
(cron di macOS/Linux, Task Scheduler di Windows), setelah pukul 17.00 WIB agar
JISDOR dan kurs referensi ECB hari itu sudah terbit.

Hanya memakai pustaka standar Python 3.8+ (tanpa instalasi tambahan).

Sumber:
  JISDOR (USD/IDR)       Bank Indonesia, halaman JISDOR (scraping, fallback ke ECB)
  Kurs IDR historis       ECB reference rates via Frankfurter API (api.frankfurter.app)
  SOFR level + riwayat    New York Fed Markets Data API
  EURIBOR 6M              ECB Data Portal (FM.M.U2.EUR.RT.MM.EURIBOR6MD_.HSTA, bulanan)
  EUR STR riwayat         ECB Data Portal (EST.B.EU000A2X2A25.WT, harian)
  Suku bunga BoJ, BI Rate Input manual di bagian KONFIGURASI (belum ada API publik stabil)

Metode kalibrasi:
  Volatilitas kurs  = simpangan baku return log harian x akar(252), jendela 3 tahun
  Korelasi kurs     = matriks korelasi Pearson return log harian, jendela 3 tahun
  Vasicek (kappa, theta, sigma) = OLS pada rata rata bulanan:
      dr = a + b r(t-1) + e,  dt = 1/12
      kappa = -b/dt, theta = -a/b, sigma = sd(e)/akar(dt)
  Parameter yang keluar dari batas wajar dipotong dan ditandai "clipped".

Penggunaan:
  python update_market.py
  python update_market.py --jisdor 17636 --jisdor-date 2026-09-18   (override manual JISDOR)
"""
import json, math, re, sys, statistics, urllib.request, datetime as dt, argparse, csv, io

# ------------------------------------------------------------------ KONFIGURASI MANUAL
BI_RATE = 5.75            # BI Rate (%), RDG 22 s.d. 23 September 2026; perbarui setelah setiap RDG
BI_RATE_DATE = "2026-09-23"
BOJ_RATE = 1.25           # Suku bunga kebijakan BoJ (%), naik 18 Sep 2026
BOJ_RATE_DATE = "2026-09-18"
CNY_RATE = None           # Isi bila tersedia acuan CNY resmi; None = CNY tetap asumsi
FX_WINDOW_YEARS = 3
RATE_WINDOW_YEARS = 5

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

UA = {"User-Agent": "MDB-Intelligence/1.0 (research dashboard)"}

# ------------------------------------------------------------------ HTTP
def http_get(url, timeout=40):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout, context=SSL_CTX) as r:
        return r.read().decode("utf-8", errors="replace")

# ------------------------------------------------------------------ STATISTIK
def log_returns(xs):
    return [math.log(xs[i] / xs[i - 1]) for i in range(1, len(xs)) if xs[i] > 0 and xs[i - 1] > 0]

def ann_vol(xs):
    r = log_returns(xs)
    return statistics.stdev(r) * math.sqrt(252) if len(r) > 30 else None

def corr(a, b):
    n = min(len(a), len(b))
    a, b = a[:n], b[:n]
    ma, mb = sum(a) / n, sum(b) / n
    sa = math.sqrt(sum((x - ma) ** 2 for x in a))
    sb = math.sqrt(sum((y - mb) ** 2 for y in b))
    return sum((x - ma) * (y - mb) for x, y in zip(a, b)) / (sa * sb) if sa and sb else 0.0

def monthly_avg(pairs):
    """pairs: list of (YYYY-MM-DD, value) -> list of monthly averages in time order"""
    buckets = {}
    for d, v in pairs:
        buckets.setdefault(d[:7], []).append(v)
    return [sum(v) / len(v) for k, v in sorted(buckets.items())]

def vasicek_ols(monthly):
    """OLS dr = a + b r_prev + e on monthly data (percent). Returns dict."""
    if len(monthly) < 24:
        return None
    x = monthly[:-1]
    y = [monthly[i + 1] - monthly[i] for i in range(len(monthly) - 1)]
    n = len(x)
    mx, my = sum(x) / n, sum(y) / n
    sxx = sum((xi - mx) ** 2 for xi in x)
    if sxx == 0:
        return None
    b = sum((xi - mx) * (yi - my) for xi, yi in zip(x, y)) / sxx
    a = my - b * mx
    resid = [yi - (a + b * xi) for xi, yi in zip(x, y)]
    s = statistics.stdev(resid)
    dt_ = 1 / 12
    kappa = -b / dt_
    theta = (-a / b) if b != 0 else mx
    sigma = s / math.sqrt(dt_)
    clipped = []
    if not (0.05 <= kappa <= 2.0):
        kappa = min(2.0, max(0.05, kappa)); clipped.append("kappa")
    if not (0.0 <= theta <= 8.0):
        theta = min(8.0, max(0.0, theta)); clipped.append("theta")
    if not (0.05 <= sigma <= 3.0):
        sigma = min(3.0, max(0.05, sigma)); clipped.append("sigma")
    return {"kappa": round(kappa, 4), "theta": round(theta, 4), "sigma": round(sigma, 4),
            "n_months": len(monthly), "clipped": clipped}

# ------------------------------------------------------------------ SUMBER DATA
def fetch_fx_history(start, end):
    """ECB reference rates via Frankfurter. Returns dict date -> {IDR,EUR,JPY,CNY per USD}."""
    urls = [f"https://api.frankfurter.app/{start}..{end}?from=USD&to=IDR,EUR,JPY,CNY",
            f"https://api.frankfurter.dev/v1/{start}..{end}?from=USD&to=IDR,EUR,JPY,CNY"]
    last_err = None
    for u in urls:
        try:
            return json.loads(http_get(u))["rates"], u
        except Exception as e:
            last_err = e
    raise RuntimeError(f"Frankfurter gagal: {last_err}")

def fetch_sofr_history(start, end):
    """New York Fed Markets API, dipecah per tahun untuk menghindari batas rentang."""
    out = []
    s = dt.date.fromisoformat(start)
    e = dt.date.fromisoformat(end)
    while s <= e:
        chunk_end = min(e, dt.date(s.year, 12, 31))
        url = (f"https://markets.newyorkfed.org/api/rates/secured/sofr/search.json"
               f"?startDate={s.isoformat()}&endDate={chunk_end.isoformat()}")
        data = json.loads(http_get(url))
        for row in data.get("refRates", []):
            if row.get("percentRate") is not None:
                out.append((row["effectiveDate"], float(row["percentRate"])))
        s = dt.date(s.year + 1, 1, 1)
    out.sort()
    return out

def fetch_ecb_series(flow, key, start):
    url = (f"https://data-api.ecb.europa.eu/service/data/{flow}/{key}"
           f"?format=csvdata&startPeriod={start}")
    text = http_get(url)
    rows = list(csv.DictReader(io.StringIO(text)))
    out = []
    for r in rows:
        try:
            out.append((r["TIME_PERIOD"], float(r["OBS_VALUE"])))
        except (KeyError, ValueError):
            pass
    return sorted(out)

BULAN = {"januari":1,"februari":2,"maret":3,"april":4,"mei":5,"juni":6,"juli":7,"agustus":8,"september":9,
         "oktober":10,"november":11,"desember":12,"january":1,"february":2,"march":3,"may":5,"june":6,"july":7,
         "august":8,"october":10,"december":12,"jan":1,"feb":2,"mar":3,"apr":4,"jun":6,"jul":7,"agu":8,"aug":8,
         "sep":9,"okt":10,"oct":10,"nov":11,"des":12,"dec":12}

def _parse_date(txt):
    m = re.search(r"(\d{1,2})\s+([A-Za-z]{3,9})\s+(20\d{2})", txt)
    if m and m.group(2).lower() in BULAN:
        return dt.date(int(m.group(3)), BULAN[m.group(2).lower()], int(m.group(1)))
    m = re.search(r"(\d{1,2})[/-](\d{1,2})[/-](20\d{2})", txt)
    if m:
        return dt.date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    m = re.search(r"(20\d{2})-(\d{2})-(\d{2})", txt)
    if m:
        return dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    return None

def fetch_jisdor(today=None, max_age_days=10):
    """Scraping halaman JISDOR BI: pasangkan tanggal dan nilai per baris tabel,
    ambil tanggal terbaru, tolak bila lebih tua dari max_age_days."""
    today = today or dt.date.today()
    html = http_get("https://www.bi.go.id/id/statistik/informasi-kurs/jisdor/default.aspx")
    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", html, flags=re.S | re.I)
    pairs = []
    for r in rows:
        txt = re.sub(r"<[^>]+>", " ", r)
        val = re.search(r"(\d{1,2}\.\d{3},\d{2})", txt)
        d = _parse_date(txt)
        if val and d:
            v = float(val.group(1).replace(".", "").replace(",", "."))
            if 10000 <= v <= 30000:
                pairs.append((d, v))
    if not pairs:
        raise RuntimeError("tabel JISDOR tidak terbaca (struktur halaman BI berubah)")
    d, v = max(pairs)
    age = (today - d).days
    if age > max_age_days or age < -1:
        raise RuntimeError(f"data JISDOR terbaru bertanggal {d.isoformat()} ({age} hari), ditolak karena usang")
    return v, d.isoformat()

# ------------------------------------------------------------------ UTAMA
def build(args, today=None):
    today = today or dt.date.today()
    log, M = [], {"generated_at": dt.datetime.now().isoformat(timespec="seconds"),
                  "items": {}, "fx": {}, "rates": {}, "corr": {}, "notes": []}

    # --- Kurs historis & kalibrasi volatilitas/korelasi
    fx_start = (today - dt.timedelta(days=365 * FX_WINDOW_YEARS)).isoformat()
    try:
        rates, src = fetch_fx_history(fx_start, today.isoformat())
        dates = sorted(rates)
        series = {"USD": [], "EUR": [], "JPY": [], "CNY": []}
        for d in dates:
            r = rates[d]
            if all(k in r for k in ("IDR", "EUR", "JPY", "CNY")):
                series["USD"].append(r["IDR"])
                series["EUR"].append(r["IDR"] / r["EUR"])
                series["JPY"].append(r["IDR"] / r["JPY"])
                series["CNY"].append(r["IDR"] / r["CNY"])
        for c, xs in series.items():
            M["fx"][c] = {"spot": round(xs[-1], 4), "date": dates[-1], "vol": round(ann_vol(xs), 4),
                          "n_obs": len(xs), "source": "ECB reference rate (Frankfurter)"}
        rets = {c: log_returns(xs) for c, xs in series.items()}
        ccys = list(series)
        for i, a in enumerate(ccys):
            for b in ccys[i + 1:]:
                M["corr"][f"{a}-{b}"] = round(corr(rets[a], rets[b]), 4)
        M["items"]["fx_window"] = f"{dates[0]} s.d. {dates[-1]} ({len(series['USD'])} hari bursa)"
        log.append(f"FX ok: {len(series['USD'])} observasi dari {src}")
    except Exception as e:
        log.append(f"FX gagal: {e}")

    # --- JISDOR (menimpa spot USD bila tersedia)
    jis = None
    if args.jisdor:
        jis = (args.jisdor, args.jisdor_date or today.isoformat()); jsrc = "JISDOR (input manual)"
    else:
        try:
            jis = fetch_jisdor(today); jsrc = "JISDOR Bank Indonesia"
        except Exception as e:
            log.append(f"JISDOR gagal: {e}")
    if jis and "USD" in M["fx"]:
        M["fx"]["USD"].update({"spot": jis[0], "date": jis[1], "source": jsrc})
        log.append(f"JISDOR ok: {jis[0]} ({jis[1]})")
    elif "USD" in M["fx"]:
        M["notes"].append("JISDOR tidak terbaca; spot USD memakai kurs referensi ECB.")

    # --- SOFR level + Vasicek
    r_start = (today - dt.timedelta(days=365 * RATE_WINDOW_YEARS)).isoformat()
    try:
        sofr = fetch_sofr_history(r_start, today.isoformat())
        est = vasicek_ols(monthly_avg(sofr))
        M["rates"]["USD"] = {"level": sofr[-1][1], "date": sofr[-1][0], "benchmark": "SOFR",
                             "source": "New York Fed Markets API", "vasicek": est}
        log.append(f"SOFR ok: {sofr[-1]} | Vasicek {est}")
    except Exception as e:
        log.append(f"SOFR gagal: {e}")

    # --- EURIBOR 6M level + dinamika dari EUR STR
    try:
        eur6 = fetch_ecb_series("FM", "M.U2.EUR.RT.MM.EURIBOR6MD_.HSTA", r_start[:7])
        est_src = fetch_ecb_series("EST", "B.EU000A2X2A25.WT", r_start)
        est = vasicek_ols(monthly_avg(est_src))
        M["rates"]["EUR"] = {"level": eur6[-1][1], "date": eur6[-1][0], "benchmark": "EURIBOR 6M",
                             "source": "ECB Data Portal", "vasicek": est,
                             "note": "Dinamika diestimasi dari EUR STR harian"}
        log.append(f"EUR ok: {eur6[-1]} | Vasicek {est}")
    except Exception as e:
        log.append(f"EUR gagal: {e}")

    # --- Input manual
    M["rates"]["JPY"] = {"level": BOJ_RATE, "date": BOJ_RATE_DATE, "benchmark": "BoJ policy rate",
                         "source": "Input manual (Bank of Japan)", "vasicek": None}
    if CNY_RATE is not None:
        M["rates"]["CNY"] = {"level": CNY_RATE, "date": today.isoformat(), "benchmark": "CNY",
                             "source": "Input manual", "vasicek": None}
    M["items"]["bi_rate"] = {"level": BI_RATE, "date": BI_RATE_DATE, "source": "Input manual (Bank Indonesia)"}
    M["log"] = log
    return M

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jisdor", type=float)
    ap.add_argument("--jisdor-date")
    ap.add_argument("--out", default="market.json")
    args = ap.parse_args()
    M = build(args)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(M, f, ensure_ascii=False, indent=2)
    print("\n".join(M["log"]))
    print(f"Tersimpan: {args.out}")

if __name__ == "__main__":
    main()
