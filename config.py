"""Load shared settings from the project .env file."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")


def env_str(name: str, default: str = "") -> str:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return value.strip()


def env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return int(raw.strip(), 0)


def env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return float(raw.strip())


def open_can():
    """Open the CAN bus using J2534_DLL and CAN_SPEED (kbit/s) from .env."""
    from connection import canbus

    dll = env_str("J2534_DLL")
    if not dll:
        raise RuntimeError("J2534_DLL is not set in .env")
    speed_kbit = env_int("CAN_SPEED", 500)
    return canbus.CANBUS(dll, baudrate=speed_kbit * 1000)


def env_id_set(name: str) -> set[int]:
    """Parse a comma- or semicolon-separated list of CAN IDs (decimal or 0x hex)."""
    raw = os.getenv(name, "")
    ids: set[int] = set()
    for part in raw.replace(";", ",").split(","):
        part = part.strip()
        if part:
            ids.add(int(part, 0))
    return ids
