# services/llm_service.py

import time

import ollama


from config import (
    OLLAMA_MODEL,
    OLLAMA_HOST,
    LLM_TEMPERATURE,
    LLM_NUM_PREDICT,
    LLM_NUM_CTX,
    MAX_AVAILABLE_MODELS,
    MODEL_LIST_CACHE_SECONDS,
)


class LLMService:


    # ==================================
    # INITIALIZE OLLAMA
    # ==================================

    def __init__(
        self
    ):

        self.model = (
            OLLAMA_MODEL
        )


        self.client = (

            ollama.Client(
                host=OLLAMA_HOST
            )

        )


        self._cached_models = []

        self._models_cache_time = 0


    # ==================================
    # GET VALUE FROM OLLAMA RESPONSE
    #
    # Supports both:
    #
    # Object:
    # response.response
    #
    # Dictionary:
    # response["response"]
    # ==================================

    def get_response_value(
        self,
        response,
        key,
        default=""
    ):

        if response is None:

            return default


        # Dictionary response.

        if isinstance(
            response,
            dict
        ):

            return response.get(
                key,
                default
            )


        # Ollama object response.

        return getattr(
            response,
            key,
            default
        )


    # ==================================
    # CHECK OLLAMA CONNECTION
    # ==================================

    def check_connection(
        self
    ):

        try:

            self.client.list()

            return True

        except Exception:

            return False


    # ==================================
    # GET AVAILABLE OLLAMA MODELS
    # ==================================

    def get_available_models(
        self,
        force_refresh=False
    ):

        current_time = (
            time.time()
        )


        cache_valid = (

            self._cached_models

            and

            not force_refresh

            and

            (

                current_time

                -

                self._models_cache_time

            )

            <

            MODEL_LIST_CACHE_SECONDS

        )


        if cache_valid:

            return (
                self._cached_models
            )


        try:

            response = (

                self.client.list()

            )


            # Support both dictionary
            # and object responses.

            if isinstance(
                response,
                dict
            ):

                response_models = (

                    response.get(
                        "models",
                        []
                    )

                )

            else:

                response_models = (

                    getattr(
                        response,
                        "models",
                        []
                    )

                )


            models = []


            for model in response_models:

                if isinstance(
                    model,
                    dict
                ):

                    model_name = (

                        model.get(
                            "model"
                        )

                        or

                        model.get(
                            "name"
                        )

                    )

                else:

                    model_name = (

                        getattr(
                            model,
                            "model",
                            None
                        )

                        or

                        getattr(
                            model,
                            "name",
                            None
                        )

                    )


                if model_name:

                    models.append(
                        str(
                            model_name
                        )
                    )


            # Remove duplicates and sort.

            models = sorted(

                list(

                    set(
                        models
                    )

                )

            )


            # Limit maximum models returned.

            models = (

                models[
                    :MAX_AVAILABLE_MODELS
                ]

            )


            self._cached_models = (
                models
            )


            self._models_cache_time = (
                current_time
            )


            return (
                models
            )


        except Exception as error:

            print(

                f"Error getting "
                f"Ollama models: {error}"

            )


            # Return cached models if
            # Ollama temporarily fails.

            if self._cached_models:

                return (
                    self._cached_models
                )


            return []


    # ==================================
    # CHECK IF MODEL EXISTS
    # ==================================

    def check_model(
        self,
        model_name
    ):

        available_models = (

            self.get_available_models()

        )


        return (

            model_name

            in

            available_models

        )


    # ==================================
    # GET SELECTED MODEL
    # ==================================

    def get_selected_model(
        self,
        model_name=None
    ):

        selected_model = (

            model_name

            or

            self.model

        )


        selected_model = str(
            selected_model
        ).strip()


        # Fall back to the configured
        # default model.

        if not selected_model:

            selected_model = (
                self.model
            )


        return (
            selected_model
        )


    # ==================================
    # VALIDATE MODEL
    # ==================================

    def validate_model(
        self,
        model_name=None
    ):

        selected_model = (

            self.get_selected_model(
                model_name
            )

        )


        if not self.check_model(
            selected_model
        ):

            raise ValueError(

                f"Ollama model "
                f"'{selected_model}' "
                f"is not installed."

            )


        return (
            selected_model
        )


    # ==================================
    # BUILD RAG PROMPT
    # ==================================

    def build_prompt(
        self,
        question,
        context
    ):

        return f"""
You are a helpful AI Document Assistant.

Answer the user's question using ONLY the information
provided in the context below.

IMPORTANT RULES:

1. Answer the user's question directly.

2. Use only information from the provided context.

3. Do not invent, assume, or add information that is
   not available in the context.

4. Do not mention embeddings, vector databases,
   retrieval systems, ChromaDB, or internal system
   implementation.

5. If multiple topics are requested, answer each
   available topic separately with clear headings.

6. If information for a specific topic is not available
   in the context, do not create an answer for that topic.

7. Keep the answer clear, accurate, and well structured.

8. Use bullet points, numbered lists, or headings when
   they improve readability.

====================
CONTEXT
====================

{context}

====================
USER QUESTION
====================

{question}

====================
ANSWER
====================
""".strip()


    # ==================================
    # GENERATION OPTIONS
    # ==================================

    def get_generation_options(
        self
    ):

        return {

            "temperature":
            LLM_TEMPERATURE,

            "num_predict":
            LLM_NUM_PREDICT,

            "num_ctx":
            LLM_NUM_CTX

        }


    # ==================================
    # GENERATE NON-STREAMING ANSWER
    # ==================================

    def generate_answer(
        self,
        question,
        context,
        model_name=None
    ):

        selected_model = (

            self.validate_model(
                model_name
            )

        )


        prompt = (

            self.build_prompt(
                question,
                context
            )

        )


        start_time = (

            time.perf_counter()

        )


        response = (

            self.client.generate(

                model=
                selected_model,

                prompt=
                prompt,

                stream=
                False,

                options=
                self.get_generation_options()

            )

        )


        generation_time = round(

            time.perf_counter()

            -

            start_time,

            4

        )


        answer = (

            self.get_response_value(

                response,

                "response",

                ""

            )

        )


        answer = str(
            answer
        ).strip()


        if not answer:

            answer = (

                "The selected model did not return "
                "an answer."

            )


        return {

            "answer":
            answer,

            "model":
            selected_model,

            "generation_time":
            generation_time

        }


    # ==================================
    # STREAM ANSWER
    #
    # Returns dictionaries:
    #
    # {
    #     "type": "token",
    #     "content": "..."
    # }
    #
    # Final event:
    #
    # {
    #     "type": "done",
    #     "model": "..."
    # }
    # ==================================

    def stream_answer(
        self,
        question,
        context,
        model_name=None
    ):

        selected_model = (

            self.validate_model(
                model_name
            )

        )


        prompt = (

            self.build_prompt(
                question,
                context
            )

        )


        print(

            f"Generating answer using model: "
            f"{selected_model}"

        )


        stream = (

            self.client.generate(

                model=
                selected_model,

                prompt=
                prompt,

                stream=
                True,

                options=
                self.get_generation_options()

            )

        )


        token_count = 0


        for chunk in stream:

            # Support both dictionary
            # and object responses.

            response_text = (

                self.get_response_value(

                    chunk,

                    "response",

                    ""

                )

            )


            if response_text:

                token_count += 1


                yield {

                    "type":
                    "token",

                    "content":
                    str(
                        response_text
                    )

                }


        print(

            f"Generated "
            f"{token_count} response chunks."

        )


        # If Ollama returned no content.

        if token_count == 0:

            yield {

                "type":
                "token",

                "content":

                "The selected model did not return "
                "a response."

            }


        # Final event.

        yield {

            "type":
            "done",

            "model":
            selected_model

        }