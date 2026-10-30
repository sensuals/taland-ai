# VERSI GROQ GRATIS — 30 Okt 2026, dari app_fixed.py milik Apip (edit Apip
# dan semua perbaikan sebelumnya dipertahankan; yang diganti hanya sumber
# model chat-nya: Ollama lokal -> Groq cloud, free tier).
#
# CARA PAKAI (versi otomatis, 30 Okt 2026):
# 1. Daftar gratis di console.groq.com (tanpa kartu kredit), buat API key
#    di menu API Keys. JANGAN kirim key ke siapa pun / tulis di chat.
# 2. Install:  pip install langchain-groq python-dotenv
#    (di .venv Apip:  .venv\Scripts\python -m pip install langchain-groq python-dotenv)
# 3. Pasang key SEKALI di file .env di folder yang sama dengan app ini:
#          GROQ_API_KEY=gsk_...
#    Key dibaca otomatis saat aplikasi jalan — tidak ada lagi kolom
#    key di sidebar, dan tidak perlu isi ulang tiap refresh/restart.
#    Alternatif (jarang dipakai): set environment variable GROQ_API_KEY
#    di Windows, atau Streamlit secrets .streamlit/secrets.toml.
#    Setelah membuat/mengubah .env, restart Streamlit.
# 4. Jalankan:  streamlit run app_groq.py
#    Model chat dan mode jawaban dipilih OTOMATIS per pertanyaan
#    (tidak ditampilkan/dipilih di sidebar): model teknis/hitungan
#    pakai gpt-oss-120b, pertanyaan sangat pendek dan umum pakai
#    gpt-oss-20b yang cepat; pertanyaan tentang Taland/produk/
#    dokumen otomatis dijawab dari boiler_db, sisanya penalaran umum.
#    File pendamping tetap sama: style.css dan logo.png di folder yang sama.
#    Kalkulator dan Proposal Generator tetap jalan TANPA key, karena
#    tidak memakai model AI.
#    DEPLOY ONLINE (Streamlit Community Cloud, gratis): file ini bisa
#    di-deploy apa adanya (lihat paket deploy). Folder boiler_db TIDAK
#    ikut di-upload; kalau folder itu tidak ada, pertanyaan dokumen
#    otomatis dijawab dengan penalaran umum + pemberitahuan.
#
# MODEL (dicek dari docs Groq, 29-30 Okt 2026):
# - openai/gpt-oss-120b (Production, default) — paling pintar di free tier,
#   konteks 131.072 token, ~500 token/detik.
# - openai/gpt-oss-20b (Production) — paling cepat, ~1.000 token/detik.
# - qwen/qwen3.8-27b (Preview) — bisa teks + gambar, tapi status Preview:
#   hanya untuk evaluasi, bisa dihentikan sewaktu-waktu oleh Groq.
# LIMIT FREE TIER (per model, per organisasi, dicek 29 Okt 2026):
# 30 request/menit, 1.000 request/hari, 8.000 token/menit, 200.000
# token/hari. Kalau kena limit, aplikasi menampilkan pesan 429 dan
# sarannya, bukan crash. Limit bisa berubah — yang berlaku adalah
# halaman Limits di console Groq milik Apip sendiri.
# CATATAN: Mode "Hanya dari dokumen boiler_db" MASIH butuh Ollama lokal
# (untuk embedding nomic-embed-text) + folder boiler_db. Mode default
# "Bebas — berpikir umum" TIDAK butuh Ollama sama sekali.
import os
import re
from pathlib import Path

import streamlit as st

BASE_DIR = Path(__file__).resolve().parent

# Muat file .env di folder yang sama dengan app ini, supaya GROQ_API_KEY
# di .env terbaca otomatis tanpa kolom input di sidebar. Dua lapis:
# (1) python-dotenv kalau ter-install, (2) parser manual sederhana
# sebagai cadangan — jadi .env tetap terbaca walau python-dotenv
# belum ter-install atau load_dotenv gagal diam-diam. Parser manual
# hanya mengisi variabel yang belum ada, dan memangkas spasi/kutip.
def _load_env_file(path: Path) -> None:
    try:
        text = path.read_text(encoding="utf-8-sig")
    except Exception:
        return
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'").strip()
        if key and value and key not in os.environ:
            os.environ[key] = value


