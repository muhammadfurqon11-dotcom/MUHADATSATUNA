import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import base64
import io
import google.generativeai as genai  # Integrasi dengan Google Gemini API

# Konfigurasi API Key untuk Gemini (ganti dengan API key Anda)
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "YOUR_API_KEY_HERE")  # Gunakan Streamlit secrets untuk produksi
genai.configure(api_key=GEMINI_API_KEY)

# Inisialisasi model Gemini
model = genai.GenerativeModel('gemini-pro')  # Atau model lain seperti 'gemini-1.5-pro'

# Inisialisasi database sederhana menggunakan SQLite (untuk demo, data hilang saat restart app)
conn = sqlite3.connect(':memory:', check_same_thread=False)
cursor = conn.cursor()

# Buat tabel-tabel dasar (sama seperti sebelumnya)
cursor.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, role TEXT, password TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS cases (id INTEGER PRIMARY KEY, title TEXT, description TEXT, user_id INTEGER)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS discussions (id INTEGER PRIMARY KEY, case_id INTEGER, user_id INTEGER, comment TEXT, timestamp TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS assignments (id INTEGER PRIMARY KEY, title TEXT, description TEXT, due_date TEXT, user_id INTEGER)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS submissions (id INTEGER PRIMARY KEY, assignment_id INTEGER, user_id INTEGER, content TEXT, timestamp TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS learning_logs (id INTEGER PRIMARY KEY, user_id INTEGER, case_id INTEGER, log TEXT, timestamp TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS reports (id INTEGER PRIMARY KEY, user_id INTEGER, content TEXT, timestamp TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS assessments (id INTEGER PRIMARY KEY, title TEXT, questions TEXT)''')  # questions as JSON string for simplicity
cursor.execute('''CREATE TABLE IF NOT EXISTS quizzes (id INTEGER PRIMARY KEY, title TEXT, questions TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS evaluations (id INTEGER PRIMARY KEY, user_id INTEGER, competency TEXT, score INTEGER)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS forums (id INTEGER PRIMARY KEY, topic TEXT, user_id INTEGER)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS forum_posts (id INTEGER PRIMARY KEY, forum_id INTEGER, user_id INTEGER, content TEXT, timestamp TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY, from_user INTEGER, to_user INTEGER, content TEXT, timestamp TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS materials (id INTEGER PRIMARY KEY, title TEXT, type TEXT, content BLOB)''')  # content as BLOB for files
cursor.execute('''CREATE TABLE IF NOT EXISTS progress (id INTEGER PRIMARY KEY, user_id INTEGER, module TEXT, status TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS attendance (id INTEGER PRIMARY KEY, user_id INTEGER, date TEXT, status TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS simulations (id INTEGER PRIMARY KEY, title TEXT, description TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS notifications (id INTEGER PRIMARY KEY, user_id INTEGER, message TEXT, timestamp TEXT)''')
conn.commit()

# Data dummy untuk demo
cursor.execute("INSERT OR IGNORE INTO users (username, role, password) VALUES ('admin', 'admin', 'admin'), ('dosen', 'dosen', 'dosen'), ('mahasiswa', 'mahasiswa', 'mahasiswa')")
conn.commit()

# Fungsi helper
def get_user_id(username):
    cursor.execute("SELECT id FROM users WHERE username=?", (username,))
    result = cursor.fetchone()
    return result[0] if result else None

def login():
    if 'user' not in st.session_state:
        st.sidebar.title("Login")
        username = st.sidebar.text_input("Username")
        password = st.sidebar.text_input("Password", type="password")
        if st.sidebar.button("Login"):
            cursor.execute("SELECT role FROM users WHERE username=? AND password=?", (username, password))
            result = cursor.fetchone()
            if result:
                st.session_state.user = username
                st.session_state.role = result[0]
                st.sidebar.success("Login berhasil!")
            else:
                st.sidebar.error("Username atau password salah")
        return False
    return True

# Fungsi untuk integrasi Gemini: Generate saran atau analisis
def generate_gemini_response(prompt):
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"

# App utama
st.title("Platform Pembelajaran Klinis Berbasis Streamlit dengan Integrasi Gemini API")

if not login():
    st.stop()

user_id = get_user_id(st.session_state.user)
role = st.session_state.role

# Sidebar navigasi
st.sidebar.title("Menu")
pages = [
    "Home",
    "1. Pembelajaran Klinis & Kasus",
    "2. Asesmen & Evaluasi",
    "3. Komunikasi & Kolaborasi",
    "4. Manajemen Konten",
    "5. Monitoring & Tracking",
    "6. Laboratorium Virtual/Simulasi",
    "7. Manajemen Pengguna",
    "8. Dukungan Teknis"
]
page = st.sidebar.selectbox("Pilih Kategori", pages)

if page == "Home":
    st.header("Selamat Datang di Platform Pembelajaran Klinis")
    st.write("Ini adalah aplikasi demo untuk platform pendidikan klinis dengan integrasi AI Gemini untuk analisis dan generasi konten. Pilih menu di sidebar untuk mengeksplorasi fitur.")

elif page == "1. Pembelajaran Klinis & Kasus":
    st.header("Fitur Pembelajaran Klinis & Kasus")
    subpage = st.selectbox("Pilih Sub Fitur", ["Diskusi Kasus", "Manajemen Tugas", "Dokumentasi Pembelajaran", "Pelaporan Klinis Digital"])
    
    if subpage == "Diskusi Kasus":
        st.subheader("Diskusi Kasus")
        case_title = st.text_input("Judul Kasus")
        case_desc = st.text_area("Deskripsi Kasus")
        if st.button("Buat Kasus Baru"):
            cursor.execute("INSERT INTO cases (title, description, user_id) VALUES (?, ?, ?)", (case_title, case_desc, user_id))
            conn.commit()
            st.success("Kasus dibuat!")
        
        st.write("Daftar Kasus:")
        cases = pd.read_sql("SELECT * FROM cases", conn)
        st.dataframe(cases)
        
        selected_case = st.selectbox("Pilih Kasus untuk Diskusi", cases['id'] if not cases.empty else [])
        if selected_case:
            comment = st.text_area("Tambah Komentar")
            if st.button("Kirim Komentar"):
                timestamp = datetime.now().isoformat()
                cursor.execute("INSERT INTO discussions (case_id, user_id, comment, timestamp) VALUES (?, ?, ?, ?)", (selected_case, user_id, comment, timestamp))
                conn.commit()
                st.success("Komentar dikirim!")
            
            discussions = pd.read_sql("SELECT * FROM discussions WHERE case_id=?", conn, params=(selected_case,))
            st.write("Diskusi:")
            st.dataframe(discussions)
            
            # Integrasi Gemini: Analisis kasus dengan AI
            if st.button("Analisis Kasus dengan Gemini AI"):
                cursor.execute("SELECT description FROM cases WHERE id=?", (selected_case,))
                desc = cursor.fetchone()[0]
                prompt = f"Analisis kasus klinis berikut: {desc}. Berikan saran diagnosis dan treatment."
                ai_response = generate_gemini_response(prompt)
                st.write("Analisis AI (Gemini):")
                st.write(ai_response)
    
    # (Subfitur lain tetap sama, bisa tambah integrasi Gemini di tempat lain jika diperlukan)
    elif subpage == "Manajemen Tugas":
        st.subheader("Manajemen Tugas")
        if role in ['dosen', 'admin']:
            ass_title = st.text_input("Judul Tugas")
            ass_desc = st.text_area("Deskripsi Tugas")
            due_date = st.date_input("Batas Waktu")
            if st.button("Buat Tugas Baru"):
                cursor.execute("INSERT INTO assignments (title, description, due_date, user_id) VALUES (?, ?, ?, ?)", (ass_title, ass_desc, str(due_date), user_id))
                conn.commit()
                st.success("Tugas dibuat!")
        
        assignments = pd.read_sql("SELECT * FROM assignments", conn)
        st.write("Daftar Tugas:")
        st.dataframe(assignments)
        
        selected_ass = st.selectbox("Pilih Tugas untuk Submit", assignments['id'] if not assignments.empty else [])
        if selected_ass:
            content = st.text_area("Isi Submission")
            if st.button("Submit Tugas"):
                timestamp = datetime.now().isoformat()
                cursor.execute("INSERT INTO submissions (assignment_id, user_id, content, timestamp) VALUES (?, ?, ?, ?)", (selected_ass, user_id, content, timestamp))
                conn.commit()
                st.success("Submission dikirim!")
            
            subs = pd.read_sql("SELECT * FROM submissions WHERE assignment_id=?", conn, params=(selected_ass,))
            st.write("Submissions:")
            st.dataframe(subs)
    
    elif subpage == "Dokumentasi Pembelajaran":
        st.subheader("Dokumentasi Pembelajaran")
        selected_case = st.selectbox("Pilih Kasus", pd.read_sql("SELECT id FROM cases", conn)['id'])
        log = st.text_area("Catatan Pembelajaran")
        if st.button("Simpan Log"):
            timestamp = datetime.now().isoformat()
            cursor.execute("INSERT INTO learning_logs (user_id, case_id, log, timestamp) VALUES (?, ?, ?, ?)", (user_id, selected_case, log, timestamp))
            conn.commit()
            st.success("Log disimpan!")
        
        logs = pd.read_sql("SELECT * FROM learning_logs WHERE user_id=?", conn, params=(user_id,))
        st.write("Log Pembelajaran:")
        st.dataframe(logs)
    
    elif subpage == "Pelaporan Klinis Digital":
        st.subheader("Pelaporan Klinis Digital")
        report_content = st.text_area("Isi Laporan")
        if st.button("Kirim Laporan"):
            timestamp = datetime.now().isoformat()
            cursor.execute("INSERT INTO reports (user_id, content, timestamp) VALUES (?, ?, ?)", (user_id, report_content, timestamp))
            conn.commit()
            st.success("Laporan dikirim!")
        
        reports = pd.read_sql("SELECT * FROM reports", conn)
        st.write("Daftar Laporan:")
        st.dataframe(reports)

# (Bagian lain dari kode tetap sama seperti sebelumnya, untuk menghindari panjang berlebih. Anda bisa copy-paste dari kode sebelumnya dan tambahkan integrasi Gemini di fitur relevan lainnya, misalnya generasi kuis di Asesmen.)

# Contoh tambahan integrasi di Fitur 2: Asesmen & Evaluasi
elif page == "2. Asesmen & Evaluasi":
    st.header("Fitur Asesmen & Evaluasi")
    subpage = st.selectbox("Pilih Sub Fitur", ["Asesmen Daring", "Kuis Interaktif", "Evaluasi Kompetensi"])
    
    if subpage == "Asesmen Daring":
        st.subheader("Asesmen Daring")
        if role in ['dosen', 'admin']:
            ass_title = st.text_input("Judul Asesmen")
            questions = st.text_area("Pertanyaan (JSON format: [{'q':'pertanyaan', 'a':'jawaban'}]")  # Sederhana
            if st.button("Buat Asesmen"):
                cursor.execute("INSERT INTO assessments (title, questions) VALUES (?, ?)", (ass_title, questions))
                conn.commit()
                st.success("Asesmen dibuat!")
        
        assessments = pd.read_sql("SELECT * FROM assessments", conn)
        st.write("Daftar Asesmen:")
        st.dataframe(assessments)
    
    elif subpage == "Kuis Interaktif":
        st.subheader("Kuis Interaktif")
        if role in ['dosen', 'admin']:
            quiz_title = st.text_input("Judul Kuis")
            topic = st.text_input("Topik untuk Generasi Kuis dengan Gemini")
            if st.button("Generate Kuis dengan Gemini"):
                prompt = f"Generate 5 soal kuis tentang {topic} dalam format JSON: [{'q':'pertanyaan', 'a':'jawaban'}]"
                questions = generate_gemini_response(prompt)
                st.write("Kuis Generated:")
                st.write(questions)
            
            questions_input = st.text_area("Pertanyaan (JSON format)", value=questions if 'questions' in locals() else "")
            if st.button("Buat Kuis"):
                cursor.execute("INSERT INTO quizzes (title, questions) VALUES (?, ?)", (quiz_title, questions_input))
                conn.commit()
                st.success("Kuis dibuat!")
        
        quizzes = pd.read_sql("SELECT * FROM quizzes", conn)
        st.write("Daftar Kuis:")
        st.dataframe(quizzes)
    
    elif subpage == "Evaluasi Kompetensi":
        st.subheader("Evaluasi Kompetensi")
        if role in ['dosen', 'admin']:
            user_to_eval = st.selectbox("Pilih Mahasiswa", pd.read_sql("SELECT username FROM users WHERE role='mahasiswa'", conn)['username'])
            competency = st.text_input("Kompetensi")
            score = st.number_input("Skor", 0, 100)
            eval_user_id = get_user_id(user_to_eval)
            if st.button("Simpan Evaluasi"):
                cursor.execute("INSERT INTO evaluations (user_id, competency, score) VALUES (?, ?, ?)", (eval_user_id, competency, score))
                conn.commit()
                st.success("Evaluasi disimpan!")
        
        evals = pd.read_sql("SELECT * FROM evaluations", conn)
        st.write("Daftar Evaluasi:")
        st.dataframe(evals)

# (Lanjutkan dengan bagian kode lainnya seperti sebelumnya...)
