#!/usr/bin/env python3
"""
Script para probar la funcionalidad TTS (Text-to-Speech).
Genera audio a partir de texto y lo reproduce.
"""

import os
import argparse
import tempfile
import subprocess
import logging
from gtts import gTTS

# Configuración de logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleTTS:
    """Clase simple para síntesis de voz y reproducción."""
    
    def __init__(self, language="es"):
        """
        Inicializa el procesador TTS.
        
        Args:
            language (str): Código de idioma (default: es)
        """
        self.language = language
        logger.info(f"TTS inicializado con idioma: {language}")
    
    def synthesize_and_play(self, text, use_ffplay=True):
        """
        Sintetiza texto a voz y lo reproduce.
        
        Args:
            text (str): Texto a sintetizar
            use_ffplay (bool): Si True, usa ffplay para reproducir, sino intenta usar otro método
            
        Returns:
            bool: True si la síntesis y reproducción fue exitosa
        """
        if not text:
            logger.warning("No hay texto para sintetizar")
            return False
        
        try:
            # Crear un archivo temporal para el MP3
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
                mp3_filename = temp_file.name
            
            # Generar audio con gTTS
            logger.info(f"Generando audio para: '{text}'")
            tts = gTTS(text=text, lang=self.language, slow=False)
            tts.save(mp3_filename)
            
            # Verificar que el archivo se generó correctamente
            if not os.path.exists(mp3_filename) or os.path.getsize(mp3_filename) < 100:
                logger.error("Error al generar el audio con gTTS")
                return False
                
            logger.info(f"Audio generado: {mp3_filename} ({os.path.getsize(mp3_filename)} bytes)")
            
            # Reproducir el audio
            if use_ffplay:
                # Usando ffplay (parte de FFmpeg)
                logger.info("Reproduciendo audio con ffplay...")
                try:
                    subprocess.run(
                        ['ffplay', '-autoexit', '-nodisp', mp3_filename],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        check=True
                    )
                    logger.info("Audio reproducido correctamente")
                    return True
                except subprocess.CalledProcessError:
                    logger.error("Error al reproducir con ffplay")
                    # Intentar método alternativo si ffplay falla
                except FileNotFoundError:
                    logger.warning("ffplay no encontrado, intentando método alternativo")
                    # Continuar con método alternativo
            
            # Método alternativo usando mpg123 (si está instalado)
            try:
                logger.info("Intentando reproducir con mpg123...")
                subprocess.run(
                    ['mpg123', mp3_filename],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=True
                )
                logger.info("Audio reproducido correctamente con mpg123")
                return True
            except (subprocess.CalledProcessError, FileNotFoundError):
                logger.error("Error al reproducir con mpg123")
            
            # Si todo falla, dar instrucciones para reproducir manualmente
            logger.info(f"No se pudo reproducir automáticamente. El archivo está en: {mp3_filename}")
            print(f"\nNo se pudo reproducir el audio automáticamente.")
            print(f"El archivo MP3 se ha guardado en: {mp3_filename}")
            print(f"Puedes reproducirlo manualmente con cualquier reproductor de audio.")
            
            # No eliminar el archivo en este caso para que el usuario pueda reproducirlo
            return False
            
        except Exception as e:
            logger.error(f"Error en síntesis o reproducción: {e}")
            return False
        finally:
            # No eliminamos el archivo si no se pudo reproducir automáticamente
            pass
    
    def convert_to_wav_and_play(self, text):
        """
        Sintetiza texto a voz, convierte a WAV y reproduce.
        Este método usa FFmpeg para convertir de MP3 a WAV.
        
        Args:
            text (str): Texto a sintetizar
            
        Returns:
            bool: True si la síntesis y reproducción fue exitosa
        """
        if not text:
            logger.warning("No hay texto para sintetizar")
            return False
        
        try:
            # Crear archivos temporales para MP3 y WAV
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_mp3:
                mp3_filename = temp_mp3.name
            
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_wav:
                wav_filename = temp_wav.name
            
            # Generar audio MP3 con gTTS
            logger.info(f"Generando audio MP3 para: '{text}'")
            tts = gTTS(text=text, lang=self.language, slow=False)
            tts.save(mp3_filename)
            
            # Verificar que el archivo se generó correctamente
            if not os.path.exists(mp3_filename) or os.path.getsize(mp3_filename) < 100:
                logger.error("Error al generar el audio con gTTS")
                return False
                
            logger.info(f"Audio MP3 generado: {mp3_filename} ({os.path.getsize(mp3_filename)} bytes)")
            
            # Convertir MP3 a WAV usando ffmpeg
            logger.info("Convirtiendo MP3 a WAV...")
            cmd = [
                'ffmpeg', '-y', '-i', mp3_filename,
                '-acodec', 'pcm_s16le', '-ar', '44100', '-ac', '2',
                wav_filename
            ]
            
            process = subprocess.run(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True
            )
            
            if process.returncode != 0:
                logger.error(f"Error al convertir MP3 a WAV: {process.stderr}")
                return False
            
            logger.info(f"Audio WAV generado: {wav_filename} ({os.path.getsize(wav_filename)} bytes)")
            
            # Reproducir WAV usando ffplay
            logger.info("Reproduciendo audio WAV...")
            try:
                subprocess.run(
                    ['ffplay', '-autoexit', '-nodisp', wav_filename],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=True
                )
                logger.info("Audio WAV reproducido correctamente")
                return True
            except Exception as e:
                logger.error(f"Error al reproducir WAV: {e}")
                # No borramos el archivo para que el usuario pueda reproducirlo manualmente
                print(f"\nNo se pudo reproducir el audio automáticamente.")
                print(f"El archivo WAV se ha guardado en: {wav_filename}")
                print(f"Puedes reproducirlo manualmente con cualquier reproductor de audio.")
                return False
                
        except Exception as e:
            logger.error(f"Error en síntesis o reproducción: {e}")
            return False
        finally:
            # No eliminamos los archivos si no se pudo reproducir correctamente
            pass

def main():
    parser = argparse.ArgumentParser(description='Probar funcionalidad TTS')
    parser.add_argument('--text', type=str, default="Hola, esto es una prueba de síntesis de voz.",
                        help='Texto a sintetizar (default: mensaje de prueba)')
    parser.add_argument('--lang', type=str, default="es",
                        help='Código de idioma (default: es)')
    parser.add_argument('--wav', action='store_true',
                        help='Convertir a WAV antes de reproducir')
    parser.add_argument('--debug', action='store_true',
                        help='Activar modo debug con más información')
    
    args = parser.parse_args()
    
    # Configurar nivel de logging
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Crear instancia de TTS
    tts = SimpleTTS(language=args.lang)
    
    print(f"\nGenerando audio para: '{args.text}'")
    
    # Sintetizar y reproducir
    if args.wav:
        print("Usando método de conversión a WAV...")
        success = tts.convert_to_wav_and_play(args.text)
    else:
        print("Usando método directo con MP3...")
        success = tts.synthesize_and_play(args.text)
    
    if success:
        print("\n✓ Audio generado y reproducido correctamente.")
    else:
        print("\n✗ Hubo un problema al generar o reproducir el audio.")
        print("  Revisa los logs para más información.")

if __name__ == "__main__":
    main()