import asyncio
from app.infrastructure.ai.agents.content.metadata_extractor import MetadataExtractorAgent
from app.infrastructure.ai.agents.content.chunk_topic_extractor import ChunkTopicExtractorAgent
from app.infrastructure.ai.agents.content.topic_merger import TopicMergerAgent

async def test_content_understanding():
    print("=== Testing Content Understanding Micro-Agents ===")
    
    # 1. Test Metadata
    meta_agent = MetadataExtractorAgent()
    sample_text = "This chapter is about Minerals and Power Resources. A mineral is a naturally occurring substance. We will learn about coal and petroleum."
    print("\n1. Testing MetadataExtractorAgent...")
    metadata = await meta_agent.extract_metadata("Minerals Chapter", sample_text)
    print(f"Result: {metadata}")
    
    # 2. Test Chunk Extractor
    chunk_agent = ChunkTopicExtractorAgent()
    print("\n2. Testing ChunkTopicExtractorAgent...")
    topics = await chunk_agent.extract_topics(sample_text, 1)
    print(f"Result: {topics}")
    
    # 3. Test Merger
    merger_agent = TopicMergerAgent()
    print("\n3. Testing TopicMergerAgent...")
    raw = ["Mineral", "Coal", "Petroleum", "Mineral", "Exercise 1"]
    clean = merger_agent.merge_topics(raw)
    print(f"Result: {clean}")

if __name__ == "__main__":
    asyncio.run(test_content_understanding())
