import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    nvidia_api_key: str | None
    nvidia_model: str
    nvidia_base_url: str


def load_settings() -> Settings:
    load_dotenv()
    return Settings(
        nvidia_api_key=os.getenv("NVIDIA_API_KEY"),
        nvidia_model=os.getenv("NVIDIA_MODEL", "minimaxai/minimax-m3.1-flash"),
        nvidia_base_url=os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1"),
    )
