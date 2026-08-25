# services/vector_service.py

import chromadb


from config import (
    CHROMA_DB_PATH,
    CHROMA_COLLECTION_NAME
)


class VectorService:


    # ==================================
    # INITIALIZE CHROMADB
    # ==================================

    def __init__(self):

        print(
            "Connecting to ChromaDB..."
        )

        self.client = (

            chromadb.PersistentClient(
                path=CHROMA_DB_PATH
            )

        )

        self.collection = (

            self.client.get_or_create_collection(

                name=CHROMA_COLLECTION_NAME,

                metadata={
                    "hnsw:space": "cosine"
                }

            )

        )

        print(
            "Connected to ChromaDB."
        )


    # ==================================
    # ADD DOCUMENT CHUNKS
    # ==================================

    def add_document_chunks(
        self,
        ids,
        documents,
        embeddings,
        metadatas
    ):

        self.collection.add(

            ids=ids,

            documents=documents,

            embeddings=embeddings,

            metadatas=metadatas

        )


    # ==================================
    # CHECK DUPLICATE DOCUMENT
    # ==================================

    def get_document_by_hash(
        self,
        file_hash
    ):

        results = (

            self.collection.get(

                where={
                    "file_hash":
                    file_hash
                },

                include=[
                    "metadatas"
                ],

                limit=1

            )

        )


        ids = (

            results.get(
                "ids",
                []
            )

        )


        if not ids:

            return None


        metadatas = (

            results.get(
                "metadatas",
                []
            )

        )


        if not metadatas:

            return None


        return metadatas[0]


    # ==================================
    # CHECK DOCUMENT EXISTS
    # ==================================

    def document_exists(
        self,
        document_id
    ):

        results = (

            self.collection.get(

                where={
                    "document_id":
                    document_id
                },

                include=[
                    "metadatas"
                ],

                limit=1

            )

        )


        ids = (

            results.get(
                "ids",
                []
            )

        )


        return len(
            ids
        ) > 0


    # ==================================
    # GET SINGLE DOCUMENT METADATA
    # ==================================

    def get_document(
        self,
        document_id
    ):

        results = (

            self.collection.get(

                where={
                    "document_id":
                    document_id
                },

                include=[
                    "metadatas"
                ],

                limit=1

            )

        )


        ids = (

            results.get(
                "ids",
                []
            )

        )


        if not ids:

            return None


        metadatas = (

            results.get(
                "metadatas",
                []
            )

        )


        if not metadatas:

            return None


        return metadatas[0]


    # ==================================
    # QUERY VECTOR DATABASE
    # ==================================

    def search(
        self,
        query_embedding,
        top_k=5
    ):

        if not query_embedding:

            return {

                "ids":
                [[]],

                "documents":
                [[]],

                "metadatas":
                [[]],

                "distances":
                [[]]

            }


        # ChromaDB expects a list of embeddings.
        # If a single embedding is provided,
        # convert it into a nested list.

        if (

            isinstance(
                query_embedding,
                list
            )

            and

            query_embedding

            and

            not isinstance(
                query_embedding[0],
                list
            )

        ):

            query_embedding = [
                query_embedding
            ]


        results = (

            self.collection.query(

                query_embeddings=
                query_embedding,

                n_results=
                top_k,

                include=[

                    "documents",

                    "metadatas",

                    "distances"

                ]

            )

        )


        return results


    # ==================================
    # MULTI QUERY SEARCH
    #
    # Searches multiple query embeddings.
    #
    # Results remain grouped according
    # to the query order.
    # ==================================

    def multi_search(
        self,
        query_embeddings,
        top_k=5
    ):

        if not query_embeddings:

            return {

                "ids":
                [],

                "documents":
                [],

                "metadatas":
                [],

                "distances":
                []

            }


        # Convert a single embedding into
        # a list containing one embedding.

        if (

            isinstance(
                query_embeddings[0],
                (int, float)
            )

        ):

            query_embeddings = [
                query_embeddings
            ]


        results = (

            self.collection.query(

                query_embeddings=
                query_embeddings,

                n_results=
                top_k,

                include=[

                    "documents",

                    "metadatas",

                    "distances"

                ]

            )

        )


        return results


    # ==================================
    # DELETE ONE DOCUMENT
    # ==================================

    def delete_document(
        self,
        document_id
    ):

        if not self.document_exists(
            document_id
        ):

            raise ValueError(
                "Document not found."
            )


        self.collection.delete(

            where={
                "document_id":
                document_id
            }

        )


        # Verify deletion.

        if self.document_exists(
            document_id
        ):

            raise RuntimeError(

                "Document could not be "
                "deleted from ChromaDB."

            )


        return True


    # ==================================
    # GET ALL DOCUMENT RECORDS
    # ==================================

    def get_all_documents(
        self
    ):

        results = (

            self.collection.get(

                include=[
                    "metadatas"
                ]

            )

        )


        return results


    # ==================================
    # GET UNIQUE DOCUMENTS
    #
    # Returns one metadata record
    # for each uploaded document.
    # ==================================

    def get_unique_documents(
        self
    ):

        results = (

            self.get_all_documents()

        )


        metadatas = (

            results.get(
                "metadatas",
                []
            )

        )


        unique_documents = {}



        for metadata in metadatas:

            if not metadata:

                continue


            document_id = (

                metadata.get(
                    "document_id"
                )

            )


            if not document_id:

                continue


            if (

                document_id
                not in
                unique_documents

            ):

                unique_documents[
                    document_id
                ] = metadata


        return list(
            unique_documents.values()
        )


    # ==================================
    # RESET DATABASE
    # ==================================

    def reset_database(
        self
    ):

        try:

            self.client.delete_collection(
                CHROMA_COLLECTION_NAME
            )

        except Exception:

            pass


        self.collection = (

            self.client.get_or_create_collection(

                name=CHROMA_COLLECTION_NAME,

                metadata={
                    "hnsw:space": "cosine"
                }

            )

        )


        return True