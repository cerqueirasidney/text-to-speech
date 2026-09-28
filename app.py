from flask import Flask, render_template, request, send_file, jsonify
import edge_tts
import os
import uuid
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
                    logger.info(f"Arquivo antigo removido: {arquivo}")
    except Exception as e:
        logger.error(f"Erro ao limpar arquivos: {e}")

# Apenas vozes que FUNCIONARAM no teste
VOZES_PERMITIDAS = [
    "pt-BR-AntonioNeural", "pt-BR-FranciscaNeural",
    "en-US-GuyNeural", "en-US-JennyNeural", "en-US-AndrewNeural",
    "en-US-ChristopherNeural", "en-US-EricNeural", "en-US-MichelleNeural",
    "en-US-RogerNeural", "en-US-SteffanNeural",
    "es-ES-AlvaroNeural", "es-ES-ElviraNeural",
    "fr-FR-HenriNeural", "fr-FR-DeniseNeural",
    "de-DE-ConradNeural", "de-DE-KatjaNeural"
]

FALLBACK_VOZES = {
    "en-US-GuyNeural": "en-US-JennyNeural",
    "en-US-JennyNeural": "en-US-GuyNeural",
    "en-US-AndrewNeural": "en-US-GuyNeural",
    "en-US-ChristopherNeural": "en-US-GuyNeural",
    "en-US-EricNeural": "en-US-GuyNeural",
    "en-US-MichelleNeural": "en-US-JennyNeural",
    "en-US-RogerNeural": "en-US-GuyNeural",
    "en-US-SteffanNeural": "en-US-GuyNeural",
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
            ("pt-BR-AntonioNeural", "Antonio (Maduro, Natural)")
        ],
        "Femininas": [
            ("pt-BR-FranciscaNeural", "Francisca (Natural)")
        ]
    },
    "English (US)": {
        "Male": [
            ("en-US-GuyNeural", "Guy (Natural)"),
            ("en-US-AndrewNeural", "Andrew"),
            ("en-US-ChristopherNeural", "Christopher"),
            ("en-US-EricNeural", "Eric"),
            ("en-US-RogerNeural", "Roger"),
            ("en-US-SteffanNeural", "Steffan")
        ],
        "Female": [
            ("en-US-JennyNeural", "Jenny (Natural)"),
            ("en-US-MichelleNeural", "Michelle")
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
        
        if not texto:
            return jsonify({'erro': 'Texto não fornecido'}), 400
        
        if not voz or voz not in VOZES_PERMITIDAS:
            logger.warning(f"Voz inválida recebida: {voz}. Usando Antonio como fallback.")
            voz = "pt-BR-AntonioNeural"
        
        nome_arquivo = f"audio_{uuid.uuid4().hex[:8]}.mp3"
        caminho_temp = os.path.join(UPLOAD_FOLDER, f"temp_{nome_arquivo}")
        caminho_final = os.path.join(UPLOAD_FOLDER, nome_arquivo)
        
        voz_usada = voz
        fallback_usado = False
        
        try:
            logger.info(f"Tentando gerar áudio com voz: {voz}")
            communicate = edge_tts.Communicate(texto, voz, rate=rate, pitch=pitch)
            communicate.save_sync(caminho_temp)
            
            if not os.path.exists(caminho_temp) or os.path.getsize(caminho_temp) == 0:
                raise Exception("Arquivo gerado está vazio ou não existe")
            
            logger.info(f"Áudio gerado com sucesso: {caminho_temp}")
            
        except Exception as e:
            erro_msg = str(e)
            logger.warning(f"Falha com voz {voz}: {erro_msg}")
            
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
                    if os.path.exists(caminho_temp):
                        os.remove(caminho_temp)
                    return jsonify({
                        'erro': f'Não foi possível gerar o áudio. Tente novamente em alguns segundos ou use outra voz. (Erro original: {erro_msg})'
                    }), 500
            else:
                if os.path.exists(caminho_temp):
                    os.remove(caminho_temp)
                return jsonify({
                    'erro': f'Não foi possível gerar o áudio. Tente novamente em alguns segundos. (Erro: {erro_msg})'
                }), 500
        
        os.rename(caminho_temp, caminho_final)
        logger.info(f"Arquivo renomeado: {caminho_final}")
        
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

@app.route('/testar_vozes')
def testar_vozes():
    todas_vozes = VOZES_PERMITIDAS
    
    resultados = []
    texto_teste = "Teste de voz."
    
    for voz in todas_vozes:
        try:
            communicate = edge_tts.Communicate(texto_teste, voz)
            arquivo_teste = f"static/test_{voz}.mp3"
            communicate.save_sync(arquivo_teste)
            
            if os.path.exists(arquivo_teste) and os.path.getsize(arquivo_teste) > 0:
                resultados.append((voz, "✅ FUNCIONOU", "success"))
                os.remove(arquivo_teste)
            else:
                resultados.append((voz, "⚠️ Arquivo vazio", "error"))
                
        except Exception as e:
            resultados.append((voz, f"❌ Erro: {str(e)[:80]}", "error"))
    
    html = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Teste de Vozes</title>
        <style>
            body {{ font-family: 'Segoe UI', Arial; padding: 40px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }}
            .container {{ background: white; padding: 30px; border-radius: 15px; max-width: 900px; margin: 0 auto; box-shadow: 0 10px 40px rgba(0,0,0,0.2); }}
            h1 {{ color: #667eea; margin-bottom: 20px; }}
            h2 {{ color: #333; margin-top: 30px; }}
            .success {{ background: #d4edda; padding: 12px; margin: 8px 0; border-radius: 8px; border-left: 4px solid #28a745; }}
            .error {{ background: #f8d7da; padding: 12px; margin: 8px 0; border-radius: 8px; border-left: 4px solid #dc3545; }}
            .resumo {{ background: #f8f9fa; padding: 20px; margin: 20px 0; border-radius: 10px; }}
            .resumo p {{ margin: 8px 0; font-size: 1.1em; }}
            .btn {{ display: inline-block; margin-top: 20px; padding: 12px 24px; background: #667eea; color: white; text-decoration: none; border-radius: 8px; font-weight: 600; }}
            .btn:hover {{ background: #764ba2; }}
            strong {{ color: #333; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1> Resultado do Teste de Vozes</h1>
            <div class="resumo">
                <h2>📊 Resumo:</h2>
                <p><strong>Total testado:</strong> {len(resultados)} vozes</p>
                <p><strong>✅ Funcionaram:</strong> {len([r for r in resultados if '✅' in r[1]])}</p>
                <p><strong> Falharam:</strong> {len([r for r in resultados if '❌' in r[1]])}</p>
            </div>
            <h2>📋 Resultados Detalhados:</h2>
    """
    
    for voz, status, classe in resultados:
        html += f'<div class="{classe}"><strong>{voz}</strong> — {status}</div>'
    
    html += """
            <a href="/" class="btn">← Voltar para o site</a>
        </div>
    </body>
    </html>
    """
    
    return html

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(debug=False, host='0.0.0.0', port=port)