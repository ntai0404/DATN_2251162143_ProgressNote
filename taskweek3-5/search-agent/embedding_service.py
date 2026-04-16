from sentence_transformers import SentenceTransformer
import numpy as np

class EmbeddingService:
    def __init__(self, model_name='paraphrase-multilingual-MiniLM-L12-v2'):
        print(f"Loading embedding model: {model_name}...")
        self.model = SentenceTransformer(model_name)
        print("Model loaded.")

    def embed_texts(self, texts):
        """
        Convert a list of strings into a list of vectors.
        """
        if isinstance(texts, str):
            texts = [texts]
        embeddings = self.model.encode(texts)
        return embeddings.tolist()

if __name__ == "__main__":
    service = EmbeddingService()
    test_text = "Quy chế đào tạo đại học Thủy Lợi"
    vector = service.embed_texts(test_text)
    print(f"Vector size: {len(vector[0])}")
