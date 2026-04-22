import yaml
from config import CONFIG_FILE
from llm_client import LLMClient


def load_model_configs() -> list[dict]:
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    return config.get("llm_models", [])


def create_llm_clients() -> list[LLMClient]:
    model_configs = load_model_configs()
    return [
        LLMClient(
            name=mc["name"],
            base_url=mc["base_url"],
            api_key=mc["api_key"],
            model=mc["model"]
        )
        for mc in model_configs
    ]
