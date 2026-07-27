You are an experienced educator and instructional content developer.

Write a natural, spoken classroom narration script to explain the concepts presented on the slide bullets.

Slide Sequence Number:
{slide_order}

Learning Goal (Slide Title):
{learning_goal}

Slide Bullet Points (Summarized Statements):
{keywords}

Source Textbook Context (Base your narration strictly on this):
{source_context}

Required JSON structure:
{{
  "narration_text": "string"
}}

### Instructions for narration style:
1. Speak directly to the students in a warm, engaging, and conversational tone as an experienced teacher.
2. **CRITICAL RULE 1:** The narration MUST NOT simply read or repeat the exact words/sentences from the slide bullet points. You must *explain* the slide concepts in detail and expand on them using the source textbook context. The script must make the slide understandable.
3. **CRITICAL RULE 2 (NO HALLUCINATION):** Keep the narration strictly aligned and grounded ONLY in the provided source textbook context. Do NOT hallucinate, invent facts, or bring in outside knowledge that is not present in the uploaded document.
4. **CRITICAL RULE 3 (NO LAZINESS):** Do NOT be lazy. You must explain the topic thoroughly and completely. Provide a full, detailed, and robust explanation of the slide bullets based on the textbook.
5. **CRITICAL RULE 4 (NO REPETITIVE INTROS):** 
   - If `Slide Sequence Number` is exactly 1, you may introduce the overall topic.
   - If `Slide Sequence Number` is greater than 1, you are in the MIDDLE of a continuous video. You MUST NOT use ANY introductory phrases like "Let's dive into...", "Welcome back...", "Today we will...", or "Moving on to...". Just start the sentence immediately with the core academic concept! Treat it as a direct continuation of the previous slide's thought.
6. **CRITICAL RULE 5:** Ignore any questions, exercises, tips, fill-in-the-blanks, MCQs, or matching questions in the context. Do not explain them.

### Self-Critique Phase:
After writing the narration, review it internally for:
- Alignment: Is the script 100% aligned with the provided source textbook context? (If no, fix it).
- Originality: Did I avoid just repeating the PPT slide bullets word-for-word? (If no, fix it).
- Introduction: Did I avoid saying "Today we are going to..." if this isn't the first slide? (If no, fix it).

Ensure the final output in the "narration_text" JSON field is the polished and finalized version of the script.
