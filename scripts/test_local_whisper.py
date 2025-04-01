# scripts/test_whisper_local.py
import os
import sys
import logging
from dotenv import load_dotenv
import argparse


# Asegurar que podemos importar desde app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configurar logging básico
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

from app.core.asr import WhisperASR

# Cargar variables de entorno
load_dotenv()

def main():
    parser = argparse.ArgumentParser(description='Probar la transcripción de audio con Whisper local')
    parser.add_argument('audio_file', help='Ruta al archivo de audio a transcribir')
    parser.add_argument('--language', default='es', help='Código de idioma (default: es)')
    parser.add_argument('--model', default='base', 
                        choices=['tiny', 'base', 'small', 'medium', 'large', 'turbo'],
                        help='Tamaño del modelo Whisper (default: base)')
    
    args = parser.parse_args()
    
    # Verificar que el archivo existe
    if not os.path.exists(args.audio_file):
        print(f"Error: El archivo {args.audio_file} no existe")
        return
    
    # Leer el archivo de audio
    with open(args.audio_file, 'rb') as f:
        audio_data = f.read()
    
    # Crear instancia de WhisperASR
    print(f"Inicializando Whisper con modelo {args.model}...")
    asr = WhisperASR(model_size=args.model)
    
    # Transcribir el audio
    print(f"Transcribiendo archivo: {args.audio_file}")
    result = asr.transcribe(audio_data, language=args.language)
    
    if result.get('success'):
        print("\nTranscripción exitosa:")
        print("-" * 50)
        print(result['text'])
        print("-" * 50)
        
        # Mostrar segmentos si existen
        if result.get('segments'):
            print("\nSegmentos:")
            for i, segment in enumerate(result['segments']):
                print(f"[{segment['start']:.1f}s -> {segment['end']:.1f}s]: {segment['text']}")
    else:
        print(f"\nError en la transcripción: {result.get('error')}")

if __name__ == "__main__":
    main()