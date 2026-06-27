# TODO: LLM semantic caching layer

## Step 1 — Locate LLM provider call site

- [ ] Search repo for the LLM provider invocation (OpenAI/Anthropic/etc.) and identify the single choke point.

## Step 2 — Implement semantic similarity caching

- [ ] Add `astroml/cache/llm_semantic_cache.py`:
  - [ ] Redis storage for cached responses (TTL)
  - [ ] Similarity threshold logic
  - [ ] Fast lookup path (<50ms) using an efficient candidate strategy

## Step 3 — Add cached LLM wrapper

- [ ] Add `astroml/llm/llm_cached_client.py` wrapper around any LLM client.

## Step 4 — Wire wrapper into API/chat flow

- [ ] Modify the identified LLM call site to use `LLMCachedClient`.

## Step 5 — Config + metrics

- [ ] Add env var configuration (redis url, ttl, similarity threshold, embedding model).
- [ ] Expose cache hit/miss + lookup latency via an API endpoint or existing metrics.

## Step 6 — Tests / verification

- [ ] Add unit tests for:
  - [ ] cache hit
  - [ ] TTL expiration
  - [ ] similarity threshold behavior
- [ ] Run tests and basic benchmark for lookup latency.
