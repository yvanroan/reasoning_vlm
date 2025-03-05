Project inspired by my G, claude 3.7 Sonnet

# Reasoning VLM( RAG for image understanding)

## Intro
the goal is to build an AI system that doesn't just label objects in images (e.g: "there's a cup") but understands and explains meaningful relationships between objects (e.g: "the cup is balancing precariously on the edge of the table, suggesting someone might have placed it there hastily").
Core Capabilities To Develop

**Scene Understanding:** Identifies not just objects but meaningful situations

**Counterfactual Reasoning:** Can answer "what if" questions about the scene

**Anomaly Detection:** Identifies unusual or important relationships

**Visual Chain-of-Thought:** Shows explicit reasoning steps from visual input to conclusions

**Interactive Reasoning:** Can have a dialogue about visual content with increasingly sophisticated understanding


## Example

**Image:** A coffee mug placed precariously on the edge of a desk with papers scattered around

**Standard Multimodal LLM Response:**

"The image shows a white ceramic coffee mug positioned on the edge of a wooden desk. There are several papers and documents scattered across the desk surface. The mug appears to be full."

**Enhanced Visual Reasoning System:**

"The coffee mug is positioned unusually - it's placed at the edge of the desk rather than in a stable central position (this occurs in only 3% of similar desk scenes in my database). The scattered papers suggest interrupted work, and the mug's precarious position indicates the person likely placed it down hastily. Based on similar scenes, this arrangement suggests the person was likely called away unexpectedly during work and may return shortly. The mug's position creates a risk of spilling, which would damage the papers below - an atypical risk situation compared to normal desk arrangements I've analyzed."

**The key differences:**

- Identification of what's unusual based on comparison to similar scenes

- Statistical context from database of images

- Temporal reasoning about what happened before and might happen after

- Risk assessment based on learned patterns of object interactions

- Inferences about human behavior that caused this arrangement


it system doesn't just see what's there - it understands what's unusual, risky, or indicative of certain human behaviors based on comparative analysis.

## 2D t-SNE Visualization of Image Embeddings

![output from visualizer.py](./asset_timestamp/mar_5.png)

## Setup

1. Copy `server/prompts.template.py` to `server/prompts.py`
2. Edit `prompts.py` with your actual prompts
3. The file is gitignored so your prompts remain private

n.b: The prompts shared in this project are simplified and do not reflect the exact ones used to achieve the results. These specific prompts will be shared at a later time.