import asyncio
import os
import sys

from app.infrastructure.ai.agents.content.chunk_topic_extractor import ChunkTopicExtractorAgent

async def main():
    text = """Iron is an important mineral in this era of industrialisation. From a safety pin to a giant ship, everything is made of iron. In fact factory machines, on which all industrial output depends, are made from this strong and sturdy metal. Iron is extracted from iron ore. There are four types of iron ores – Haematite, Magnetite, Limonite, and Pyrite. Haematite is the best quality ore as it has 70% iron. The United States has the richest reserves of iron ore followed by Russia, China, and Sweden. India also has rich reserves of iron."""
    agent = ChunkTopicExtractorAgent()
    topics = await agent.extract_topics(text, 1)
    print("Topics extracted:", topics)

if __name__ == "__main__":
    asyncio.run(main())
