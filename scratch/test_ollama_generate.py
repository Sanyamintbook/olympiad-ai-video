import asyncio
import os
import sys

# Add app to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.config.settings import get_settings
from app.infrastructure.ai.providers.ollama_provider import OllamaProvider
from app.domain.models.understanding import Understanding

async def main():
    settings = get_settings()
    print(f"Ollama base URL: {settings.ollama_base_url}")
    print(f"Ollama model: {settings.default_model}")
    
    provider = OllamaProvider()
    
    prompt = """
    Identify the main topic, chapter title, major topics, subtopics, definitions, examples, activities, questions, learning objectives, and a concise summary.
    Use the exact chapter title and section headings from the source text.
    Do not replace source terms with synonyms.
    
    Source text:
    Chapter 3: Minerals and Power Resources
    A mineral is a naturally occurring inorganic substance. Quartz and granite are examples.
    """
    
    schema = Understanding.model_json_schema()
    
    print("\nCalling Ollama generate_structured...")
    try:
        res = await provider.generate_structured(prompt, schema)
        print("\nSUCCESS!")
        print("Result type:", type(res))
        print("Result dict:")
        import json
        print(json.dumps(res, indent=2))
    except Exception as e:
        print("\nFAILED!")
        print(f"{type(e).__name__}: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
