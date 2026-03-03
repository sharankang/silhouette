# Silhouette
An AI-powered personal stylist that generates outfits from your wardrobe. Upload your clothes, describe a vibe, and get a styled look pulled from what you actually own.

## What it does

- **Wardrobe management** — upload clothing photos, auto-tag them by category, season, color and style using computer vision
- **Style Chat** — describe a mood, occasion, or aesthetic in natural language (or voice) and get a complete outfit suggestion with a styled explanation
- **Outfit history** — saved looks you can rate and revisit

## Tech stack

**Frontend**
- React + Tailwind CSS

**Backend**
- FastAPI
- LangGraph — stateful outfit generation pipeline
- ChromaDB — vector store for wardrobe items and fashion knowledge base
- CLIP (OpenAI ViT-B-32) — multimodal image + text embeddings
- Hybrid retrieval — BM25 + vector search with Reciprocal Rank Fusion
- HyDE + MultiQuery — retrieval augmentation strategies
- Whisper — voice input transcription
- Groq (llama-3.3-70b) — outfit selection and styling
- Ollama (llama3.2) — local fallback