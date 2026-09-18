from abc import ABC, abstractmethod
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key = os.environ.get("CHATAI_API_KEY"),
    base_url = os.environ.get("BASE_URL")
)


"""Base class for all text variation strategies."""
class VariationGeneration(ABC):

    def __init__(self, model: str, language: str):
        self.model = model
        self.language = language

    @abstractmethod
    def style_instruction(self) -> str:
        pass

    def system_prompt(self) -> str:
        """Language-aware system prompt"""
        if self.language == "de":
            return "Du bist ein Experte für stilistische Textumformulierung."
        return "You are an expert text rewriter."

    def vary(self, text: str) -> str:
        prompt = (
            f"{self.style_instruction()}\n\n"
            f"---\n"
            f"Original response:\n{text}\n\n"
            f"Rewritten version:"
        )

        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_prompt()},
                {"role": "user", "content": prompt},
            ],
            temperature=0.8,
            max_tokens=512,
        )
        print("Testing response:", response)
        choice = response.choices[0]
        content = choice.message.content

        if content is None:
            raise RuntimeError(
                f"Variation failed: model returned no content "
                f"(finish_reason={choice.finish_reason})"
            )

        return content.strip()

    def vary_stream(self, text: str):
        """Yields content tokens as the variation is generated."""
        prompt = (
            f"{self.style_instruction()}\n\n"
            f"---\n"
            f"Original response:\n{text}\n\n"
            f"Rewritten version:"
        )

        stream = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_prompt()},
                {"role": "user", "content": prompt},
            ],
            temperature=0.8,
            max_tokens=512,
            stream=True,
        )

        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content

# Here are the different Promts for the Variators
# To add a new Variator, simply create a new class inheriting from VariationGeneration
# and implement the style_instruction method.
# Then scroll down to VariatorManager and add the new class to the VARIATORS dictionary.
class SimilarWordVariator(VariationGeneration):
    def style_instruction(self) -> str:
        return (
            "Rewrite the text using similar words."
            if self.language == "en"
            else "Formuliere den Text mit ähnlichen Wörtern um."
        )


class HedgingVariator(VariationGeneration):
    def style_instruction(self) -> str:
        return (
            "Rewrite the text using a hedging academic style."
            if self.language == "en"
            else "Formuliere den Text in einem vorsichtigen, akademischen Stil um."
        )


class MetaphorVariator(VariationGeneration):
    def style_instruction(self) -> str:
        return (
            "Rewrite the text using metaphors."
            if self.language == "en"
            else "Formuliere den Text mithilfe von Metaphern um."
        )


class StyleVariator(VariationGeneration):
    def style_instruction(self) -> str:
        return (
            "Rewrite the text in a different style."
            if self.language == "en"
            else "Formuliere den Text in einem anderen Stil um."
        )


# Add the new variators here
class VariatorManager:
    """Selects and applies a given variation style using an LLM."""

    # The word in "..." is how to call the variations
    VARIATORS = {
        "similarword": SimilarWordVariator,
        "hedging": HedgingVariator,
        "metaphor": MetaphorVariator,
        "style": StyleVariator,
    }

    @classmethod
    def apply_variation(cls, text: str, style: str, config) -> str:
        style = style.lower()
        variator_class = cls.VARIATORS.get(style)

        if not variator_class:
            raise ValueError(f"Unknown variation style: {style}")

        variator = variator_class(
            model=config.llm_model_name,
            language=config.language
        )

        return variator.vary(text)

    @classmethod
    def apply_variation_stream(cls, text: str, style: str, config):
        """Yields variation tokens as they are generated."""
        style = style.lower()
        variator_class = cls.VARIATORS.get(style)

        if not variator_class:
            raise ValueError(f"Unknown variation style: {style}")

        variator = variator_class(
            model=config.llm_model_name,
            language=config.language
        )

        yield from variator.vary_stream(text)
