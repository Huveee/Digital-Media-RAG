from Chatbots.AnswerGenerator import LLMRequester as LLM_Bot
from Chatbots.VariatedLLM import VariatedLLMAnswerGenerator as VarLLM_Bot
from Chatbots.VariationGeneration import VariatorManager
from Core.runtime_config import RuntimeConfig


def generate_answer(prompt: str, config: RuntimeConfig, image=None):


    # Choose bot
    if config.active_bot == "llm":
        bot = LLM_Bot(model_name= config.llm_model_name)
        print(config.llm_model_name)
        print(config.variation_enabled)
        answer = bot.get_response(
            prompt,
            language=config.language,
            image=image
        )
        # Apply variation
        if config.variation_enabled:
            print("testing if code goes here")
            answer = VariatorManager.apply_variation(
                answer,
                config.variation_type,
                config
            )


    elif config.active_bot == "varllm":
        bot = VarLLM_Bot(model_name=config.varllm_model_name)
        answer = bot.get_response(
            prompt,
            variationPrompt=config.varllm_style,
            language=config.language,
            image=image
        )
        # Apply variation
        if config.variation_enabled:
            print("testing if code goes here")
            answer = VariatorManager.apply_variation(
                answer,
                config.variation_type,
                config
            )

    else:
        raise Exception("Unknown bot selected in config")

    """# Apply variation
    if config.variation_enabled:
        print("testing if code goes here")
        answer = VariatorManager.apply_variation(
            answer,
            config.variation_type
        )"""

    return answer


def generate_answer_stream(prompt: str, config: RuntimeConfig, image=None):

    if config.active_bot == "llm":
        bot = LLM_Bot(model_name=config.llm_model_name)

        if config.variation_enabled:
            # Must collect full answer first, then stream the variation
            answer = bot.get_response(prompt, language=config.language, image=image)
            yield from VariatorManager.apply_variation_stream(
                answer, config.variation_type, config
            )
        else:
            # Stream directly from LLM
            yield from bot.get_response_stream(prompt, language=config.language, image=image)

    elif config.active_bot == "varllm":
        bot = VarLLM_Bot(model_name=config.varllm_model_name)

        if config.variation_enabled:
            # Must collect full answer first, then stream the variation
            answer = bot.get_response(
                prompt, variationPrompt=config.varllm_style, language=config.language, image=image
            )
            yield from VariatorManager.apply_variation_stream(
                answer, config.variation_type, config
            )
        else:
            # Stream directly from varLLM
            yield from bot.get_response_stream(
                prompt, variationPrompt=config.varllm_style, language=config.language, image=image
            )

    else:
        raise Exception("Unknown bot selected in config")
