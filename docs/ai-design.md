# PocketSmart AI - GenAI Design & Prompt Strategy

## AI Role Definition
Gemini acts as an intelligent budget advisory consultant and visual stylist:
- Analyzes unstructured user preferences (e.g., style, guest priorities, vibes).
- Proposes categorical weights.
- Generates contextual explanations for each financial decision.
- Performs computer vision analysis on uploaded jewelry outfits (dominant colors, formality, neckline compatibility).

## Failure Fallback Mechanism
- If the Gemini API key is missing or fails due to network or quota limitations, the system automatically uses a deterministic rule-based allocation algorithm.
- The user is notified via an alert banner without blocking plan generation.
