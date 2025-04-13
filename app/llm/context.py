from dataclasses import dataclass
from collections import deque
from .message import Message
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ContextConfig:
    max_context_length: int
    context_invalidation_time_seconds: int
    system_instruction: str


class ContextManager:
    _instance = None  # Class-level attribute to hold the singleton instance

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ContextManager, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "initialized"):  # Ensure __init__ runs only once
            self.context_configs: dict[str, ContextConfig] = {}
            self.context: dict[str, deque[Message]] = {}
            self.initialized = True  # Mark as initialized

    def add_context_config(self, key, **kwargs):
        for required_arg in ContextConfig.__dataclass_fields__.keys():
            if required_arg not in kwargs:
                raise ValueError(f"Missing required argument: {required_arg}")

        self.context_configs[key] = ContextConfig(**kwargs)

    def _update_context(self, key, message: Message):
        current_length = sum(map(len, self.context[key]))
        while (
            len(self.context[key]) > 0
            and current_length + len(message)
            >= self.context_configs[key].max_context_length
        ):
            current_length -= len(self.context[key].popleft())

        self.context[key].append(message)
        logger.info(f"Context updated: {self.context[key]}")

    def _ensure_relevant_context(self, key):
        # Clear context if most recent message is older than context_invalidation_time
        if (
            len(self.context[key]) > 0
            and (datetime.now() - self.context[key][-1].timestamp).total_seconds()
            > self.context_configs[key].context_invalidation_time_seconds
        ):
            logging.info("Clearing context...")
            self.context[key].clear()

    def add_mesage_to_context(self, key, message: Message):
        if key not in self.context:
            raise ValueError(f"Context key {key} not found.")
        self._update_context(key, message)

    def contextualize_prompt(self, key, prompt):
        if key not in self.context:
            raise ValueError(f"Context key {key} not found.")
        self._ensure_relevant_context(key)
        context = self.context[key]
        context_str = "\n".join([str(msg) for msg in context])
        return "<CONTEXT>\n" + context_str + "\n</CONTEXT>\n" + prompt
