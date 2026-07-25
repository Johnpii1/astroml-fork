from typing import Optional, Dict, Tuple, List
from astroml.search.embedders import get_embedder

class SemanticCache:
    def __init__(self, similarity_threshold: float = 0.85):
        self.threshold = similarity_threshold
        # Stores: query_text -> (response_text, embedding_vector)
        self.cache: Dict[str, Tuple[str, List[float]]] = {}

    def get(self, query: str) -> Optional[str]:
        if not self.cache:
            return None
            
        embedder = get_embedder()
        query_vec = embedder.generate_embedding(query)
        
        best_query = None
        best_score = -1.0
        
        for cached_query, (response, cached_vec) in self.cache.items():
            # Cosine similarity
            dot = sum(a * b for a, b in zip(query_vec, cached_vec))
            if dot > best_score:
                best_score = dot
                best_query = cached_query
                
        if best_score >= self.threshold and best_query:
            return self.cache[best_query][0]
        return None

    def set(self, query: str, response: str):
        embedder = get_embedder()
        vec = embedder.generate_embedding(query)
        self.cache[query] = (response, vec)