try:
    from dotenv import load_dotenv

    load_dotenv(BASE_DIR / ".env")
    load_dotenv(Path.cwd() / ".env")
except Exception:
    pass
_load_env_file(BASE_DIR / ".env")
_load_env_file(Path.cwd() / ".env")

st.set_page_config(
    page_title="Taland AI",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inisialisasi di paling atas, di luar blok menu, supaya selalu ada
# sebelum dibaca di bagian chat, apa pun urutan edit file-nya.
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_question" not in st.session_state:
    st.session_state.pending_question = None

css_path = BASE_DIR / "style.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

with st.sidebar:
    logo_path = BASE_DIR / "logo.png"
    if logo_path.exists():
        st.image(str(logo_path), width=50)
    st.markdown("## Taland AI")
    st.markdown("### Made by Apip")

    menu = st.selectbox(
        "Menu",
        [
            "Engineering Chat",
            "Steam Calculator",
            "Fuel Calculator",
            "Boiler Sizing",
            "Proposal Generator"
        ],
    )

    # Groq jalan di server Groq, bukan di CPU/GPU PC Apip. Tidak perlu
    # pull model dan tidak perlu GPU. Model dan mode jawaban dipilih
    # otomatis per pertanyaan (lihat select_groq_model dan
    # select_answer_mode), jadi keduanya tidak ditampilkan lagi di
    # sidebar sesuai permintaan Apip. API key dibaca otomatis dari .env /
    # environment variable / Streamlit secrets — tidak ada kolom key.
    env_key = os.environ.get("GROQ_API_KEY", "").strip()
    secrets_key = ""
    try:
        secrets_key = str(st.secrets.get("GROQ_API_KEY", "") or "").strip()
    except Exception:
        secrets_key = ""
    groq_api_key = env_key or secrets_key
    if groq_api_key:
        st.caption("✅ API key Groq terpasang otomatis (tidak ditampilkan).")
    # Kalau key belum terpasang, tidak ada peringatan kuning di sidebar
    # sesuai permintaan Apip. Penjelasan muncul di chat saat pertanyaan
    # dikirim (lihat error di bawah).
    # Mode jawaban TIDAK dipilih di sidebar lagi: ditentukan otomatis
    # per pertanyaan di bawah (select_answer_mode).

if menu == "Steam Calculator":
    st.header("Steam Requirement Calculator")

    fluid = st.selectbox(
        "Jenis Zat Yang Dipanaskan",
        [
           "Air (Water)",
           "Thermal Oil",
           "Susu",
           "CPO",
           "Minyak Goreng",
           "Solar",
           "Ethanol",
           "Larutan Gula",
           "Air Laut",
           "Custom"
        ],
    )

    cp_dict = {
        "Air (Water)": 1.00,
        "Thermal Oil": 0.50,
        "Susu": 0.94,
        "CPO": 0.48,
        "Minyak Goreng": 0.47,
        "Solar": 0.50,
        "Ethanol": 0.58,
        "Larutan Gula": 0.81,
        "Air Laut": 0.95
    }
    if fluid == "Custom":
        cp = st.number_input(
            "Cp (kcal/kg°C)",
            value=1.00
        )

    else:
        cp = cp_dict[fluid]

    mass = st.number_input("Kapasitas / Massa Produk (kg)",value=1000.0)
    heating_time = st.number_input("Waktu Pemanasan (Jam)", value=1.0)
    t1 = st.number_input("Temperature Awal (°C)", value=30.0)
    t2 = st.number_input("Temperature Akhir (°C)", value=90.0)

    safety_factor = st.number_input(
        "Efisiensi (%)",
        value=10.0
    )

    if st.button("Hitung Kebutuhan Energi"):
        if heating_time <= 0:
            st.error("Waktu pemanasan harus lebih dari 0 jam.")
        elif t2 <= t1:
            st.error("Temperature akhir harus lebih tinggi dari temperature awal.")
        elif mass <= 0:
            st.error("Massa harus lebih dari 0 kg.")
        else:
            delta_t = t2 - t1
            q = mass * cp * delta_t
            heat_load = q / heating_time
            steam_required = heat_load / 540
            efisiensi = ((safety_factor + 100) / 100 ) * heat_load
            recommended_boiler = (steam_required *(1 + safety_factor/100))

            st.metric("Energi Yang Diperlukan", f"{heat_load:,.0f} kcal/h")
            st.metric("Energi + Efisiensi to Cust.", f"{efisiensi:,.0f} kcal/h")
            st.metric("Steam Requirement", f"{steam_required:,.0f} kg steam/h")

            st.metric(
                "Recommended Boiler Capacity to Cust.",
                f"{recommended_boiler:,.0f} kg steam/h"
            )

            st.info(
                f"""
    RUMUS:

    Q = m × Cp × ΔT

    m = {mass:,.0f} kg

    Cp = {cp:.2f} kcal/kg°C

    ΔT = {delta_t:.1f} °C

    Total Energi (Q) = {q:,.0f} kcal

    Heat Transfer Rate (q) = {heat_load:,.0f} kcal/h

    Steam Requirement = Heat Load ÷ 540

    Boiler Capacity = Steam Requirement + Safety Factor
    """
        )

if menu == "Fuel Calculator":
    st.header("Fuel Consumption Calculator")

    steam = st.number_input("Steam Demand (kg/hr)", value=2000.0)
    fuel = st.selectbox(
        "Jenis Bahan Bakar",
        [
            "LPG",
            "Natural Gas",
            "Solar (Light Oil)",
            "Kayu",
            "Cangkang Sawit",
            "Batubara",
            "Heavy Oil (MFO)",
            "Waste Oil"
        ],
    )

    efficiency = st.selectbox(
        "Efisiensi Boiler (%)",
        [
            50,
            60,
            70,
            75,
            80,
            85,
            90
        ]
    )
    lhv_dict = {

        "LPG": 11000,
        "Natural Gas": 12000,
        "Solar (Light Oil)": 10200,
        "Kayu": 3500,
        "Cangkang Sawit": 4300,
        "Batubara": 5000,
        "Heavy Oil (MFO)": 9600,
        "Waste Oil": 9000,
    }
    lhv = lhv_dict[fuel]

    if st.button("Hitung Fuel"):
        if steam <= 0:
            st.error("Steam demand harus lebih dari 0 kg/hr.")
        else:
            steam_energy = steam * 540
            fuel_consumption = (steam_energy / (lhv * (efficiency / 100)))
            st.metric("Fuel Consumption", f"{fuel_consumption:,.2f} kg/hr")
            st.metric("LHV", f"{lhv:,.0f} kcal/kg")
            st.metric("Boiler Efficiency", f"{efficiency}%")
            st.info(
            f"""
Rumus:

Fuel Consumption = ( Steam × 540 ) ÷ ( LHV × Efisiensi )

Steam Demand = {steam:,.0f} kg/hr

LHV = {lhv:,.0f} kcal/kg

Efisiensi = {efficiency}%
"""
            )

if menu == "Boiler Sizing":
    st.header("Boiler Sizing")
    capacity = st.number_input("Steam Demand (kg/hr)", value=2000.0)
    if st.button("Sizing Boiler"):
        if capacity <= 0:
            st.error("Steam demand harus lebih dari 0 kg/hr.")
        else:
            st.success(f"Rekomendasi Boiler = {capacity * 1.1:,.0f} kg/hr")

if menu == "Proposal Generator":
    st.header("Proposal Generator")
    customer = st.text_input("Nama Customer")
    capacity = st.text_input("Kapasitas Boiler")

    if st.button("Generate Proposal"):
        if not customer.strip() or not capacity.strip():
            st.error("Nama customer dan kapasitas boiler harus diisi.")
        else:
            proposal = f"""
PROPOSAL TEKNIS

Customer:
{customer.strip()}

Kapasitas:
{capacity.strip()}

Sistem:
Steam Boiler

Fuel:
Gas / Solar

Standar:
ASME
"""
            st.download_button(
                "Download Proposal",
                proposal,
                file_name="proposal.txt",
            )

@st.cache_resource(show_spinner=False)
def load_database():
    # Import ditunda ke sini supaya mode Bebas (default) tidak butuh
    # Ollama/Chroma sama sekali. Hanya mode Dokumen yang memakainya.
    try:
        from langchain_chroma import Chroma
        from langchain_ollama import OllamaEmbeddings
    except ImportError as exc:
        raise RuntimeError(
            "Mode Dokumen butuh langchain-chroma + langchain-ollama "
            "dan Ollama yang jalan. Pakai mode Bebas, atau install: "
            "pip install langchain-chroma langchain-ollama"
        ) from exc
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    return Chroma(
        persist_directory=str(BASE_DIR / "boiler_db"),
        embedding_function=embeddings,
    )


@st.cache_resource(show_spinner=False)
def get_llm(model: str, temperature: float, api_key: str):
    # Import ditunda ke sini supaya pesan error-nya jelas kalau
    # langchain-groq belum ter-install di .venv Apip.
    try:
        from langchain_groq import ChatGroq
    except ImportError as exc:
        raise RuntimeError(
            "langchain-groq belum ter-install. Jalankan di .venv: "
            "pip install langchain-groq, lalu restart Streamlit."
        ) from exc
    # model_name + groq_api_key adalah nama field kanonis ChatGroq
    # (dicek langsung dari ChatGroq.model_fields). reasoning_effort
    # sengaja tidak diset: pakai default Groq, dan penalaran terlihat
    # tetap diminta lewat prompt. max_tokens DULU 900 (bebas) / 600
    # (dokumen) — terlalu kecil: jawaban hitungan panjang yang penuh
    # rumus LaTeX habis di tengah jalan (kepotong di langkah 4 pada
    # 30 Okt 2026). Sekarang 3000 / 1500: masih jauh di bawah limit
    # free tier Groq (8.000 token/menit, 200.000 token/hari per model).
    return ChatGroq(
        model_name=model,
        groq_api_key=api_key,
        temperature=temperature,
        max_tokens=3000 if temperature >= 0.3 else 1500,
    )

def select_groq_model(question: str) -> str:
    # Model ditentukan otomatis saat prompt dibuat, tanpa pilihan manual.
    # Hampir semua pertanyaan boiler/teknis/hitungan pakai model paling
    # pintar (gpt-oss-120b). Hanya pertanyaan sangat pendek, umum, dan
    # tanpa angka/kata teknis yang pakai gpt-oss-20b yang lebih cepat.
    # qwen3.8-27b (Preview) sengaja tidak dipakai otomatis.
    q = (question or "").lower()
    technical = (
        "hitung", "sizing", "trip", "troubleshoot", "desain", "rekomendasi",
        "penyebab", "cara", "steam", "fuel", "kapasitas", "tekanan",
        "temperatur", "boiler", "suhu", "katup", "pompa", "burner",
        "bahan bakar", "efisiensi",
    )
    if (
        len(q.strip()) <= 60
        and not any(word in q for word in technical)
        and not any(ch.isdigit() for ch in q)
    ):
        return "openai/gpt-oss-20b"
    return "openai/gpt-oss-120b"


def select_answer_mode(question: str) -> bool:
    # Mode jawaban ditentukan otomatis saat prompt dibuat, tanpa
    # pilihan di sidebar. Return True = Bebas (penalaran umum),
    # False = Dokumen (hanya dari boiler_db).
    # Pertanyaan tentang PT Taland Utama, Taland Thermal, produk,
    # katalog, spesifikasi, harga, atau dokumen perusahaan otomatis
    # dijawab dari boiler_db, supaya spesifikasi produk tidak ditebak.
    # Pertanyaan engineering umum / hitungan / troubleshooting umum
    # tetap dijawab dengan penalaran umum.
    q = (question or "").lower()
    document_keywords = (
        "taland",
        "thermal",
        "produk",
        "katalog",
        "spesifikasi",
        "datasheet",
        "data sheet",
        "brosur",
        "manual",
        "garansi",
        "harga",
        "perusahaan",
        "profil",
    )
    if any(word in q for word in document_keywords):
        return False
    return True



_SUPERSCRIPT = str.maketrans("0123456789+-=()", "\u2070\u00b9\u00b2\u00b3\u2074\u2075\u2076\u2077\u2078\u2079\u207a\u207b\u207c\u207d\u207e")


def clean_math_text(text: str) -> str:
    """Ubah sisa LaTeX di jawaban jadi teks biasa yang pasti tampil.

    Streamlit di app ini terbukti TIDAK merender rumus LaTeX: baik
    tanda kurung siku maupun dolar tampil apa adanya sebagai kode aneh
    (30 Okt 2026). Jadi rumus ditulis ulang sebagai teks biasa dengan
    simbol Unicode. Fungsi ini idempotent: teks yang sudah bersih
    tidak berubah.
    """
    if not text:
        return text
    text = re.sub(r"\\text\{([^{}]*)\}", r"\1", text)
    text = re.sub(r"\\mathrm\{([^{}]*)\}", r"\1", text)
    text = re.sub(r"\\mathbf\{([^{}]*)\}", r"\1", text)
    text = re.sub(r"\\dot\{([^{}]*)\}", r"\1_dot", text)
    text = re.sub(r"_\{([^{}]*)\}", r"_\1", text)

    def _sup(m):
        inner = m.group(1)
        if all(c in "0123456789+-=()" for c in inner):
            return inner.translate(_SUPERSCRIPT)
        return "^" + inner

    text = re.sub(r"\^\{([^{}]*)\}", _sup, text)
    text = re.sub(r"\^([0-9+\-()])", lambda m: m.group(1).translate(_SUPERSCRIPT), text)
    text = re.sub(r"\\Delta\s", "Δ", text)
    text = re.sub(r"\\frac\{([^{}]*)\}\{([^{}]*)\}", r"(\1)/(\2)", text)
    simple = {
        r"\times": "\u00d7",
        r"\cdot": "\u00d7",
        r"\approx": "\u2248",
        r"\Delta": "\u0394",
        r"\delta": "\u03b4",
        r"\circ": "\u00b0",
        r"\div": "\u00f7",
        r"\leq": "\u2264",
        r"\geq": "\u2265",
        r"\pm": "\u00b1",
        r"\rightarrow": "\u2192",
        r"\left": "",
        r"\right": "",
        r"\!": "",
        r"\,": " ",
        r"\;": " ",
        r"\ ": " ",
    }
    for cmd, symbol in simple.items():
        text = text.replace(cmd, symbol)
    text = re.sub(r"\\[a-zA-Z]+", "", text)
    for delim in ("$$", "$", "\\[", "\\]", "\\(", "\\)"):
        text = text.replace(delim, "")
    text = text.replace("{", "").replace("}", "")
    text = re.sub(r"[ \t]+", " ", text)
    text = text.replace("^", "")
    return text


def build_prompt(question: str, context: str, history: list[dict], free_mode: bool = True) -> str:
    history_text = ""
    if history:
        lines = []
        for msg in history[-6:]:  # 3 tanya-jawab terakhir, cukup
            role = "User" if msg["role"] == "user" else "Asisten"
            lines.append(f"{role}: {msg['content'][:600]}")
        history_text = "\n".join(lines)

    if free_mode:
        # MODE BEBAS: berpikir umum seperti Muse, tidak dibatasi boiler_db.
        # Referensi (kalau ada) hanya pendukung, bukan satu-satunya sumber.
        return f"""Anda adalah asisten engineering yang berpikir seperti Muse: paham maksud pertanyaan, bernalar, dan menjelaskan dengan jelas.

Jawab dalam Bahasa Indonesia, singkat tapi lengkap. Boleh menjawab topik engineering umum, bukan hanya boiler, dan jangan menolak pertanyaan hanya karena tidak ada di dokumen referensi.

CARA MENJAWAB:
1. Pahami dulu apa yang sebenarnya ditanyakan, termasuk konteks dari Riwayat Chat. Kalau pertanyaan lanjutan, sambung pembahasan sebelumnya, jangan mulai dari nol.
2. Bernalarlah langkah demi langkah: jelaskan logika / prinsipnya dulu, baru kesimpulan dan rekomendasi.
3. Untuk hitungan: tulis rumus, sebut asumsi yang dipakai, substitusi angkanya, lalu hasil + satuan. Sarankan cek ulang di menu kalkulator bila ada. JANGAN pakai LaTeX sama sekali untuk rumus (tanpa tanda dolar, kurung siku, atau perintah LaTeX seperti times, frac, dan text). Tulis rumus dengan teks biasa dan simbol Unicode: × · ≈ Δ ° ÷ ± ² ³. Contoh: Q = m × cp × ΔT = 1000 × 4,186 × 60 = 251.160 kJ. Pecahan tulis sebagai (a)/(b).
4. Untuk troubleshooting: urutkan penyebab dari yang paling mungkin, sebut cara mengeceknya dengan aman, dan kapan harus berhenti / memanggil teknisi.
5. Bedakan angka yang pasti dari perkiraan: angka dari pertanyaan atau rumus itu pasti; spesifikasi produk, standar, atau harga yang tidak yakin harus disebut sebagai perkiraan / rentang umum dan wajib dicek di manual atau pabrikan. Jangan menyajikannya seolah spesifikasi pasti.
6. Jika ada Referensi Tambahan di bawah dan relevan, pakailah sebagai pendukung dan sebut sumbernya seperti [Sumber 1]. Jika tidak relevan, abaikan saja.

Referensi Tambahan (opsional, boleh diabaikan):
{context if context else "(tidak ada)"}

Riwayat Chat:
{history_text if history_text else "(belum ada)"}

Pertanyaan:
{question}

Jawaban:
"""

    # MODE DOKUMEN: prompt ketat lama — hanya dari boiler_db.
    return f"""Anda adalah Senior Boiler Engineer. Jawab dalam Bahasa Indonesia, singkat dan langsung ke intinya.

ATURAN WAJIB:
1. Gunakan HANYA Referensi di bawah. Jangan memakai pengetahuan umum untuk angka, spesifikasi, standar, atau harga.
2. Jika Referensi tidak menjawab pertanyaan, jawab persis: "Tidak ada di dokumen referensi saya." Lalu sebutkan info apa yang kurang, tanpa menebak.
3. Jangan mengarang angka, kapasitas, temperatur, tekanan, atau nama standar. Jika angka tidak ada di Referensi/pertanyaan, katakan tidak ada.
4. Untuk pertanyaan hitungan: tulis rumus, substitusi angka yang memang ada di pertanyaan/Referensi, dan sarankan cek ulang di menu kalkulator. Jangan mengubah angka dari pertanyaan.
5. Jika memakai Referensi, sebut sumbernya seperti [Sumber 1].
6. Jika pertanyaan lanjutan, pakai Riwayat Chat untuk konteksnya.
7. JANGAN pakai LaTeX sama sekali untuk rumus (tanpa tanda dolar, kurung siku, atau perintah LaTeX seperti times, frac, dan text). Tulis rumus dengan teks biasa dan simbol Unicode: × · ≈ Δ ° ÷ ± ² ³. Contoh: Q = m × cp × ΔT = 1000 × 4,186 × 60 = 251.160 kJ. Pecahan tulis sebagai (a)/(b).

Referensi:
{context if context else "(tidak ada referensi yang ditemukan)"}

Riwayat Chat:
{history_text if history_text else "(belum ada)"}

Pertanyaan:
{question}

Jawaban:
"""


if menu == "Engineering Chat":
    _, center, _ = st.columns([1, 2, 1])
    with center:
        st.markdown(
            """
            <h1 style='text-align:center; margin-bottom:0;'>TALAND AI</h1>
            <p style='text-align:center; color:#64748b;'>
            Engineering • Sizing • Troubleshooting Assistant
            </p>
            """,
            unsafe_allow_html=True,
        )

    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "pending_question" not in st.session_state:
        st.session_state.pending_question = None

    # Hapus chat di sidebar, bukan di tengah layar utama.
    with st.sidebar:
        st.divider()
        if st.button("Hapus chat", key="hapus_chat_sidebar"):
            st.session_state.messages = []
            st.rerun()

    # Saat chat masih kosong, hanya tampilkan contoh pertanyaan yang
    # bisa diklik. Kotak sambutan biru sudah dihapus sesuai permintaan.
    if not st.session_state.messages:
        with center:
            examples = [
                (
                    "Sizing boiler",
                    "Bagaimana cara sizing boiler untuk steam demand 2000 kg/h?",
                ),
                (
                    "Boiler trip",
                    "Apa penyebab boiler sering trip dan cara mengatasinya?",
                ),
                (
                    "Hitung steam",
                    "Hitung kebutuhan steam untuk memanaskan 1000 kg air "
                    "dari 30°C ke 90°C dalam 1 jam.",
                ),
            ]
            ex_cols = st.columns(len(examples))
            for col, (label, full_question) in zip(ex_cols, examples):
                if col.button(label):
                    st.session_state.pending_question = full_question
                    st.rerun()

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            _content = msg["content"]
            if msg["role"] == "assistant":
                _content = clean_math_text(_content)
            st.markdown(_content)
            if msg["role"] == "assistant" and msg.get("sources"):
                with st.expander("Sumber yang dipakai"):
                    for source in msg["sources"]:
                        st.markdown(f"- {source}")

    typed_question = st.chat_input("Tanyakan sesuatu tentang boiler...")
    question = typed_question or st.session_state.get("pending_question")
    st.session_state.pending_question = None

    if question:
        with st.chat_message("user"):
            st.markdown(question)

        # Mode jawaban ditentukan otomatis dari pertanyaan ini:
        # Taland/produk/dokumen -> boiler_db, sisanya -> penalaran umum.
        free_mode = select_answer_mode(question)

        # Versi online (Streamlit Cloud): folder boiler_db tidak ikut
        # di-deploy, jadi mode Dokumen tidak bisa jalan di sini. Kalau
        # pertanyaan mengarah ke dokumen, jawab dengan penalaran umum
        # dan beri tahu alasannya — jangan biarkan model menjawab
        # dengan prompt ketat tanpa referensi.
        if not free_mode and not (BASE_DIR / "boiler_db").exists():
            st.info(
                "Versi online: jawaban dari dokumen (boiler_db) tidak "
                "tersedia di sini, jadi pertanyaan ini dijawab dengan "
                "penalaran umum. Untuk jawaban dari dokumen, pakai "
                "aplikasi di laptop."
            )
            free_mode = True

        # 1) Retrieval — HANYA di mode Dokumen, dan hanya di sini.
        #    Mode Bebas tidak memuat boiler_db sama sekali: lebih cepat
        #    dan tidak berpatokan pada folder itu.
        context = ""
        sources: list[str] = []
        if not free_mode:
            try:
                db = load_database()
                docs = db.similarity_search(question, k=4)
                parts = []
                for i, doc in enumerate(docs, start=1):
                    source = (
                        doc.metadata.get("source")
                        or doc.metadata.get("file")
                        or doc.metadata.get("title")
                        or "boiler_db"
                    )
                    sources.append(source)
                    parts.append(f"[Sumber {i} — {source}]\n{doc.page_content}")
                context = "\n\n".join(parts)
            except Exception:
                st.warning(
                    "Database boiler_db / Ollama tidak bisa dibaca. "
                    "Jawaban mungkin kurang akurat. Pastikan Ollama jalan "
                    "dan folder boiler_db ada di folder yang sama dengan app.py."
                )

        # 2) Jawab dengan streaming + histori chat.
        #    Model ditentukan otomatis dari pertanyaan ini dan tidak
        #    ditampilkan lagi, sesuai permintaan Apip.
        model_name = select_groq_model(question)
        prompt = build_prompt(
            question, context, st.session_state.messages, free_mode=free_mode
        )
        with st.chat_message("assistant"):
            if not groq_api_key:
                answer = ""
                st.error(
                    "API key Groq belum dipasang. Daftar gratis di "
                    "console.groq.com, buat key di menu API Keys, lalu "
                    "pasang GROQ_API_KEY di file .env di folder yang sama "
                    "dengan app ini dan restart Streamlit. Kalkulator "
                    "tetap bisa dipakai tanpa key."
                )
            else:
                try:
                    llm = get_llm(
                        model_name, 0.3 if free_mode else 0.1, groq_api_key
                    )

                    def _stream_text(chunks):
                        for chunk in chunks:
                            if chunk.content:
                                yield clean_math_text(chunk.content)

                    answer = st.write_stream(_stream_text(llm.stream(prompt)))
                except Exception as exc:
                    answer = ""
                    detail = str(exc)
                    if "429" in detail or "rate_limit" in detail.lower():
                        st.error(
                            "Limit gratis Groq habis untuk hari/menit ini "
                            "(error 429). Tunggu sebentar lalu coba lagi, "
                            "atau cek sisa jatah di halaman Limits "
                            "console.groq.com."
                        )
                    elif "401" in detail or "invalid_api_key" in detail.lower():
                        st.error(
                            "API key Groq tidak diterima (error 401). "
                            "Periksa lagi key-nya di console.groq.com — "
                            "key diawali gsk_ dan tidak ada spasi di "
                            "ujungnya."
                        )
                    else:
                        st.error(
                            "Groq tidak merespons. Periksa koneksi internet "
                            f"dan API key. Detail: {exc}"
                        )

        if answer:
            st.session_state.messages.append(
                {"role": "user", "content": question}
            )
            st.session_state.messages.append(
                {"role": "assistant", "content": answer, "sources": sources}
            )

