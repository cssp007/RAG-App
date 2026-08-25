from sentence_transformers import (
    SentenceTransformer
)

from config import (
    EMBEDDING_MODEL
)


class EmbeddingService:

    def __init__(self):

        print(
            "Loading embedding model..."
        )

        self.model = (
            SentenceTransformer(
                EMBEDDING_MODEL
            )
        )

        print(
            "Embedding model loaded."
        )


    # ==================================
    # CREATE EMBEDDINGS FOR DOCUMENTS
    # ==================================

    def create_embeddings(
        self,
        texts
    ):

        embeddings = (
            self.model.encode(

                texts,

                show_progress_bar=False,

                convert_to_numpy=True

            )
        )

        return embeddings.tolist()


    # ==================================
    # CREATE SINGLE EMBEDDING
    # ==================================

    def create_embedding(
        self,
        text
    ):

        embedding = (
            self.model.encode(

                text,

                convert_to_numpy=True

            )
        )

        return embedding.tolist()


    # ==================================
    # CREATE QUERY EMBEDDING
    #
    # Required by app.py:
    #
    # embedding_service
    # .create_query_embedding(query)
    # ==================================

    def create_query_embedding(
        self,
        query
    ):

        return self.create_embedding(
            query
        )