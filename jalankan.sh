#!/bin/bash
# Peluncur MDB Intelligence. Jalankan dengan:  bash jalankan.sh
cd "$(dirname "$0")" || exit 1

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 belum terpasang. Unduh dari https://www.python.org/downloads/ lalu ulangi."
  exit 1
fi

cek_kunci () {
  # keluaran: OK, TIDAK_VALID, AQ_DITOLAK, ATAU KONEKSI
  local code
  code=$(curl -s -o /tmp/mdb_cek.json -w "%{http_code}" --max-time 15 \
    "https://generativelanguage.googleapis.com/v1beta/models?pageSize=1" \
    -H "x-goog-api-key: $1")
  case "$code" in
    200) echo OK ;;
    401) echo AQ_DITOLAK ;;
    000) echo KONEKSI ;;
    *)   echo TIDAK_VALID ;;
  esac
}

coba=0
while :; do
  if [ -z "$GEMINI_API_KEY" ]; then
    read -r -s -p "Tempel GEMINI_API_KEY (tidak ditampilkan), atau Enter untuk mode offline: " GEMINI_API_KEY; echo
  fi
  # buang spasi, tanda kutip, dan awalan export yang ikut tertempel
  GEMINI_API_KEY=$(printf '%s' "$GEMINI_API_KEY" | sed -e 's/^export GEMINI_API_KEY=//' | tr -d " \t\r\n\"'")
  if [ -z "$GEMINI_API_KEY" ]; then
    echo "Tanpa kunci: dashboard tetap jalan, AI Copilot memakai mode offline."
    break
  fi
  echo "Kunci terbaca: ${#GEMINI_API_KEY} karakter, awalan ${GEMINI_API_KEY:0:4}"
  hasil=$(cek_kunci "$GEMINI_API_KEY")
  case "$hasil" in
    OK) echo "Kunci valid."; export GEMINI_API_KEY; break ;;
    KONEKSI) echo "Tidak bisa menghubungi Google (cek internet). Server tetap dijalankan dengan kunci ini."; export GEMINI_API_KEY; break ;;
    AQ_DITOLAK) echo "Ditolak (401). Kunci berawalan AQ. sering ditolak Gemini API. Buat kunci berawalan AIza di Google Cloud Console > APIs & Services > Credentials." ;;
    *) echo "Ditolak: kunci tidak valid. Pastikan disalin utuh (kunci AIza = 39 karakter). Kunci yang baru dibuat perlu 1 sampai 2 menit untuk aktif." ;;
  esac
  coba=$((coba+1)); unset GEMINI_API_KEY
  if [ $coba -ge 3 ]; then echo "Tiga kali gagal. Server dijalankan tanpa kunci (mode offline)."; break; fi
done
rm -f /tmp/mdb_cek.json

if [ -f update_market.py ]; then
  echo "Memperbarui data pasar..."
  python3 update_market.py || echo "Data pasar gagal diperbarui, dashboard memakai data terakhir."
fi

python3 mdb_server.py --open --model gemini-3.5-flash "$@"
