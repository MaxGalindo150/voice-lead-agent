# Voice Lead Agent

Un agente de inteligencia artificial basado en voz para la nutrición de leads, capaz de interactuar mediante reconocimiento y síntesis de voz para recopilar información relevante de prospectos.

## Instalación

### Prerrequisitos

- Python 3.10 o superior
- pip (gestor de paquetes de Python)
- Acceso a Internet para descargar dependencias y modelos
- Micrófono y altavoces para la interacción por voz

### Instrucciones de instalación

1. **Clonar el repositorio**

```bash
git clone https://github.com/tu-usuario/voice-lead-agent.git
cd voice-lead-agent
```

2. **Crear un entorno virtual (opcional pero recomendado)**

```bash
python -m venv venv

# En Windows
venv\Scripts\activate

# En macOS/Linux
source venv/bin/activate
```

3. **Instalar dependencias**

```bash
pip install -e .
```

5. **Configurar variables de entorno**

Crea un archivo `.env` en la raíz del proyecto con las siguientes variables (ajusta según tus credenciales), siguiendo el formato de ejemplo:

```
OPENAI_API_KEY=tu_clave_api_de_openai
```

6. **Iniciar la aplicación**

```bash
# Para la interfaz web con Streamlit
cd app
streamlit run ui/stramlit_app.py

## Solución de Problemas

### Problemas comunes

#### Error: "No module named 'openai'"

Asegúrate de haber instalado todas las dependencias correctamente:
```bash
pip install -r requirements.txt
```

#### Error al inicializar los modelos de ASR/TTS

- Verifica que tienes conexión a Internet para la descarga inicial de los modelos (Whisper).


#### Problemas de reconocimiento de voz

- Asegúrate de que tu micrófono está correctamente configurado y seleccionado como dispositivo de entrada.
- Habla claro y a un volumen moderado.
- Si estás en un entorno ruidoso, considera usar la opción de entrada de texto como alternativa temporal.

#### Consumo elevado de memoria

- Los modelos de lenguaje y ASR locales requieren una cantidad significativa de RAM. Si experimentas problemas de rendimiento:
  - Cierra otras aplicaciones para liberar memoria.
  - Edita `config.py` para usar modelos más ligeros (ajusta `MODEL_SIZE` a "small" o "base").


#### Errores de conexión con la base de datos

- Verifica la configuración en `app/db/base.py`.
- Asegúrate de que la base de datos está funcionando y es accesible.
- Para pruebas locales, puedes usar la base de datos en memoria configurando `USE_IN_MEMORY_DB=True` en tu `.env`.

### Problemas específicos para distintos sistemas operativos

#### Windows
- Si tienes problemas con PyAudio (necesario para entrada/salida de audio), instala primero las dependencias de compilación:
  ```bash
  pip install pipwin
  pipwin install pyaudio
  ```

#### macOS
- En caso de problemas con la síntesis de voz, instala portaudio:
  ```bash
  brew install portaudio
  pip install pyaudio
  ```
- Si no tienes Homebrew, instálalo desde [brew.sh](https://brew.sh/).

#### Linux
- Instala las dependencias necesarias para audio:
  ```bash
  # Para distribuciones basadas en Debian/Ubuntu
  sudo apt-get update
  sudo apt-get install python3-dev portaudio19-dev python3-pyaudio
  
  # Para distribuciones basadas en Fedora
  sudo dnf install python3-devel portaudio-devel python3-pyaudio
  ```

### Reportar problemas

Si encuentras algún problema no listado aquí, por favor crea un issue en el repositorio con la siguiente información:
- Sistema operativo y versión
- Versión de Python
- Descripción detallada del problema
- Pasos para reproducir el error
- Logs o mensajes de error (si están disponibles)