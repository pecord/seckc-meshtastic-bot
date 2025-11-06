"""
LLM Service - AI chat integration via OpenAI-compatible API

Provides AI chat capabilities using any OpenAI-compatible endpoint,
including Ollama, OpenAI, Azure OpenAI, or other compatible services.
Includes availability checking for robust operation.

Compatible endpoints:
- Ollama (http://localhost:11434/v1/)
- OpenAI (https://api.openai.com/v1/)
- Azure OpenAI
- Any OpenAI-compatible API
"""
from openai import OpenAI


class LLMService:
    """
    Service for interacting with OpenAI-compatible LLM APIs.
    
    Handles availability checking and chat requests.
    Designed to work on low-bandwidth mesh networks with concise responses.
    """
    
    def __init__(self, base_url, model, api_key="ollama"):
        """
        Initialize LLM service.
        
        Args:
            base_url: OpenAI-compatible API base URL (e.g., 'http://localhost:11434/v1/')
            model: Model name (e.g., 'llama3.2:3b' for Ollama, 'gpt-4' for OpenAI)
            api_key: API key (defaults to 'ollama' for local Ollama, required for OpenAI)
        """
        self.base_url = base_url
        self.model = model
        self.api_key = api_key
        self.client = None
        self._available = None
        
    def _ensure_client(self):
        """Lazy initialize the OpenAI client"""
        if not self.client:
            self.client = OpenAI(
                base_url=self.base_url,
                api_key=self.api_key
            )
    
    def is_available(self):
        """Check if the LLM service is available"""
        if self._available is not None:
            return self._available
            
        try:
            self._ensure_client()
            # Try to list models to check if service is running
            # This works for most OpenAI-compatible endpoints
            try:
                models_response = self.client.models.list()
                model_ids = [m.id for m in models_response.data]
                
                # Check if our model is in the list (optional - some endpoints may not list all models)
                if model_ids and self.model not in model_ids:
                    print(f"⚠️  Model '{self.model}' not found in available models. Will attempt to use anyway.")
                    print(f"    Available: {', '.join(model_ids[:3])}")
            except Exception:
                # Some endpoints may not support model listing, that's okay
                print(f"ℹ️  Model listing not supported by endpoint, will use '{self.model}' directly")
            
            self._available = True
            return True
            
        except Exception as e:
            print(f"⚠️  LLM service not available: {e}")
            self._available = False
            return False
    
    def chat(self, message, system_prompt=None):
        """Send a message to the LLM and get response"""
        if not self.is_available():
            return "❌ LLM service not available. Check your configuration."
            
        try:
            self._ensure_client()
            
            messages = []
            if system_prompt:
                messages.append({'role': 'system', 'content': system_prompt})
            messages.append({'role': 'user', 'content': message})
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"❌ LLM error: {e}"
