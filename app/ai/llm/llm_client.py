import os
import json
import time
from typing import Literal
from dotenv import load_dotenv
from google import genai
from google.genai import types
from groq import Groq
from ollama import Client as OllamaClient

load_dotenv()

Provider = Literal["groq", "gemini", "ollama"]


class LLMClient:
    def __init__(self, primary_provider: Provider = "gemini", fallback_providers: list[Provider] = None):
        self.primary_provider = primary_provider
        self.fallback_providers = fallback_providers or ["groq", "ollama"]
        
        # Initialize Groq client
        self.groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        
        # Initialize Gemini client
        self.gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        
        # Initialize Ollama client
        self.ollama_client = OllamaClient(host='http://localhost:11434')
        
        # Model configurations
        self.models = {
            "groq": "openai/gpt-oss-120b",
            "gemini": "gemini-3.8-flash",
            "ollama": "qwen3:8b"
        }

    def generate_content(
        self,
        prompt: str,
        response_mime_type: str = "application/json",
        max_retries: int = 3,
        base_delay: float = 2.0
    ) -> dict:
        """
        Generate content using primary provider with fallback to secondary.
        Implements exponential backoff for retries.
        """
        providers = [self.primary_provider] + self.fallback_providers
        print(f"[LLMClient] Starting generation with providers: {providers}")
        
        for provider in providers:
            model_name = self.models[provider]
            print(f"[LLMClient] Trying provider: {provider}, model: {model_name}")
            
            for attempt in range(max_retries):
                try:
                    print(f"[LLMClient] Attempt {attempt + 1}/{max_retries} for {provider}")
                    
                    if provider == "groq":
                        response = self._call_groq(prompt, model_name)
                    elif provider == "ollama":
                        response = self._call_ollama(prompt, model_name)
                    else:
                        response = self._call_gemini(prompt, model_name, response_mime_type)
                    
                    print(f"[LLMClient] Success with {provider}!")
                    return response
                    
                except Exception as e:
                    print(f"[LLMClient] {provider} attempt {attempt + 1} failed: {type(e).__name__}: {str(e)[:200]}")
                    
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)  # Exponential backoff
                        print(f"[LLMClient] Retrying in {delay} seconds...")
                        time.sleep(delay)
                    else:
                        print(f"[LLMClient] {provider} failed after {max_retries} attempts, trying next provider...")
                        break
        
        print(f"[LLMClient] All providers failed!")
        raise Exception(f"All providers failed after {max_retries} attempts each")

    def _call_groq(self, prompt: str, model: str) -> dict:
        """Call Groq API"""
        response = self.groq_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant. Return ONLY valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        return json.loads(content)

    def _call_gemini(self, prompt: str, model: str, response_mime_type: str) -> dict:
        """Call Gemini API"""
        response = self.gemini_client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type=response_mime_type,
            ),
        )
        
        return json.loads(response.text)

    def _call_ollama(self, prompt: str, model: str) -> dict:
        """Call Ollama API"""
        response = self.ollama_client.chat(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant. Return ONLY valid JSON."},
                {"role": "user", "content": prompt}
            ],
            format="json"
        )
        
        content = response["message"]["content"]
        return json.loads(content)


# Global client instance
llm_client = LLMClient(primary_provider="gemini", fallback_providers=["groq", "ollama"])
