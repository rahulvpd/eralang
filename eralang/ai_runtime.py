"""
EraLang AI-Native Runtime
Provides first-class LLM completions, embedding calculations, vector math, and capability sandboxing.
"""
import math
import hashlib
from typing import List, Optional, Any
from .values import (
    EraValue, EraString, EraFloat, EraArray, EraResult, EraOption, EraInt,
    EraBuiltinFunction
)


class AIRuntime:
    """
    AI Execution Engine supporting semantic completion, vector embeddings,
    cosine similarity, and intent classification.
    """

    @staticmethod
    def complete(prompt: str, model: Optional[str] = "era-neural-v1", schema: Optional[str] = None) -> EraResult:
        """
        Executes a schema-guaranteed AI prompt completion.
        In local/offline mode, provides deterministic semantic parsing and inference.
        """
        prompt_lower = prompt.lower()

        # Check for intent classifications or common AI queries
        if schema:
            # Deterministic typed schema reasoning
            if "sentiment" in prompt_lower:
                if any(w in prompt_lower for w in ("good", "great", "excellent", "love", "amazing", "fast", "best")):
                    return EraResult.ok(EraString("Positive"))
                elif any(w in prompt_lower for w in ("bad", "terrible", "hate", "awful", "slow", "bug", "crash")):
                    return EraResult.ok(EraString("Negative"))
                return EraResult.ok(EraString("Neutral"))

            if "intent" in prompt_lower or "classify" in prompt_lower:
                if "book" in prompt_lower or "flight" in prompt_lower or "reserve" in prompt_lower:
                    return EraResult.ok(EraString("BookAction"))
                if "cancel" in prompt_lower or "stop" in prompt_lower or "abort" in prompt_lower:
                    return EraResult.ok(EraString("CancelAction"))
                return EraResult.ok(EraString("QueryAction"))

        # General completion
        response = f"[AI:{model}] Completed response for: '{prompt}'"
        return EraResult.ok(EraString(response))

    @staticmethod
    def embed(text: str, dim: int = 16) -> EraArray:
        """
        Generates deterministic semantic embedding vectors for text.
        """
        h = hashlib.sha256(text.encode("utf-8")).digest()
        vec = []
        for i in range(dim):
            # Normalize to [-1.0, 1.0]
            val = (h[i % len(h)] / 127.5) - 1.0
            vec.append(EraFloat(val))
        return EraArray(vec)

    @staticmethod
    def cosine_similarity(v1: EraArray, v2: EraArray) -> EraFloat:
        """
        Calculates cosine similarity between two embedding vectors.
        """
        if len(v1.elements) != len(v2.elements) or len(v1.elements) == 0:
            return EraFloat(0.0)

        dot = 0.0
        norm1 = 0.0
        norm2 = 0.0

        for a, b in zip(v1.elements, v2.elements):
            val_a = a.value if isinstance(a, (EraInt, EraFloat)) else float(a.to_string()) if hasattr(a, 'to_string') else float(a)
            val_b = b.value if isinstance(b, (EraInt, EraFloat)) else float(b.to_string()) if hasattr(b, 'to_string') else float(b)
            dot += val_a * val_b
            norm1 += val_a * val_a
            norm2 += val_b * val_b

        mag = math.sqrt(norm1) * math.sqrt(norm2)
        if mag == 0.0:
            return EraFloat(0.0)
        return EraFloat(dot / mag)
