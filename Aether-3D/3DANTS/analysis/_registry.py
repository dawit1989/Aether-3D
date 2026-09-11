"""Optional, lightweight component registry.

Maps human-readable names to callable factories so that the orchestrator (and
users) can register/resolve custom traffic, fading, interference or other
components without touching the core simulation loop.

This is intentionally simple: name -> factory. No dependency-injection
framework is introduced.
"""
from __future__ import annotations

from typing import Callable, Dict, TypeVar

T = TypeVar("T")


class ComponentRegistry:
    """A minimal name -> factory registry."""

    def __init__(self):
        self._factories: Dict[str, Callable[..., object]] = {}

    def register(self, name: str, factory: Callable[..., T]) -> "ComponentRegistry":
        """Register a factory under ``name``.

        Returns ``self`` so registration can be chained.
        """
        if not isinstance(name, str) or not name:
            raise ValueError("component name must be a non-empty string")
        if not callable(factory):
            raise TypeError("factory must be callable")
        self._factories[name] = factory
        return self

    def get(self, name: str) -> Callable[..., T]:
        """Return the factory registered under ``name``."""
        try:
            return self._factories[name]
        except KeyError:
            raise KeyError(f"no component registered as {name!r}") from None

    def names(self):
        """Return the registered component names."""
        return list(self._factories)

    def __contains__(self, name: str) -> bool:
        return name in self._factories