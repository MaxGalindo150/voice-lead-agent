# core/langchain_integration.py
from typing import Dict, List, Any, Optional
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain.schema import HumanMessage, AIMessage
import time
import re
import logging

from app.core.llm.base import BaseLLM
from app import config

# Configurar logging
logger = logging.getLogger(__name__)

class ConversationOrchestrator:
    """
    Orquestador de conversaciones usando Langchain para mantener el contexto
    y estructurar el flujo de la conversación con el lead de manera eficiente.
    """
    
    def __init__(self, llm: BaseLLM, initial_context: Dict[str, Any] = None):
        """
        Inicializa el orquestador de conversaciones.
        
        Args:
            llm (BaseLLM): Modelo de lenguaje a utilizar
            initial_context (Dict[str, Any], optional): Contexto inicial si existe
        """
        self.llm = llm
        self.lead_info = initial_context or {}
        self.memory = ConversationBufferMemory()
        self.conversation_stage = "introduccion"
        
        # Historial de mensajes para tracking
        self.message_history = []
        
        # Campos importantes para capturar (con prioridad)
        self.essential_fields = {
            "introduccion": ["nombre", "empresa"],
            "identificacion_necesidades": ["necesidades", "punto_dolor"],
            "calificacion": ["presupuesto", "plazo"],
            "propuesta": ["objeciones"],
            "cierre": ["interes_siguiente_paso"]
        }
        
        # Contador para manejar transiciones de etapa
        self.stage_message_count = 0
        
        # Contadores específicos para etapas finales
        self.propuesta_message_count = 0
        self.cierre_message_count = 0
        
        # Caché de información extraída para reducir llamadas al LLM
        self.info_cache = {}
        
        # Última vez que se extrajo información (para throttling)
        self.last_extraction_time = 0
        
        # Estado de finalización de la conversación
        self.conversation_ending = False
        self.conversation_ended = False
        
        # Detectar si hay respuestas repetitivas
        self.last_responses = []
        
        # Contador de mensajes de cierre para finalización
        self.closing_message_count = 0
    
    def get_stage_prompt(self) -> str:
        """
        Obtiene el prompt específico para la etapa actual de la conversación
        con enfoque en los campos esenciales.
        """
        # Campos faltantes prioritarios para esta etapa
        missing_fields = [field for field in self.essential_fields.get(self.conversation_stage, []) 
                          if not self.lead_info.get(field)]
        
        # Si estamos finalizando la conversación, ignorar campos faltantes
        if self.conversation_ending:
            return self._get_ending_prompt()
        
        # Si estamos detectando repetición en etapas avanzadas, forzar avance
        if self._is_stuck_in_stage() and self.conversation_stage in ["propuesta", "cierre"]:
            if self.conversation_stage == "propuesta":
                return """
                IMPORTANTE: Estás atascado en la etapa de propuesta y repitiendo contenido similar.
                
                Debes avanzar a la etapa de cierre ahora.
                
                Resume brevemente la propuesta de valor y PREGUNTA DIRECTAMENTE si el prospecto 
                está interesado en programar una demostración o una llamada con un especialista.
                
                Usa un enfoque decisivo y directo. Es momento de cerrar, no de seguir explicando beneficios.
                """
            elif self.conversation_stage == "cierre":
                self.conversation_ending = True
                return self._get_ending_prompt()
        
        prompts = {
            "introduccion": f"""
            Estás en la etapa de introducción como LeadBot. Tu objetivo es iniciar una conversación natural
            y conseguir el nombre del prospecto y su empresa sutilmente.
            
            {"Aún necesitas obtener: " + ", ".join(missing_fields) if missing_fields else "Ya tienes la información básica."}
            
            Mantén la conversación breve y fluida, evitando preguntas genéricas. Si ya sabes su nombre, úsalo.
            Limita tus respuestas a 1-2 oraciones para mantener el ritmo conversacional.
            """,
            
            "identificacion_necesidades": f"""
            Estás explorando las necesidades y puntos de dolor de {self.lead_info.get('nombre', 'el prospecto')} 
            de {self.lead_info.get('empresa', 'su empresa')}.
            
            {"Aún necesitas entender: " + ", ".join(missing_fields) if missing_fields else "Ya has identificado sus necesidades principales."}
            
            Usa preguntas dirigidas y específicas. Demuestra comprensión reformulando lo que exprese el prospecto.
            Limita tus respuestas a 2-3 oraciones para mantener el ritmo conversacional.
            """,
            
            "calificacion": f"""
            Estás calificando a {self.lead_info.get('nombre', 'el prospecto')} en función de su potencial.
            
            {"Aún necesitas obtener información sobre: " + ", ".join(missing_fields) if missing_fields else "Tienes suficiente información de calificación."}
            
            Aborda el tema del presupuesto/plazos de forma indirecta: "¿Qué inversión tienen contemplada?" o 
            "¿En qué horizonte temporal necesitarían implementar una solución?"
            Limita tus respuestas a 1-2 oraciones para mantener el ritmo conversacional.
            """,
            
            "propuesta": f"""
            Estás presentando cómo podemos ayudar a {self.lead_info.get('nombre', 'el prospecto')} 
            con sus necesidades específicas: {self.lead_info.get('necesidades', 'que has identificado')}.
            
            Este es el mensaje #{self.propuesta_message_count + 1} en la etapa de propuesta.
            
            Concéntrate en 1-2 beneficios directamente relacionados con su punto de dolor principal.
            Evita hablar de características técnicas y enfócate en resultados concretos.
            
            IMPORTANTE: Si este es tu tercer mensaje en propuesta o si el usuario ha respondido brevemente
            indicando interés o aceptación, debes prepararte para avanzar al cierre. Pregunta si le gustaría
            ver una demostración o hablar con un especialista.
            
            Limita tus respuestas a 2-3 oraciones para presentar ideas concisas y claras.
            """,
            
            "cierre": f"""
            Estás cerrando la conversación con {self.lead_info.get('nombre', 'el prospecto')}.
            
            Este es el mensaje #{self.cierre_message_count + 1} en la etapa de cierre.
            
            {"Aún necesitas confirmar el interés en un siguiente paso." if missing_fields else "Ya has confirmado su interés en seguir adelante."}
            
            Resume BREVEMENTE los puntos clave y sugiere UN paso concreto, como una demostración o reunión.
            Pregunta claramente si desea proceder con este siguiente paso.
            
            IMPORTANTE: Si este es tu tercer mensaje en cierre o si el usuario ha respondido brevemente
            indicando acuerdo, debes prepararte para finalizar la conversación formalmente. Propón un
            horario específico o pregunta por su disponibilidad para agendar la siguiente interacción. Después,
            prepara un mensaje de despedida claro y profesional.
            
            Mantén un tono cordial y seguro. Limita tu respuesta a 2-3 oraciones.
            """
        }
        
        return prompts.get(self.conversation_stage, prompts["introduccion"])
    
    def _get_ending_prompt(self) -> str:
        """
        Obtiene el prompt para finalizar la conversación de manera clara.
        """
        nombre = self.lead_info.get('nombre', 'el prospecto')
        
        if self.closing_message_count == 0:
            # Primer mensaje de cierre (preparar despedida)
            return f"""
            Es momento de finalizar la conversación con {nombre} de manera educada y profesional.
            
            Resume los puntos más importantes que has aprendido sobre sus necesidades y confirma
            el siguiente paso concretamente, indicando que un representante se pondrá en contacto
            para coordinar los detalles.
            
            Indícale claramente que vas a finalizar la conversación. Por ejemplo:
            "Para finalizar nuestra conversación de hoy, quisiera confirmar que..."
            
            Limita tu respuesta a 3-4 oraciones como máximo.
            """
        else:
            # Mensaje final de despedida explícita
            return f"""
            Este es tu mensaje final de despedida para {nombre}.
            
            Agradécele por su tiempo hoy y hazle saber que un representante se pondrá en contacto 
            con él pronto según los siguientes pasos acordados.
            
            ES MUY IMPORTANTE: Termina con la frase exacta "¡Hasta pronto! Ha sido un placer ayudarte hoy."
            para indicar el final formal de la conversación.
            
            Esta frase es clave para que el sistema sepa que la conversación ha terminado y pueda
            generar el resumen automáticamente.
            """
    
    def _is_stuck_in_stage(self) -> bool:
        """
        Detecta si estamos atascados repitiendo contenido similar en una etapa.
        """
        # Necesitamos al menos 3 respuestas para comparar
        if len(self.last_responses) < 3:
            return False
        
        # Verificar las últimas 3 respuestas del asistente
        last_three = self.last_responses[-3:]
        
        # Calcular similitud de contenido (implementación simple)
        # En una implementación más sofisticada se podría usar similitud coseno o embeddings
        similarity_count = 0
        for i in range(len(last_three)):
            for j in range(i+1, len(last_three)):
                # Comparar longitudes y algunos fragmentos de texto
                len_diff = abs(len(last_three[i]) - len(last_three[j])) / max(len(last_three[i]), len(last_three[j]))
                content_overlap = len(set(last_three[i].split()) & set(last_three[j].split())) / len(set(last_three[i].split()) | set(last_three[j].split()))
                
                if len_diff < 0.3 and content_overlap > 0.5:  # Umbral de similitud
                    similarity_count += 1
        
        # Si al menos 2 pares son similares, consideramos que estamos atascados
        return similarity_count >= 2
    
    def advance_stage(self) -> bool:
        """
        Avanza a la siguiente etapa de la conversación y reinicia contadores.
        
        Returns:
            bool: True si se avanzó a una nueva etapa, False si ya estaba en la última
        """
        stages = ["introduccion", "identificacion_necesidades", "calificacion", "propuesta", "cierre"]
        current_index = stages.index(self.conversation_stage)
        
        if current_index < len(stages) - 1:
            previous_stage = self.conversation_stage
            self.conversation_stage = stages[current_index + 1]
            self.stage_message_count = 0
            
            # Registrar avance de etapa en logs
            logger.info(f"Avanzando de etapa: {previous_stage} -> {self.conversation_stage}")
            
            # Reiniciar contadores específicos
            if self.conversation_stage == "propuesta":
                self.propuesta_message_count = 0
            elif self.conversation_stage == "cierre":
                self.cierre_message_count = 0
                
            return True
        return False
    
    def start_ending_sequence(self) -> None:
        """
        Inicia la secuencia de finalización de la conversación.
        """
        self.conversation_ending = True
        self.closing_message_count = 0
        logger.info("Iniciando secuencia de finalización de conversación")
    
    def should_advance_stage(self) -> bool:
        """
        Determina si se debe avanzar a la siguiente etapa basado en la información
        recopilada y la dinámica de la conversación.
        """
        self.stage_message_count += 1
        
        # Actualizar contadores específicos
        if self.conversation_stage == "propuesta":
            self.propuesta_message_count += 1
        elif self.conversation_stage == "cierre":
            self.cierre_message_count += 1
        
        # Si ya estamos en la secuencia de finalización, no avanzar más
        if self.conversation_ending or self.conversation_ended:
            return False
            
        # Verificar si detectamos patrones de estancamiento
        if self._is_stuck_in_stage():
            logger.info(f"Detectado estancamiento en etapa: {self.conversation_stage}")
            
            # Si estamos atascados en propuesta, forzar avance a cierre
            if self.conversation_stage == "propuesta":
                return True
            
            # Si estamos atascados en cierre, iniciar secuencia de finalización
            if self.conversation_stage == "cierre":
                self.start_ending_sequence()
                return False
        
        # Criterios optimizados para cada etapa
        if self.conversation_stage == "introduccion":
            # Avanzar si tenemos nombre y empresa O si llevamos 3+ mensajes
            has_basic_info = bool(self.lead_info.get("nombre") and self.lead_info.get("empresa"))
            return has_basic_info or self.stage_message_count >= 3
            
        elif self.conversation_stage == "identificacion_necesidades":
            # Avanzar si tenemos alguna necesidad identificada O si llevamos 4+ mensajes
            has_needs = bool(self.lead_info.get("necesidades") or self.lead_info.get("punto_dolor"))
            return has_needs or self.stage_message_count >= 4
            
        elif self.conversation_stage == "calificacion":
            # Avanzar si tenemos presupuesto O plazo O si llevamos 3+ mensajes
            has_qualification = bool(self.lead_info.get("presupuesto") or self.lead_info.get("plazo"))
            return has_qualification or self.stage_message_count >= 3
            
        elif self.conversation_stage == "propuesta":
            # Detectar respuestas cortas del usuario que indiquen interés
            user_brief_interest = False
            if len(self.message_history) >= 1 and self.message_history[-1]["role"] == "user":
                last_user_msg = self.message_history[-1]["content"].lower()
                # Detectar respuestas cortas de aceptación
                if len(last_user_msg.split()) <= 10 and any(term in last_user_msg for term in 
                                                        ["ok", "bien", "me gusta", "entiendo", "perfecto", 
                                                         "estoy interesado", "adelante", "me parece"]):
                    user_brief_interest = True
            
            # Avanzar después de 3 mensajes o si el usuario muestra interés explícito
            return self.propuesta_message_count >= 3 or user_brief_interest
            
        elif self.conversation_stage == "cierre":
            # Detectar respuestas cortas del usuario que indiquen aceptación
            user_acceptance = False
            if len(self.message_history) >= 1 and self.message_history[-1]["role"] == "user":
                last_user_msg = self.message_history[-1]["content"].lower()
                if len(last_user_msg.split()) <= 10 and any(term in last_user_msg for term in 
                                                        ["ok", "sí", "claro", "de acuerdo", "perfecto", 
                                                         "me parece bien", "excelente", "adelante"]):
                    user_acceptance = True
            
            # En cierre, iniciar despedida después de 3 mensajes o aceptación clara
            if self.cierre_message_count >= 3 or user_acceptance:
                # No avanzamos de etapa, sino que iniciamos secuencia de finalización
                self.start_ending_sequence()
                return False
        
        return False
    
    def _should_end_conversation(self, user_input: str, response: str) -> bool:
        """
        Determina si la conversación debe finalizar basado en la respuesta del asistente.
        
        Args:
            user_input (str): Último mensaje del usuario
            response (str): Respuesta generada por el asistente
            
        Returns:
            bool: True si la conversación debe finalizar
        """
        # Si ya estamos en proceso de finalización, verificar si la respuesta contiene
        # la frase clave de despedida
        if self.conversation_ending:
            self.closing_message_count += 1
            
            # Verificar si la respuesta contiene la frase de despedida
            if "¡Hasta pronto! Ha sido un placer ayudarte hoy." in response:
                self.conversation_ended = True
                logger.info("Detectada frase clave de finalización")
                return True
                
            # Si llevamos 2+ mensajes de cierre, forzar el fin
            if self.closing_message_count >= 2:
                self.conversation_ended = True
                logger.info("Forzando finalización después de 2+ mensajes de cierre")
                return True
        
        # Detectar señales en el mensaje del usuario que indiquen deseo de finalizar
        end_indicators = [
            "gracias por tu ayuda",
            "muchas gracias",
            "hasta luego",
            "adiós",
            "chao",
            "me tengo que ir",
            "tengo que irme",
            "hablamos después",
            "hablaremos después",
            "nos vemos",
            "hasta pronto"
        ]
        
        if any(indicator in user_input.lower() for indicator in end_indicators) and self.conversation_stage in ["propuesta", "cierre"]:
            logger.info(f"Detectada señal de finalización en mensaje del usuario: {user_input}")
            self.start_ending_sequence()
        
        return False
    
    def _extract_direct_info(self, user_input: str) -> Dict[str, Any]:
        """
        Extrae información directamente del mensaje del usuario usando patrones
        para reducir llamadas al LLM.
        
        Args:
            user_input (str): Mensaje del usuario
            
        Returns:
            Dict[str, Any]: Información extraída
        """
        extracted = {}
        
        # Patrones para extracción rápida (regex)
        patterns = {
            "nombre": r"(?:me llamo|soy|nombre es)[:\s]+([A-ZÁÉÍÓÚÜÑa-záéíóúüñ\s]+?)[\.,]",
            "empresa": r"(?:trabajo en|de la empresa|compañía|nuestra empresa es)[:\s]+([A-ZÁÉÍÓÚÜÑa-záéíóúüñ\s&\.,]+?)[\.,]",
            "email": r"\b([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b",
            "telefono": r"\b(\+?[0-9]{8,15})\b",
            "presupuesto": r"(?:presupuesto|invertir|gastar|inversión)[:\s]+([0-9.,]+\s*(?:mil|k|millones|M|USD|MXN|€|\$)?)",
            "plazo": r"(?:plazo|tiempo|necesitamos|para|en)[:\s]+([0-9]+\s*(?:días|semanas|meses|años))",
        }
        
        for field, pattern in patterns.items():
            if field in self.essential_fields.get(self.conversation_stage, []):
                matches = re.search(pattern, user_input, re.IGNORECASE)
                if matches:
                    extracted[field] = matches.group(1).strip()
        
        return extracted
    
    def process_message(self, user_input: str) -> Dict[str, Any]:
        """
        Procesa un mensaje del usuario y genera una respuesta optimizada.
        
        Args:
            user_input (str): Mensaje del usuario
            
        Returns:
            Dict[str, Any]: Respuesta y metadatos
        """
        # Añadir mensaje al historial
        self.message_history.append({"role": "user", "content": user_input})
        
        # Extraer información directa (sin llamada al LLM)
        direct_extraction = self._extract_direct_info(user_input)
        if direct_extraction:
            self.lead_info.update(direct_extraction)
        
        # Construir contexto para el prompt
        logger.debug(f"Procesando mensaje en etapa: {self.conversation_stage}")
        context = f"""
        Información del lead: {self.lead_info}
        Etapa actual: {self.conversation_stage}
        
        {self.get_stage_prompt()}
        """
        
        # Optimización: Usar sólo los últimos mensajes para el contexto inmediato
        recent_history = self.message_history[-8:] if len(self.message_history) > 8 else self.message_history
        formatted_history = [{"role": msg["role"], "content": msg["content"]} for msg in recent_history]
        
        # Generar respuesta
        start_time = time.time()
        response = self.llm.generate_with_history(formatted_history, context)
        generation_time = time.time() - start_time
        
        # Añadir respuesta al historial
        self.message_history.append({"role": "assistant", "content": response})
        
        # Guardar respuesta para detección de patrones repetitivos
        self.last_responses.append(response)
        if len(self.last_responses) > 5:  # Mantener solo las últimas 5 respuestas
            self.last_responses.pop(0)
        
        # Comprobar si la conversación debe finalizar
        should_end = self._should_end_conversation(user_input, response)
        
        # Extraer información del lead con throttling
        current_time = time.time()
        extracted_info = {}
        
        # Solo hacer extracción completa si:
        # 1. No estamos en fase de despedida
        # 2. Han pasado al menos 2 segundos desde la última extracción
        # 3. Estamos en una etapa donde es prioritario extraer información
        # 4. No hemos extraído toda la información esencial para esta etapa
        if (not self.conversation_ending and
            current_time - self.last_extraction_time > 2 and 
            any(field not in self.lead_info for field in self.essential_fields.get(self.conversation_stage, []))):
            
            # Optimización: enviar solo los últimos 5 pares de mensajes (10 mensajes)
            recent_conversation = "\n".join([
                f"{'Usuario' if msg['role'] == 'user' else 'Asistente'}: {msg['content']}" 
                for msg in self.message_history[-10:]
            ])
            
            # CORRECCIÓN: No pasar el parámetro priority_fields que no está soportado
            extracted_info = self.llm.extract_info(recent_conversation)
            self.last_extraction_time = current_time
            
            # Actualizar información del lead con prioridad a la extracción directa
            if extracted_info:
                for key, value in extracted_info.items():
                    if key not in direct_extraction:  # La extracción directa tiene prioridad
                        self.lead_info[key] = value
        
        # Evaluar si se debe avanzar a la siguiente etapa (solo si no estamos finalizando)
        stage_changed = False
        if not self.conversation_ending and self.should_advance_stage():
            stage_changed = self.advance_stage()
        
        # Incluir información sobre tiempos para análisis de rendimiento
        return {
            "response": response,
            "lead_info": self.lead_info,
            "stage": self.conversation_stage,
            "stage_changed": stage_changed,
            "extracted_info": {**direct_extraction, **extracted_info},
            "response_time": generation_time,
            "conversation_ending": self.conversation_ending,
            "conversation_ended": self.conversation_ended
        }