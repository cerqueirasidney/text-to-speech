from flask import Flask, render_template, request, send_file, jsonify
import edge_tts
import asyncio
import os
import uuid

app = Flask(__name__)

UPLOAD_FOLDER = 'static'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

VOZES = {
    "Português (Brasil)": {
        "Masculinas": [
            ("pt-BR-AntonioNeural", "Antonio (Maduro, Natural)"),
            ("pt-BR-DonatoNeural", "Donato (Jovem)"),
            ("pt-BR-FabioNeural", "Fabio (Formal)")
        ],
        "Femininas": [
            ("pt-BR-FranciscaNeural", "Francisca (Natural)"),
            ("pt-BR-LeilaNeural", "Leila (Jovem)"),
            ("pt-BR-ValerioNeural", "Valerio (Suave)")
        ]
    },
    "English (US)": {
        "Male": [
            ("en-US-GuyNeural", "Guy (Natural)"),
            ("en-US-DavisNeural", "Davis (Young)"),
            ("en-US-TonyNeural", "Tony (Casual)")
        ],
        "Female": [
            ("en-US-JennyNeural", "Jenny (Natural)"),
            ("en-US-AriaNeural", "Aria (Young)"),
            ("en-US-SaraNeural", "Sara (Soft)")
        ]
    }
}

@app.route('/')
def index():
    return render_template('index.html', vozes=VOZES)

@app.route('/gerar_audio', methods=['POST'])
def gerar_audio():
    try:
        texto = request.form.get('texto')
        voz = request.form.get('voz')
        rate = request.form.get('rate', '+0%')
        pitch = request.form.get('pitch', '+0Hz')
        
        if not texto:
            return jsonify({'erro': 'Texto não fornecido'}), 400
        
        nome_arquivo = f"audio_{uuid.uuid4().hex[:8]}.mp3"
        caminho_completo = os.path.join(UPLOAD_FOLDER, nome_arquivo)
        
        async def criar_audio():
            communicate = edge_tts.Communicate(
                texto,
                voz,
                rate=rate,
                pitch=pitch
            )
            await communicate.save(caminho_completo)
        
        asyncio.run(criar_audio())
        
        return jsonify({'sucesso': True, 'arquivo': f"/static/{nome_arquivo}"})
    
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@app.route('/download/<nome_arquivo>')
def download(nome_arquivo):
    caminho = os.path.join(UPLOAD_FOLDER, nome_arquivo)
    if os.path.exists(caminho):
        return send_file(caminho, as_attachment=True)
    return jsonify({'erro': 'Arquivo não encontrado'}), 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
