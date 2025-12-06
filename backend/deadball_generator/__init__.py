"""
Embedded Deadball generator module.

Provides a callable API for roster generation and a minimal CLI for manual use.
Swap the internals of `generate_roster` with the real generator logic when ready.
"""

from .generator import GeneratedRoster, generate_roster  # noqa: F401
