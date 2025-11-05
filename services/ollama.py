"""
Ollama Service - Local AI chat integration

Provides AI chat capabilities using Ollama, a local LLM runner.
Includes model validation and availability checking.

Learn more: https://ollama.ai
"""
import ollama


class OllamaService:
    """
    Service for interacting with local Ollama AI models.
    
    Handles model validation, availability checking, and chat requests.
    Designed to work on low-bandwidth mesh networks with concise responses.
    """
    
    def __init__(self, host, model):
        """
        Initialize Ollama service.
        
        Args:
            host: Ollama API URL (e.g., 'http://localhost:11434')
            model: Model name (e.g., 'llama3.2:3b')
        """
        self.host = host
        self.model = model
        self.client = None
        self._available = None
        
    def _ensure_client(self):
        """Lazy initialize the Ollama client"""
        if not self.client:
            self.client = ollama.Client(host=self.host)
    
    def is_available(self):
        """Check if Ollama is available and the model exists"""
        if self._available is not None:
            return self._available
            
        try:
            self._ensure_client()
            # List models to check if service is running
            models_response = self.client.list()
            
            # Extract model names from Model objects
            model_names = [m.model for m in models_response.models]
            
            # Check if our model is in the list
            model_found = self.model in model_names
            
            if not model_found:
                print(f"⚠️  Ollama model '{self.model}' not found. Available: {', '.join(model_names[:3])}")
                self._available = False
            else:
                self._available = True
                
            return self._available
            
        except Exception as e:
            print(f"⚠️  Ollama not available: {e}")
            self._available = False
            return False
    
    def chat(self, message, system_prompt=None):
        """Send a message to Ollama and get response"""
        if not self.is_available():
            return "❌ Ollama not available. Make sure it's running."
            
        try:
            self._ensure_client()
            
            messages = []
            if system_prompt:
                messages.append({'role': 'system', 'content': system_prompt})
            messages.append({'role': 'user', 'content': message})
            
            response = self.client.chat(
                model=self.model,
                messages=messages
            )
            
            return response['message']['content']
            
        except Exception as e:
            return f"❌ Ollama error: {e}"
