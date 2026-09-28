from flask import Flask, render_template, request, send_file, jsonify
import edge_tts
import os
import uuid
import time
import logging

# Configurar logs detalhados
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

UPLOAD_FOLDER = 'static'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def limpar_arquivos_antigos():
    """Remove arquivos MP3 com mais de 1 hora"""
    try:
        agora = time.time()
        for arquivo in os.listdir(UPLOAD_FOLDER):
            caminho = os.path.join(UPLOAD_FOLDER, arquivo)
            if os.path.isfile(caminho):
                if agora - os.path.getmtime(caminho) > 3600:
                    os.remove(caminho)
                    logger.info(f"Arquivo antigo removido: {arquivo}")
    except Exception as e:
        logger.error(f"Erro ao limpar arquivos: {e}")

# Lista estrita de vozes permitidas (apenas as mais estáveis)
VOZES_PERMITIDAS = [
    "pt-BR-AntonioNeural", "pt-BR-DonatoNeural", 
    "pt-BR-FranciscaNeural", "pt-BR-LeilaNeural",
    "en-US-GuyNeural", "en-US-DavisNeural", 
    "en-US-JennyNeural", "en-US-AriaNeural",
    "es-ES-AlvaroNeural", "es-ES-ElviraNeural",
    "fr-FR-HenriNeural", "fr-FR-DeniseNeural",
    "de-DE-ConradNeural", "de-DE-KatjaNeural"
]

# Mapeamento de fallback: se uma voz falhar, usa esta
FALLBACK_VOZES = {
    "pt-BR-DonatoNeural": "pt-BR-AntonioNeural",
    "pt-BR-LeilaNeural": "pt-BR-FranciscaNeural",
    "en-US-DavisNeural": "en-US-GuyNeural",
    "en-US-AriaNeural": "en-US-JennyNeural",
    "es-ES-AlvaroNeural": "pt-BR-AntonioNeural",
    "es-ES-ElviraNeural": "pt-BR-FranciscaNeural",
    "fr-FR-HenriNeural": "pt-BR-AntonioNeural",
    "fr-FR-DeniseNeural": "pt-BR-FranciscaNeural",
    "de-DE-ConradNeural": "pt-BR-AntonioNeural",
    "de-DE-KatjaNeural": "pt-BR-FranciscaNeural"
}

VOZES = {
    "Português (Brasil)": {
        "Masculinas": [
            ("pt-BR-AntonioNeural", "Antonio (Maduro, Natural)"),
            ("pt-BR-DonatoNeural", "Donato (Jovem)")
        ],
        "Femininas": [
            ("pt-BR-FranciscaNeural", "Francisca (Natural)"),
            ("pt-BR-LeilaNeural", "Leila (Jovem)")
        ]
    },
    "English (US)": {
        "Male": [
            ("en-US-GuyNeural", "Guy (Natural)"),
            ("en-US-DavisNeural", "Davis (Young)")
        ],
        "Female": [
            ("en-US-JennyNeural", "Jenny (Natural)"),
            ("en-US-AriaNeural", "Aria (Young)")
        ]
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
        texto = request.form.get('texto', '').strip()
        voz = request.form.get('voz', '').strip()
        rate = request.form.get('rate', '+0%')
        pitch = request.form.get('pitch', '+0Hz')
        
        logger.info(f"Requisição recebida - Voz: {voz}, Rate: {rate}, Pitch: {pitch}")
        
        # Validação de dados
        if not texto:
            return jsonify({'erro': 'Texto não fornecido'}), 400
        
        if not voz or voz not in VOZES_PERMITIDAS:
            logger.warning(f"Voz inválida recebida: {voz}. Usando Antonio como fallback.")
            voz = "pt-BR-AntonioNeural"
        
        # Gerar nome único para o arquivo
        nome_arquivo = f"audio_{uuid.uuid4().hex[:8]}.mp3"
        caminho_temp = os.path.join(UPLOAD_FOLDER, f"temp_{nome_arquivo}")
        caminho_final = os.path.join(UPLOAD_FOLDER, nome_arquivo)
        
        # Tentar gerar o áudio com a voz solicitada
        voz_usada = voz
        fallback_usado = False
        
        try:
            logger.info(f"Tentando gerar áudio com voz: {voz}")
            
            # Usar API síncrona do edge-tts (save_sync)
            communicate = edge_tts.Communicate(texto, voz, rate=rate, pitch=pitch)
            communicate.save_sync(caminho_temp)
            
            # Verificar se o arquivo foi criado corretamente
            if not os.path.exists(caminho_temp) or os.path.getsize(caminho_temp) == 0:
                raise Exception("Arquivo gerado está vazio ou não existe")
            
            logger.info(f"Áudio gerado com sucesso: {caminho_temp}")
            
        except Exception as e:
            erro_msg = str(e)
            logger.warning(f"Falha com voz {voz}: {erro_msg}")
            
            # Tentar fallback se disponível
            voz_fallback = FALLBACK_VOZES.get(voz)
            
            if voz_fallback:
                logger.info(f"Tentando fallback para voz: {voz_fallback}")
                fallback_usado = True
                voz_usada = voz_fallback
                
                try:
                    communicate = edge_tts.Communicate(texto, voz_fallback, rate=rate, pitch=pitch)
                    communicate.save_sync(caminho_temp)
                    
                    if not os.path.exists(caminho_temp) or os.path.getsize(caminho_temp) == 0:
                        raise Exception("Arquivo de fallback está vazio")
                    
                    logger.info(f"Fallback funcionou com voz: {voz_fallback}")
                    
                except Exception as e2:
                    logger.error(f"Fallback também falhou: {str(e2)}")
                    # Limpar arquivo temporário se existir
                    if os.path.exists(caminho_temp):
                        os.remove(caminho_temp)
                    return jsonify({
                        'erro': f'Não foi possível gerar o áudio. Tente novamente em alguns segundos ou use outra voz. (Erro original: {erro_msg})'
                    }), 500
            else:
                # Sem fallback disponível
                if os.path.exists(caminho_temp):
                    os.remove(caminho_temp)
                return jsonify({
                    'erro': f'Não foi possível gerar o áudio. Tente novamente em alguns segundos. (Erro: {erro_msg})'
                }), 500
        
        # Renomear arquivo temporário para final (operação atômica)
        os.rename(caminho_temp, caminho_final)
        logger.info(f"Arquivo renomeado: {caminho_final}")
        
        # Montar mensagem de resposta
        mensagem_fallback = ""
        if fallback_usado:
            mensagem_fallback = f" A voz original ({voz.split('-')[-1].replace('Neural', '')}) estava indisponível. Áudio gerado com {voz_usada.split('-')[-1].replace('Neural', '')}."
        
        return jsonify({
            'sucesso': True, 
            'arquivo': f"/static/{nome_arquivo}",
            'texto': texto[:50] + '...' if len(texto) > 50 else texto,
            'voz': voz_usada,
            'mensagem': mensagem_fallback
        })
    
    except Exception as e:
        logger.error(f"Erro inesperado: {str(e)}", exc_info=True)
        return jsonify({'erro': f'Erro interno do servidor: {str(e)}'}), 500

@app.route('/download/<nome_arquivo>')
def download(nome_arquivo):
    caminho = os.path.join(UPLOAD_FOLDER, nome_arquivo)
    if os.path.exists(caminho):
        return send_file(caminho, as_attachment=True)
    return jsonify({'erro': 'Arquivo não encontrado'}), 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(debug=False, host='0.0.0.0', port=port)