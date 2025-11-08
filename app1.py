from flask import Flask, request, render_template, send_file
from io import BytesIO
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Protocol.KDF import scrypt
import base64, struct, textwrap
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm

app = Flask(__name__)

# ==== Konstanta & Parameter Enkripsi ====
MAGIC = b'ENCPDFv1'   # tanda pengenal unik di payload
SALT_SIZE = 16
NONCE_SIZE = 12
TAG_SIZE = 16
KEY_LEN = 32           # AES-256


# ==== Fungsi Bantu ====
def derive_key(password: str, salt: bytes) -> bytes:
    """Turunkan kunci AES dari password menggunakan KDF scrypt."""
    return scrypt(password.encode('utf-8'), salt, KEY_LEN, N=2**14, r=8, p=1)

def rot_custom_str(s: str) -> str:
    """Lakukan ROT47 terhadap semua karakter ASCII (33–126)."""
    result = []
    for ch in s:
        o = ord(ch)
        if 33 <= o <= 126:
            result.append(chr(33 + ((o - 33 + 47) % 94)))
        else:
            result.append(ch)
    return ''.join(result)

def xor_with_password(data: bytes, password: str) -> bytes:
    """XOR setiap byte dengan password (looping jika lebih pendek)."""
    key_bytes = password.encode('utf-8')
    out = bytearray(len(data))
    for i, b in enumerate(data):
        out[i] = b ^ key_bytes[i % len(key_bytes)]
    return bytes(out)


# ==== Header Handling ====
def make_header(salt: bytes, nonce: bytes, tag: bytes, filename: str) -> bytes:
    """Buat header metadata untuk payload terenkripsi."""
    fname_bytes = filename.encode('utf-8')
    return MAGIC + salt + nonce + tag + struct.pack('!H', len(fname_bytes)) + fname_bytes

def parse_header(stream: bytes):
    """Baca kembali header dari payload terenkripsi."""
    offset = 0
    magic = stream[offset:offset+8]; offset += 8
    if magic != MAGIC:
        raise ValueError("Signature MAGIC tidak cocok — bukan file terenkripsi.")
    salt = stream[offset:offset+SALT_SIZE]; offset += SALT_SIZE
    nonce = stream[offset:offset+NONCE_SIZE]; offset += NONCE_SIZE
    tag = stream[offset:offset+TAG_SIZE]; offset += TAG_SIZE
    fname_len = struct.unpack('!H', stream[offset:offset+2])[0]; offset += 2
    fname = stream[offset:offset+fname_len].decode('utf-8'); offset += fname_len
    rest = stream[offset:]
    return salt, nonce, tag, fname, rest


# ==== Fungsi Enkripsi ====
def encrypt_text_payload(plain_bytes: bytes, password: str, label: str) -> str:
    """
    Tahapan enkripsi isi PDF:
    - AES-GCM dengan key hasil scrypt(password)
    - Base64 -> ROT47 -> XOR password
    - Tambah header + encode base64 keseluruhan
    """
    salt = get_random_bytes(SALT_SIZE)
    key = derive_key(password, salt)
    nonce = get_random_bytes(NONCE_SIZE)
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    ciphertext, tag = cipher.encrypt_and_digest(plain_bytes)
    b64 = base64.b64encode(ciphertext).decode('ascii')
    rot = rot_custom_str(b64)
    xor_bytes = xor_with_password(rot.encode('utf-8'), password)
    header = make_header(salt, nonce, tag, label)
    payload = header + xor_bytes
    return base64.b64encode(payload).decode('ascii')


def decrypt_text_payload(final_b64_str: str, password: str) -> bytes:
    """Proses dekripsi sesuai urutan terbalik dari enkripsi."""
    payload = base64.b64decode(final_b64_str)
    salt, nonce, tag, label, xor_bytes = parse_header(payload)
    rot_bytes = xor_with_password(xor_bytes, password)
    rot_str = rot_bytes.decode('utf-8')
    b64_cipher = rot_custom_str(rot_str)
    ciphertext = base64.b64decode(b64_cipher)
    key = derive_key(password, salt)
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    return cipher.decrypt_and_verify(ciphertext, tag)


# ==== Fungsi Buat Halaman PDF ====
def make_overlay_pdf(w, h, text):
    """Buat halaman PDF berisi teks terenkripsi atau hasil dekripsi."""
    packet = BytesIO()
    c = canvas.Canvas(packet, pagesize=(w, h))
    c.setFont("Courier", 8)
    margin = 12 * mm
    usable_w = w - margin * 2
    lines = textwrap.wrap(text, width=max(40, int(usable_w / 5)))
    x, y = margin, h - margin
    for line in lines:
        if y < margin:
            c.showPage()
            c.setFont("Courier", 8)
            y = h - margin
        c.drawString(x, y, line)
        y -= 9
    c.save()
    packet.seek(0)
    return packet


# ==== ROUTES ====
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/encrypt', methods=['POST'])
def encrypt_route():
    """Upload PDF dan hasilkan PDF terenkripsi."""
    f = request.files.get('pdf_file')
    password = request.form.get('password', '')
    if not f or f.filename == '':
        return "⚠️ File PDF belum diupload", 400
    if password == '':
        return "⚠️ Password wajib diisi", 400

    pdf_in = PdfReader(f)
    writer = PdfWriter()
    for i, page in enumerate(pdf_in.pages):
        try:
            text = page.extract_text() or ""
        except:
            text = ""
        label = f"{f.filename}-page-{i+1}"
        enc_str = encrypt_text_payload(text.encode('utf-8'), password, label)
        media = page.mediabox
        overlay = make_overlay_pdf(float(media.width), float(media.height), enc_str)
        writer.add_page(PdfReader(overlay).pages[0])

    out = BytesIO()
    writer.write(out)
    out.seek(0)
    return send_file(out, as_attachment=True,
                     download_name=f.filename.replace('.pdf', '_encrypted.pdf'),
                     mimetype='application/pdf')


@app.route('/decrypt', methods=['POST'])
def decrypt_route():
    """Upload PDF terenkripsi dan hasilkan PDF teks asli."""
    f = request.files.get('pdf_file')  # sekarang pakai pdf_file, bukan enc_file
    password = request.form.get('password', '')
    if not f or f.filename == '':
        return "⚠️ File PDF belum diupload", 400
    if password == '':
        return "⚠️ Password wajib diisi", 400

    pdf_in = PdfReader(f)
    writer = PdfWriter()
    for i, page in enumerate(pdf_in.pages):
        try:
            payload = "".join((page.extract_text() or "").split())
        except:
            payload = ""
        if not payload:
            writer.add_page(page)
            continue
        try:
            plain_bytes = decrypt_text_payload(payload, password)
            plain_text = plain_bytes.decode('utf-8')
        except Exception as e:
            return f"❌ Dekripsi gagal di halaman {i+1}: {str(e)}", 400

        media = page.mediabox
        overlay = make_overlay_pdf(float(media.width), float(media.height), plain_text)
        writer.add_page(PdfReader(overlay).pages[0])

    out = BytesIO()
    writer.write(out)
    out.seek(0)
    return send_file(out, as_attachment=True,
                     download_name=f.filename.replace('_encrypted.pdf', '_decrypted.pdf'),
                     mimetype='application/pdf')


if __name__ == '__main__':
    app.run(debug=True, port=5000)
