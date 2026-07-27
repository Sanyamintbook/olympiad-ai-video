import os
import pickle
from typing import List
import faiss
import numpy as np
import httpx
from loguru import logger
from app.config.settings import get_settings

class LocalVectorStore:
    def __init__(self, dimension: int = 768):
        settings = get_settings()
        self.base_url = settings.ollama_base_url.rstrip("/")
        # Use the model from settings instead of hardcoding
        self.model = settings.ollama_embedding_model or "nomic-embed-text"
        self.dimension = None
        self.index = None
        self.chunks: List[str] = []

    def _ensure_model_exists(self) -> None:
        """Checks if model exists, if not, automatically pulls it."""
        with httpx.Client(timeout=get_settings().ollama_embedding_timeout_seconds) as client:
            logger.info(f"Checking/pulling Ollama embedding model '{self.model}' at {self.base_url}")
            try:
                response = client.post(
                    f"{self.base_url}/api/pull",
                    json={"name": self.model, "stream": False}
                )
                response.raise_for_status()
                logger.info(f"Successfully ensured model '{self.model}' is available.")
            except Exception as exc:
                logger.warning(f"Could not auto-pull model '{self.model}': {exc}")

    def _get_embedding(self, text: str) -> List[float]:
        """Synchronous HTTP call to local Ollama embeddings endpoint."""
        with httpx.Client(timeout=get_settings().ollama_embedding_timeout_seconds) as client:
            try:
                response = client.post(
                    f"{self.base_url}/api/embeddings",
                    json={"model": self.model, "prompt": text}
                )
                if response.status_code == 404:
                    self._ensure_model_exists()
                    response = client.post(
                        f"{self.base_url}/api/embeddings",
                        json={"model": self.model, "prompt": text}
                    )
                response.raise_for_status()
                data = response.json()
                return data["embedding"]
            except (httpx.ConnectError, httpx.TimeoutException) as exc:
                logger.error(f"Failed to connect to Ollama for embeddings at {self.base_url}. Is Ollama running?")
                raise Exception(f"Ollama connection refused or timed out: {exc}") from exc
            except httpx.HTTPStatusError as exc:
                error_msg = exc.response.text
                logger.error(f"HTTPStatusError from Ollama: {error_msg}")
                raise Exception(f"Ollama returned HTTP error: {error_msg}") from exc

    def _get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Synchronous batch call to local Ollama embeddings endpoint."""
        with httpx.Client(timeout=get_settings().ollama_embedding_timeout_seconds) as client:
            try:
                # 10x SPEEDUP: Use Ollama's native batch embedding endpoint (/api/embed)
                response = client.post(
                    f"{self.base_url}/api/embed",
                    json={"model": self.model, "input": texts}
                )
                if response.status_code == 200:
                    data = response.json()
                    if "embeddings" in data:
                        return data["embeddings"]
            except Exception as exc:
                logger.warning(f"Fast batch /api/embed failed ({exc}), falling back to sequential /api/embeddings")

        # Fallback to sequential /api/embeddings for older Ollama versions
        embeddings = []
        with httpx.Client(timeout=get_settings().ollama_embedding_timeout_seconds) as client:
            for i, text in enumerate(texts):
                try:
                    response = client.post(
                        f"{self.base_url}/api/embeddings",
                        json={"model": self.model, "prompt": text}
                    )
                    if response.status_code == 404 and i == 0:
                        self._ensure_model_exists()
                        response = client.post(
                            f"{self.base_url}/api/embeddings",
                            json={"model": self.model, "prompt": text}
                        )
                    response.raise_for_status()
                    data = response.json()
                    embeddings.append(data["embedding"])
                except (httpx.ConnectError, httpx.TimeoutException) as exc:
                    logger.error(f"Failed to connect to Ollama for embeddings at {self.base_url}. Is Ollama running?")
                    raise Exception(f"Ollama connection refused or timed out: {exc}") from exc
                except httpx.HTTPStatusError as exc:
                    error_msg = exc.response.text
                    logger.error(f"HTTPStatusError from Ollama: {error_msg}")
                    raise Exception(f"Ollama returned HTTP error: {error_msg}") from exc
        return embeddings

    def add_documents(self, documents: List[str]) -> None:
        if not documents:
            return
        embeddings = self._get_embeddings_batch(documents)
        embeddings_np = np.array(embeddings).astype("float32")
        
        # Dynamically initialize the FAISS index based on the actual embedding dimension
        if self.index is None:
            self.dimension = embeddings_np.shape[1]
            self.index = faiss.IndexFlatL2(self.dimension)
            logger.info(f"Dynamically initialized FAISS index with dimension {self.dimension}")
            
        # Add to FAISS index
        self.index.add(embeddings_np)
        # Store matching text chunk
        self.chunks.extend(documents)
        logger.info(f"Added {len(documents)} chunks to local vector store index using Ollama embeddings.")

    def similarity_search(self, query: str, top_k: int = 3) -> List[str]:
        if not self.chunks:
            return []
        query_vector = self._get_embedding(query)
        query_vector_np = np.array([query_vector]).astype("float32")
        
        # Search FAISS index
        distances, indices = self.index.search(query_vector_np, min(top_k, len(self.chunks)))
        
        results = []
        for idx in indices[0]:
            if idx != -1 and idx < len(self.chunks):
                results.append(self.chunks[idx])
        return results

    def save(self, directory: str) -> None:
        os.makedirs(directory, exist_ok=True)
        # Save FAISS index
        index_path = os.path.join(directory, "index.faiss")
        faiss.write_index(self.index, index_path)
        
        # Save chunk texts mapping
        meta_path = os.path.join(directory, "metadata.pkl")
        with open(meta_path, "wb") as f:
            pickle.dump(self.chunks, f)
        logger.info(f"Saved local vector store FAISS index to {directory}")

    def load(self, directory: str) -> None:
        index_path = os.path.join(directory, "index.faiss")
        meta_path = os.path.join(directory, "metadata.pkl")
        if not os.path.exists(index_path) or not os.path.exists(meta_path):
            raise FileNotFoundError(f"FAISS index files not found in {directory}")
            
        self.index = faiss.read_index(index_path)
        with open(meta_path, "rb") as f:
            self.chunks = pickle.load(f)
        logger.info(f"Loaded local vector store FAISS index from {directory} containing {len(self.chunks)} chunks.")
