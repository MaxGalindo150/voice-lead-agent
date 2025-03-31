import os
import sys
import logging
from dotenv import load_dotenv

# Asegurar que podemos importar desde app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configurar logging básico
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Cargar variables de entorno
load_dotenv()

from app.core.llm.factory import create_llm
from app import config

def test_simple_generation():
    """Prueba generación simple de texto."""
    print("\n=== Prueba de Generación Simple ===")
    
    # Crear LLM usando la factory
    llm = create_llm("openai")
    
    # Prompt de prueba
    prompt = "Hola, soy un posible cliente interesado en servicios de consultoría de software. ¿Qué ofrece tu empresa?"
    
    print(f"Prompt: {prompt}")
    print("\nGenerando respuesta...")
    
    # Generar respuesta
    response = llm.generate(prompt)
    
    print(f"\nRespuesta:\n{response}")
    
    return response

def test_conversation():
    """Prueba generación con historial de conversación."""
    print("\n=== Prueba de Conversación ===")
    
    # Crear LLM usando la factory
    llm = create_llm("openai")
    
    # Historial de conversación simulado
    history = [
        {"role": "user", "content": "Hola, me gustaría saber más sobre sus servicios de consultoría."},
        {"role": "assistant", "content": "¡Hola! Claro, estaré encantado de informarte sobre nuestros servicios de consultoría. Ofrecemos consultoría en desarrollo de software, transformación digital y optimización de procesos. ¿Hay algún área específica que te interese?"},
        {"role": "user", "content": "Me interesa principalmente el desarrollo de aplicaciones web."}
    ]
    
    # Nueva entrada del usuario
    user_input = "Trabajo para la empresa XYZ y necesitamos renovar nuestra plataforma de comercio electrónico."
    
    print("Historial:")
    for msg in history:
        prefix = "Usuario: " if msg["role"] == "user" else "Asistente: "
        print(f"{prefix}{msg['content']}")
    
    print(f"\nNueva entrada: {user_input}")
    print("\nGenerando respuesta...")
    
    # Generar respuesta con historial
    response = llm.generate_with_history(history, user_input)
    
    print(f"\nRespuesta:\n{response}")
    
    # Actualizar historial
    history.append({"role": "user", "content": user_input})
    history.append({"role": "assistant", "content": response})
    
    return history

def test_info_extraction():
    """Prueba extracción de información de una conversación."""
    print("\n=== Prueba de Extracción de Información ===")
    
    # Crear LLM usando la factory
    llm = create_llm("openai")
    
    # Conversación simulada
    conversation = """
    Usuario: Hola, me interesa conocer sus servicios de desarrollo de software.
    Asistente: ¡Hola! Por supuesto, estaré encantado de informarte sobre nuestros servicios de desarrollo. Ofrecemos desarrollo a medida para aplicaciones web, móviles y de escritorio. ¿Podría saber tu nombre y para qué empresa trabajas?
    Usuario: Me llamo Carlos Rodríguez y trabajo para TechSolutions.
    Asistente: Gracias, Carlos. ¿Qué cargo ocupas en TechSolutions y qué tipo de solución de software estás buscando?
    Usuario: Soy el Director de Tecnología. Buscamos un sistema para gestionar nuestro inventario y pedidos, ya que el actual está obsoleto. Nuestro presupuesto es de aproximadamente 50,000 euros y necesitaríamos tenerlo implementado en 4 meses.
    Asistente: Entiendo, Carlos. TechSolutions necesita un sistema de gestión de inventario y pedidos con un presupuesto de 50,000 euros y un plazo de 4 meses. ¿Hay alguna funcionalidad específica que consideres indispensable en este nuevo sistema?
    Usuario: Sí, necesitamos que se integre con nuestro ERP actual y que permita acceso desde dispositivos móviles.
    """
    
    print("Conversación:")
    print(conversation)
    print("\nExtrayendo información...")
    
    # Extraer información
    info = llm.extract_info(conversation)
    
    print("\nInformación extraída:")
    for key, value in info.items():
        print(f"- {key}: {value}")
    
    return info

if __name__ == "__main__":
    print(f"Usando configuración: LLM_MODE={config.LLM_MODE}, OPENAI_MODEL={config.OPENAI_MODEL}")
    
    try:
        # Pruebas
        test_simple_generation()
        history = test_conversation()
        info = test_info_extraction()
        
        print("\n=== Todas las pruebas completadas con éxito ===")
        
    except Exception as e:
        print(f"\n❌ Error durante las pruebas: {str(e)}")
        import traceback
        traceback.print_exc()