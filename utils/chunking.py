from transformers import AutoTokenizer

from config import (
    EMBEDDING_MODEL,
    CHUNK_SIZE,
    CHUNK_OVERLAP
)


print("Loading tokenizer...")


tokenizer = AutoTokenizer.from_pretrained(
    EMBEDDING_MODEL
)


print("Tokenizer loaded.")


def chunk_text(
    text,
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP
):

    """
    Split text into token-aware chunks.

    The document is processed in smaller pieces first
    to avoid sending the entire document through the
    tokenizer at once.
    """

    # ==========================================
    # CLEAN TEXT
    # ==========================================

    text = text.strip()


    if not text:

        return []


    # ==========================================
    # SPLIT INTO PARAGRAPHS
    # ==========================================

    paragraphs = [
        paragraph.strip()
        for paragraph in text.split("\n")
        if paragraph.strip()
    ]


    chunks = []

    current_tokens = []


    # ==========================================
    # PROCESS EACH PARAGRAPH
    # ==========================================

    for paragraph in paragraphs:

        paragraph_tokens = tokenizer.encode(
            paragraph,
            add_special_tokens=False
        )


        # ======================================
        # HANDLE VERY LARGE PARAGRAPHS
        # ======================================

        if len(paragraph_tokens) > chunk_size:

            # Save existing chunk first

            if current_tokens:

                chunk_text_value = tokenizer.decode(
                    current_tokens,
                    skip_special_tokens=True
                ).strip()


                if chunk_text_value:

                    chunks.append(
                        chunk_text_value
                    )


                # Keep overlap

                current_tokens = current_tokens[
                    -chunk_overlap:
                ]


            # Split large paragraph directly

            start = 0


            while start < len(paragraph_tokens):

                end = start + chunk_size


                chunk_tokens = (
                    paragraph_tokens[
                        start:end
                    ]
                )


                chunk_text_value = (
                    tokenizer.decode(
                        chunk_tokens,
                        skip_special_tokens=True
                    ).strip()
                )


                if chunk_text_value:

                    chunks.append(
                        chunk_text_value
                    )


                start += (
                    chunk_size
                    -
                    chunk_overlap
                )


            continue


        # ======================================
        # CHECK IF PARAGRAPH FITS CURRENT CHUNK
        # ======================================

        if (
            len(current_tokens)
            +
            len(paragraph_tokens)
            <=
            chunk_size
        ):

            current_tokens.extend(
                paragraph_tokens
            )


        else:

            # ==================================
            # SAVE CURRENT CHUNK
            # ==================================

            if current_tokens:

                chunk_text_value = (
                    tokenizer.decode(
                        current_tokens,
                        skip_special_tokens=True
                    ).strip()
                )


                if chunk_text_value:

                    chunks.append(
                        chunk_text_value
                    )


            # ==================================
            # KEEP OVERLAP
            # ==================================

            overlap_tokens = current_tokens[
                -chunk_overlap:
            ]


            current_tokens = (
                overlap_tokens
                +
                paragraph_tokens
            )


    # ==========================================
    # ADD FINAL CHUNK
    # ==========================================

    if current_tokens:

        chunk_text_value = (
            tokenizer.decode(
                current_tokens,
                skip_special_tokens=True
            ).strip()
        )


        if chunk_text_value:

            chunks.append(
                chunk_text_value
            )


    return chunks