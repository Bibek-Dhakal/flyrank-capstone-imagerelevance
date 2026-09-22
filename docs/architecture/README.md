# Architecture Documentation

This directory contains technical design documents and diagrams.

- **Main Architecture Sketch:** See the root `README.md` for the Phase 1 layer sketch.
- **AI Agent Tooling:** All interaction with LLMs (Gemini / Ollama) is facilitated via `LiteLLM` utilizing strict
  asynchronous `acompletion()` calls.
