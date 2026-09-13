"""
Hardware detection module for Sovereign AI Workbench.
Safely detects whether an NVIDIA GPU is available on the host machine.
GPU is treated as an optional optimization — missing NVIDIA GPU will NEVER raise an exception.
"""

import subprocess
import shutil
from typing import Dict, Any
from core.logging import logger

_cached_hardware_info: Dict[str, Any] = None


def detect_hardware() -> Dict[str, Any]:
    """
    Detect whether NVIDIA GPU is available on the host.
    Returns safe hardware information dictionary.
    Falls back gracefully to CPU mode if NVIDIA GPU or nvidia-smi is unavailable.
    """
    global _cached_hardware_info
    if _cached_hardware_info is not None:
        return _cached_hardware_info

    fallback_info = {
        "nvidiaAvailable": False,
        "mode": "cpu",
        "gpuName": None,
        "driverVersion": None,
        "totalMemory": None,
        "detail": "Using CPU / integrated graphics"
    }

    try:
        # Check if nvidia-smi is available on PATH
        nvidia_smi_path = shutil.which("nvidia-smi")
        if not nvidia_smi_path:
            logger.info("NVIDIA GPU not available (nvidia-smi not found in PATH)")
            logger.info("Operating mode: CPU / integrated graphics")
            _cached_hardware_info = fallback_info
            return fallback_info

        # Execute nvidia-smi to query GPU information
        result = subprocess.run(
            [
                nvidia_smi_path,
                "--query-gpu=name,driver_version,memory.total",
                "--format=csv,noheader,nounits"
            ],
            capture_output=True,
            text=True,
            timeout=2.5,
            check=False
        )

        if result.returncode == 0 and result.stdout.strip():
            output = result.stdout.strip().split("\n")[0]
            parts = [p.strip() for p in output.split(",")]
            gpu_name = parts[0] if len(parts) > 0 else "NVIDIA GPU"
            driver_ver = parts[1] if len(parts) > 1 else "Unknown"
            mem_total = f"{parts[2]} MB" if len(parts) > 2 else "Unknown"

            logger.info(f"NVIDIA GPU detected: {gpu_name} (Driver: {driver_ver}, VRAM: {mem_total})")
            logger.info("Operating mode: GPU acceleration enabled for local Ollama")

            _cached_hardware_info = {
                "nvidiaAvailable": True,
                "mode": "gpu",
                "gpuName": gpu_name,
                "driverVersion": driver_ver,
                "totalMemory": mem_total,
                "detail": f"{gpu_name} ({mem_total})"
            }
            return _cached_hardware_info
        else:
            logger.info("NVIDIA GPU not available or nvidia-smi query returned non-zero code")
            logger.info("Operating mode: CPU / integrated graphics")
            _cached_hardware_info = fallback_info
            return fallback_info

    except Exception as e:
        logger.info(f"NVIDIA GPU not available: {e}")
        logger.info("Operating mode: CPU / integrated graphics")
        _cached_hardware_info = fallback_info
        return fallback_info
