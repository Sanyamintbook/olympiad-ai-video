from app.infrastructure.ai.prompts.loader import PromptLoader

def test_prompts():
    loader = PromptLoader()
    
    # Audience profiler
    ap = loader.load("audience_profiler")
    ap.format(chapter_title="A", main_topic="B", major_topics="C", learning_objectives="D")
    
    # Unit Goal
    ug = loader.load("unit_goal_generator")
    ug.format(subtopic="A", main_topic="B")
    
    # Unit Content
    uc = loader.load("unit_content_generator")
    uc.format(subtopic="A", learning_goal="B", definitions="C", raw_text="D")
    
    # Tone refiner
    tr = loader.load("tone_refiner")
    tr.format(learning_goal="A", keywords="B", source_context="C")
    
    # Validator
    v = loader.load("validator")
    v.format(learning_goal="A", bullet_sentences="B", source_refs="C", generated_narration="D")
    
    print("ALL PROMPTS COMPILED SUCCESSFULLY WITH CONTEXT.")

if __name__ == "__main__":
    test_prompts()
