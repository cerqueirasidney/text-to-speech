import asyncio
import edge_tts

async def gerar_audio():
    texto = """No lançamento oblíquo, você sabe qual ângulo faz o objeto ir mais longe? Vamos testar! Primeiro, lançando a 30 graus, o objeto ganha velocidade e atinge uma certa distância. Agora, aumentando para 45 graus... Veja só! Ele atinge o alcance máximo! E se subirmos para 60 graus? O lançamento fica mais alto, mas cai exatamente no mesmo lugar dos 30 graus! Isso acontece porque ângulos complementares têm o mesmo alcance. Tudo isso é provado por essa equação, onde o alcance depende do seno do dobro do ângulo. Gostou dessa explicação? Já curte esse vídeo, segue o perfil e compartilha com quem precisa dominar Física!"""
    
    # Voz masculina brasileira (Antonio é muito natural)
    voz = "pt-BR-AntonioNeural"
    
    # Ajuste de velocidade e tom para soar mais humanizado
    # rate: velocidade (+0% é normal, +10% é mais rápido, -10% é mais lento)
    # volume: volume do áudio
    # pitch: tom da voz (+0Hz é normal, +5Hz é mais agudo, -5Hz é mais grave)
    communicate = edge_tts.Communicate(
        texto, 
        voz, 
        rate="+5%",      # Levemente mais rápido para soar natural
        volume="+0%",
        pitch="-2Hz"     # Levemente mais grave para soar mais masculino
    )
    
    # Salva o arquivo de áudio
    await communicate.save("lancamento_obliquo.mp3")
    print("✅ Áudio gerado com sucesso: lancamento_obliquo.mp3")

# Executa a função assíncrona
asyncio.run(gerar_audio())