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

# Configure logging
logger = logging.getLogger(__name__)

class ConversationOrchestrator:
    """
    Conversation orchestrator using Langchain to maintain context
    and structure the conversation flow with the lead efficiently.
    """
    
    def __init__(self, llm: BaseLLM, initial_context: Dict[str, Any] = None):
        """
        Initialize the conversation orchestrator.
        
        Args:
            llm (BaseLLM): Language model to use
            initial_context (Dict[str, Any], optional): Initial context if it exists
        """
        self.llm = llm
        self.lead_info = initial_context or {}
        self.memory = ConversationBufferMemory()
        self.conversation_stage = "introduccion"
        
        # Message history for tracking
        self.message_history = []
        
        # Important fields to capture (with priority)
        self.essential_fields = {
            "introduccion": ["nombre", "empresa"],
            "identificacion_necesidades": ["necesidades", "punto_dolor"],
            "calificacion": ["presupuesto", "plazo"],
            "propuesta": ["objeciones"],
            "cierre": ["interes_siguiente_paso"]
        }
        
        # Counter to manage stage transitions
        self.stage_message_count = 0
        
        # Specific counters for final stages
        self.propuesta_message_count = 0
        self.cierre_message_count = 0
        
        # Cache of extracted information to reduce LLM calls
        self.info_cache = {}
        
        # Last time information was extracted (for throttling)
        self.last_extraction_time = 0
        
        # Conversation ending state
        self.conversation_ending = False
        self.conversation_ended = False
        
        # Detect repetitive responses
        self.last_responses = []
        
        # Closing message counter for finalization
        self.closing_message_count = 0
    
    def get_stage_prompt(self) -> str:
        """
        Get the specific prompt for the current stage of the conversation
        focusing on essential fields.
        """
        # Priority missing fields for this stage
        missing_fields = [field for field in self.essential_fields.get(self.conversation_stage, []) 
                          if not self.lead_info.get(field)]
        
        # If we're ending the conversation, ignore missing fields
        if self.conversation_ending:
            return self._get_ending_prompt()
        
        # If we're detecting repetition in advanced stages, force progress
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
        Get the prompt to end the conversation clearly.
        """
        nombre = self.lead_info.get('nombre', 'el prospecto')
        
        if self.closing_message_count == 0:
            # First closing message (prepare farewell)
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
            # Final farewell message
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
        Detect if we're stuck repeating similar content in a stage.
        """
        # We need at least 3 responses to compare
        if len(self.last_responses) < 3:
            return False
        
        # Check the last 3 assistant responses
        last_three = self.last_responses[-3:]
        
        # Calculate content similarity (simple implementation)
        # In a more sophisticated implementation, cosine similarity or embeddings could be used
        similarity_count = 0
        for i in range(len(last_three)):
            for j in range(i+1, len(last_three)):
                # Compare lengths and some text fragments
                len_diff = abs(len(last_three[i]) - len(last_three[j])) / max(len(last_three[i]), len(last_three[j]))
                content_overlap = len(set(last_three[i].split()) & set(last_three[j].split())) / len(set(last_three[i].split()) | set(last_three[j].split()))
                
                if len_diff < 0.3 and content_overlap > 0.5:  # Similarity threshold
                    similarity_count += 1
        
        # If at least 2 pairs are similar, we consider we're stuck
        return similarity_count >= 2
    
    def advance_stage(self) -> bool:
        """
        Advance to the next stage of the conversation and reset counters.
        
        Returns:
            bool: True if advanced to a new stage, False if already at the last stage
        """
        stages = ["introduccion", "identificacion_necesidades", "calificacion", "propuesta", "cierre"]
        current_index = stages.index(self.conversation_stage)
        
        if current_index < len(stages) - 1:
            previous_stage = self.conversation_stage
            self.conversation_stage = stages[current_index + 1]
            self.stage_message_count = 0
            
            # Log stage advancement
            logger.info(f"Avanzando de etapa: {previous_stage} -> {self.conversation_stage}")
            
            # Reset specific counters
            if self.conversation_stage == "propuesta":
                self.propuesta_message_count = 0
            elif self.conversation_stage == "cierre":
                self.cierre_message_count = 0
                
            return True
        return False
    
    def start_ending_sequence(self) -> None:
        """
        Start the conversation ending sequence.
        """
        self.conversation_ending = True
        self.closing_message_count = 0
        logger.info("Iniciando secuencia de finalización de conversación")
    
    def should_advance_stage(self) -> bool:
        """
        Determine if we should advance to the next stage based on the information
        collected and the conversation dynamics.
        """
        self.stage_message_count += 1
        
        # Update specific counters
        if self.conversation_stage == "propuesta":
            self.propuesta_message_count += 1
        elif self.conversation_stage == "cierre":
            self.cierre_message_count += 1
        
        # If we're already in the ending sequence, don't advance further
        if self.conversation_ending or self.conversation_ended:
            return False
            
        # Check if we detect stagnation patterns
        if self._is_stuck_in_stage():
            logger.info(f"Detectado estancamiento en etapa: {self.conversation_stage}")
            
            # If we're stuck in proposal, force advancement to closing
            if self.conversation_stage == "propuesta":
                return True
            
            # If we're stuck in closing, start ending sequence
            if self.conversation_stage == "cierre":
                self.start_ending_sequence()
                return False
        
        # Optimized criteria for each stage
        if self.conversation_stage == "introduccion":
            # Advance if we have name and company OR after 3+ messages
            has_basic_info = bool(self.lead_info.get("nombre") and self.lead_info.get("empresa"))
            return has_basic_info or self.stage_message_count >= 3
            
        elif self.conversation_stage == "identificacion_necesidades":
            # Advance if we have any identified need OR after 4+ messages
            has_needs = bool(self.lead_info.get("necesidades") or self.lead_info.get("punto_dolor"))
            return has_needs or self.stage_message_count >= 4
            
        elif self.conversation_stage == "calificacion":
            # Advance if we have budget OR timeframe OR after 3+ messages
            has_qualification = bool(self.lead_info.get("presupuesto") or self.lead_info.get("plazo"))
            return has_qualification or self.stage_message_count >= 3
            
        elif self.conversation_stage == "propuesta":
            # Detect short user responses indicating interest
            user_brief_interest = False
            if len(self.message_history) >= 1 and self.message_history[-1]["role"] == "user":
                last_user_msg = self.message_history[-1]["content"].lower()
                # Detect short acceptance responses
                if len(last_user_msg.split()) <= 10 and any(term in last_user_msg for term in 
                                                        ["ok", "bien", "me gusta", "entiendo", "perfecto", 
                                                         "estoy interesado", "adelante", "me parece"]):
                    user_brief_interest = True
            
            # Advance after 3 messages or if the user shows explicit interest
            return self.propuesta_message_count >= 3 or user_brief_interest
            
        elif self.conversation_stage == "cierre":
            # Detect short user responses indicating acceptance
            user_acceptance = False
            if len(self.message_history) >= 1 and self.message_history[-1]["role"] == "user":
                last_user_msg = self.message_history[-1]["content"].lower()
                if len(last_user_msg.split()) <= 10 and any(term in last_user_msg for term in 
                                                        ["ok", "sí", "claro", "de acuerdo", "perfecto", 
                                                         "me parece bien", "excelente", "adelante"]):
                    user_acceptance = True
            
            # In closing, start farewell after 3 messages or clear acceptance
            if self.cierre_message_count >= 3 or user_acceptance:
                # We don't advance stage, but start ending sequence
                self.start_ending_sequence()
                return False
        
        return False
    
    def _should_end_conversation(self, user_input: str, response: str) -> bool:
        """
        Determine if the conversation should end based on the assistant's response.
        
        Args:
            user_input (str): Last user message
            response (str): Response generated by the assistant
            
        Returns:
            bool: True if the conversation should end
        """
        # If we're already in the ending process, check if the response contains
        # the key farewell phrase
        if self.conversation_ending:
            self.closing_message_count += 1
            
            # Check if the response contains the farewell phrase
            if "¡Hasta pronto! Ha sido un placer ayudarte hoy." in response:
                self.conversation_ended = True
                logger.info("Detectada frase clave de finalización")
                return True
                
            # If we have 2+ closing messages, force the end
            if self.closing_message_count >= 2:
                self.conversation_ended = True
                logger.info("Forzando finalización después de 2+ mensajes de cierre")
                return True
        
        # Detect signals in the user's message indicating a desire to end
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
        Extract information directly from the user's message using patterns
        to reduce calls to the LLM.
        
        Args:
            user_input (str): User message
            
        Returns:
            Dict[str, Any]: Extracted information
        """
        extracted = {}
        
        # Patterns for quick extraction (regex)
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
        Process a user message and generate an optimized response.
        
        Args:
            user_input (str): User message
            
        Returns:
            Dict[str, Any]: Response and metadata
        """
        # Add message to history
        self.message_history.append({"role": "user", "content": user_input})
        
        # Extract direct information (without LLM call)
        direct_extraction = self._extract_direct_info(user_input)
        if direct_extraction:
            self.lead_info.update(direct_extraction)
        
        # Build context for the prompt
        logger.debug(f"Procesando mensaje en etapa: {self.conversation_stage}")
        context = f"""
        Información del lead: {self.lead_info}
        Etapa actual: {self.conversation_stage}
        
        {self.get_stage_prompt()}
        """
        
        # Optimization: Use only the last messages for immediate context
        recent_history = self.message_history[-8:] if len(self.message_history) > 8 else self.message_history
        formatted_history = [{"role": msg["role"], "content": msg["content"]} for msg in recent_history]
        
        # Generate response
        start_time = time.time()
        response = self.llm.generate_with_history(formatted_history, context)
        generation_time = time.time() - start_time
        
        # Add response to history
        self.message_history.append({"role": "assistant", "content": response})
        
        # Save response for repetitive pattern detection
        self.last_responses.append(response)
        if len(self.last_responses) > 5:  # Keep only the last 5 responses
            self.last_responses.pop(0)
        
        # Check if the conversation should end
        should_end = self._should_end_conversation(user_input, response)
        
        # Extract lead information with throttling
        current_time = time.time()
        extracted_info = {}
        
        # Only do full extraction if:
        # 1. We're not in farewell phase
        # 2. At least 2 seconds have passed since the last extraction
        # 3. We're in a stage where extracting information is a priority
        # 4. We haven't extracted all the essential information for this stage
        if (not self.conversation_ending and
            current_time - self.last_extraction_time > 2 and 
            any(field not in self.lead_info for field in self.essential_fields.get(self.conversation_stage, []))):
            
            # Optimization: send only the last 5 message pairs (10 messages)
            recent_conversation = "\n".join([
                f"{'Usuario' if msg['role'] == 'user' else 'Asistente'}: {msg['content']}" 
                for msg in self.message_history[-10:]
            ])
            
            # CORRECTION: Don't pass the priority_fields parameter as it's not supported
            extracted_info = self.llm.extract_info(recent_conversation)
            self.last_extraction_time = current_time
            
            # Update lead information with priority to direct extraction
            if extracted_info:
                self._update_lead_info_safely(extracted_info, direct_extraction)
        
        # Evaluate if we should advance to the next stage (only if not ending)
        stage_changed = False
        if not self.conversation_ending and self.should_advance_stage():
            stage_changed = self.advance_stage()
        
        # Include timing information for performance analysis
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
    
    def _update_lead_info_safely(self, extracted_info: Dict[str, Any], direct_extraction: Dict[str, Any]) -> None:
        """
        Update lead information safely, preserving existing values
        and avoiding overwriting with empty or unspecified values.
        
        Args:
            extracted_info (Dict[str, Any]): Information extracted by the LLM
            direct_extraction (Dict[str, Any]): Information extracted directly by regex
        """
        for key, value in extracted_info.items():
            # If the key is already in direct_extraction, skip (already processed with priority)
            if key in direct_extraction:
                continue
                
            # Check if it's a significant value
            is_empty_value = value is None or (isinstance(value, str) and (
                not value.strip() or 
                value.lower() in ["no especificado", "desconocido", "n/a", "na", "none", "null", "no proporcionado", "no disponible"]
            ))
            
            # Don't overwrite existing values with empty values
            if key in self.lead_info and is_empty_value:
                continue
                
            # Only add significant values
            if not is_empty_value:
                self.lead_info[key] = value