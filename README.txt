
PDF Encryptor - Prototype (Flask)

Files:
- app.py
- templates/index.html
- static/style.css
- uploads/ (empty folder for runtime uploads)
- example.pdf (sample file to test)

Requirements:
  pip install flask pycryptodome

Run:
  python app.py
Then open http://127.0.0.1:5000 in your browser.

Notes:
- This prototype uses AES-GCM + ROT47 + XOR(password) as requested.
- Do NOT use for high-security secrets without audit.
