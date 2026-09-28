from flask import Flask, render_template, request, send_file, jsonify
import edge_tts
import asyncio
import os
import uuid
import time

app = Flask(__name__)

UPLOAD_FOLDER = 'static'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def limpar_arquivos_antigos():
    try:
        agora = time.time()
        for arquivo in os.listdir(UPLOAD_FOLDER):
            caminho = os.path.join(UPLOAD_FOLDER, arquivo)
            if os.path.isfile(caminho):
                if agora - os.path.getmtime(caminho) > 3600:
                    os.remove(caminho)
    except:
        pass

# Lista estrita de vozes permitidas (apenas as estáveis)
VOZES_PERMITIDAS = [
    "pt-BR-AntonioNeural", "pt-BR-DonatoNeural", "pt-BR-FranciscaNeural", "pt-BR-LeilaNeural",
    "en-US-GuyNeural", "en-US-DavisNeural", "en-US-JennyNeural", "en-US-AriaNeural",
    "es-ES-AlvaroNeural", "es-ES-ElviraNeural",
    "fr-FR-HenriNeural", "fr-FR-DeniseNeural",
    "de-DE-ConradNeural", "de-DE-KatjaNeural"
]

VOZES = {
    "Português (Brasil)": {
        "Masculinas": [("pt-BR-AntonioNeural", "Antonio (Maduro, Natural)"), ("pt-BR-DonatoNeural", "Donato (Jovem)")],
        "Femininas": [("pt-BR-FranciscaNeural", "Francisca (Natural)"), ("pt-BR-LeilaNeural", "Leila (Jovem)")]
    },
    "English (US)": {
        "Male": [("en-US-GuyNeural", "Guy (Natural)"), ("en-US-DavisNeural", "Davis (Young)")],
        "Female": [("en-US-JennyNeural", "Jenny (Natural)"), ("en-US-AriaNeural", "Aria (Young)")]
    },
    "Español (España)": {
        "Masculinas": [("es-ES-AlvaroNeural", "Alvaro (Natural)")],
        "Femininas": [("es-ES-ElviraNeural", "Elvira (Natural)")]
    },
    "Français (France)": {
        "Masculines": [("fr-FR-HenriNeural", "Henri (Natural)")],
        "Féminines": [("fr-FR-DeniseNeural", "Denise (Natural)")]
    },
    "Deutsch (Germany)": {
        "Männlich": [("de-DE-ConradNeural", "Conrad (Natural)")],
        "Weiblich": [("de-DE-KatjaNeural", "Katja (Natural)")]
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
        
        if not texto or not voz:
            return jsonify({'erro': 'Dados incompletos'}), 400
        
        # SEGURANÇA: Se o navegador enviar uma voz inválida (ex: Fabio), força a Antonio
        if voz not in VOZES_PERMITIDAS:
            voz = "pt-BR-AntonioNeural"
        
        nome_arquivo = f"audio_{uuid.uuid4().hex[:8]}.mp3"
        caminho_completo = os.path.join(UPLOAD_FOLDER, nome_arquivo)
        
        # Função assíncrona segura para Flask
        def rodar_async():
            async def _gerar():
                max_tentativas = 3
                for tentativa in range(max_tentativas):
                    try:
                        communicate = edge_tts.Communicate(texto, voz, rate=rate, pitch=pitch)
                        await communicate.save(caminho_completo)
                        return True
                    except Exception as e:
                        if tentativa < max_tentativas - 1:
                            await asyncio.sleep(2)
                        else:
                            raise e
            
            # Cria um novo loop de eventos para evitar conflitos no Render
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(_gerar())
            finally:
                loop.close()

        rodar_async()
        
        return jsonify({
            'sucesso': True, 
            'arquivo': f"/static/{nome_arquivo}",
            'texto': texto[:50] + '...' if len(texto) > 50 else texto,
            'voz': voz
        })
    
    except Exception as e:
        return jsonify({'erro': f'Erro ao gerar áudio: {str(e)}'}), 500

@app.route('/download/<nome_arquivo>')
def download(nome_arquivo):
    caminho = os.path.join(UPLOAD_FOLDER, nome_arquivo)
    if os.path.exists(caminho):
        return send_file(caminho, as_attachment=True)
    return jsonify({'erro': 'Arquivo não encontrado'}), 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000)) # Render usa portas dinâmicas
    app.run(debug=False, host='0.0.0.0', port=port)