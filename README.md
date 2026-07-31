# PawPal+: AI-Powered Pet Care Planning System

## Original Project
**PawPal (Module 2)** was a Streamlit-based pet care task tracker that allowed users to manually log daily activities (walks, feeding, grooming) for their pets.

## Extended System
PawPal+ transforms this into an **autonomous pet care orchestration agent** that:
- Automatically generates daily/weekly care plans using RAG-retrieved breed-specific guidelines
- Adapts plans based on pet age, health conditions, and owner constraints
- Explains reasoning with citations from veterinary sources
- Validates outputs through safety guardrails and confidence scoring

## Setup Instructions

1. Clone this repository:
   ```bash
   git clone https://github.com/priyanka-bh2/applied-ai-system-pawpal.git
   cd applied-ai-system-pawpal
   ```

2. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

3. Edit `.env` and add your Google AI API key

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Run the app:
   ```bash
   streamlit run app.py
   ```

## Architecture
See `diagrams/architecture.mmd` for the full system diagram.

## Features
- RAG-based retrieval for breed-specific care guidelines
- Agentic workflow using LangGraph for multi-step planning
- Validation guardrails and confidence scoring
- Structured testing and evaluation

