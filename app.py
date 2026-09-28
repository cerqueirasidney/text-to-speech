from flask import Flask, render_template, request, send_file, jsonify
import edge_tts
import asyncio
import os
import uuid
import time

app = Flask(__name__)

# Configurar pasta para salvar áudios
UPLOAD_FOLDER = 'static'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Limpar arquivos com mais de 1 hora (para não encher o disco)
def limpar_arquivos_antigos():
    try:
        agora = time.time()
        for arquivo in os.listdir(UPLOAD_FOLDER):
            caminho = os.path.join(UPLOAD_FOLDER, arquivo)
            if os.path.isfile(caminho):
                if agora - os.path.getmtime(caminho) > 3600:  # 1 hora
                    os.remove(caminho)
    except:
        pass

# Lista completa de vozes disponíveis
VOZES = {
    "🇧🇷 Português (Brasil)": {
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
    "🇺🇸 English (US)": {
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
    },
    "🇪 Español (España)": {
        "Masculinas": [
            ("es-ES-AlvaroNeural", "Alvaro (Natural)"),
            ("es-ES-ArnauNeural", "Arnau (Jovem)")
        ],
        "Femininas": [
            ("es-ES-ElviraNeural", "Elvira (Natural)"),
            ("es-ES-AbrilNeural", "Abril (Jovem)")
        ]
    },
    "🇫🇷 Français (France)": {
        "Masculines": [
            ("fr-FR-HenriNeural", "Henri (Natural)"),
            ("fr-FR-ClaudeNeural", "Claude (Formal)")
        ],
        "Féminines": [
            ("fr-FR-DeniseNeural", "Denise (Natural)"),
            ("fr-FR-EloiseNeural", "Eloise (Jovem)")
        ]
    },
    "🇪 Deutsch (Germany)": {
        "Männlich": [
            ("de-DE-ConradNeural", "Conrad (Natural)"),
            ("de-DE-KillianNeural", "Killian (Jovem)")
        ],
        "Weiblich": [
            ("de-DE-KatjaNeural", "Katja (Natural)"),
            ("de-DE-AmalaNeural", "Amala (Suave)")
        ]
    }
}

@app.route('/')
def index():
    limpar_arquivos_antigos()
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
        
        # Função assíncrona com retry (tentar até 3 vezes)
        async def criar_audio_com_retry():
            max_tentativas = 3
            for tentativa in range(max_tentativas):
                try:
                    communicate = edge_tts.Communicate(
                        texto,
                        voz,
                        rate=rate,
                        pitch=pitch
                    )
                    await communicate.save(caminho_completo)
                    return True
                except Exception as e:
                    if tentativa < max_tentativas - 1:
                        await asyncio.sleep(2)  # Esperar 2 segundos antes de tentar de novo
                    else:
                        raise e
        
        asyncio.run(criar_audio_com_retry())
        
        return jsonify({
            'sucesso': True, 
            'arquivo': f"/static/{nome_arquivo}",
            'texto': texto[:50] + '...' if len(texto) > 50 else texto,
            'voz': voz
        })
    
    except Exception as e:
        erro_msg = str(e)
        # Mensagem mais amigável para o usuário
        if 'No audio was received' in erro_msg:
            erro_msg = 'Não foi possível gerar o áudio. Tente novamente em alguns segundos ou use outra voz.'
        return jsonify({'erro': erro_msg}), 500

@app.route('/download/<nome_arquivo>')
def download(nome_arquivo):
    caminho = os.path.join(UPLOAD_FOLDER, nome_arquivo)
    if os.path.exists(caminho):
        return send_file(caminho, as_attachment=True)
    return jsonify({'erro': 'Arquivo não encontrado'}), 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)