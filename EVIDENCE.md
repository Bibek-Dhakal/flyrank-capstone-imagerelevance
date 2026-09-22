# Evidence Log

Paste proofs here for each requirement as they are completed. Claims without evidence score as not done.

## AI Processing

- [ ] Vision model produces structured output validated against a schema; invalid responses are never trusted.
  > *Proof goes here...*
- [ ] Low-confidence classifications are flagged instead of accepted.
  > *Proof goes here...*
- [ ] Images are processed through a batch background job with retries.
  > *Proof goes here...*
- [ ] Vision and embedding costs are tracked per call.
  > *Proof goes here...*

## Matching System

- [ ] Image and post embeddings are stored; posts return ranked image suggestions.
  > *Proof goes here...*
- [ ] Semantic matching works for equivalent concepts — "red fox" matches "Vulpes vulpes".
  > *Proof goes here...*

## Safety Layer

- [ ] The mismatch guard rejects incorrect recommendations — the wolf-on-a-fox-post scenario provably fails.
  > *Proof goes here...*
- [ ] Rejections include a human-readable explanation.
  > *Proof goes here...*
- [ ] When no image clears the bar, the system answers "no confident match" with reasons.
  > *Proof goes here...*

## Backend

- [ ] Database models for images, tags, embeddings, posts, suggestions, approvals/rejections — with the required
  indexes.
  > *Proof goes here...*
- [ ] API endpoints validated; the review workflow (approve / reject / inspect why) exists.
  > *Proof goes here...*

## Quality & Documentation

- [ ] A small labeled evaluation dataset measures top-1 precision — the number is in your README.
  > *Proof goes here...*
- [x] README with architecture explanation and diagram; the required files from Section 11 present.
  > **Proof**: See `README.md`, `capstone.yaml`, `EVIDENCE.md`, and `BUILDLOG.md`.
