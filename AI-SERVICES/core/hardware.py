"""
Hardware detection and profile management module for Sovereign AI Workbench.
Supports dual profiles:
- GPU_RTX2050: NVIDIA GeForce RTX 2050 with 4 GB VRAM
- CPU_ONLY: No dedicated GPU, optimized for lightweight models
"""

import subprocess
import shutil
import re
from typing import Dict, Any, Optional
from core.logging import logger
from core.config import settings

PROFILE_GPU_RTX2050 = "GPU_RTX2050"
PROFILE_CPU_ONLY = "CPU_ONLY"

_cached_hardware_info: Optional[Dict[str, Any]] = None


def detect_hardware(force_refresh: bool = False) -> Dict[str, Any]:
    """
    Detect host hardware and determine active profile (GPU_RTX2050 vs CPU_ONLY).
    Treats GPU as an optimization — missing NVIDIA hardware will NEVER raise an exception.
    """
    global _cached_hardware_info
    if _cached_hardware_info is not None and not force_refresh:
        return _cached_hardware_info

    # 1. Check explicit setting override from .env / settings
    configured_profile = getattr(settings, "HARDWARE_PROFILE", "AUTO").upper().strip()
    if configured_profile in [PROFILE_CPU_ONLY, "CPU"]:
        logger.info("[HARDWARE] Explicit CPU_ONLY profile configured in settings.")
        _cached_hardware_info = {
            "profile": PROFILE_CPU_ONLY,
            "nvidiaAvailable": False,
            "mode": "cpu",
            "gpuName": None,
            "driverVersion": None,
            "totalMemory": None,
            "vramMb": 0,
            "detail": "Explicit CPU_ONLY profile active (lightweight models)"
        }
        return _cached_hardware_info

    fallback_info = {
        "profile": PROFILE_CPU_ONLY,
        "nvidiaAvailable": False,
        "mode": "cpu",
        "gpuName": None,
        "driverVersion": None,
        "totalMemory": None,
        "vramMb": 0,
        "detail": "CPU / integrated graphics mode (lightweight models)"
    }

    try:
        nvidia_smi_path = shutil.which("nvidia-smi")
        if not nvidia_smi_path:
            logger.info("[HARDWARE] NVIDIA GPU not detected (nvidia-smi not found in PATH). Defaulting to CPU_ONLY profile.")
            _cached_hardware_info = fallback_info
            return fallback_info

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
            
            # Extract numeric VRAM in MB
            vram_mb = 0
            if len(parts) > 2:
                match = re.search(r'(\d+)', parts[2])
                if match:
                    vram_mb = int(match.group(1))

            mem_total = f"{vram_mb} MB" if vram_mb > 0 else "Unknown"
            is_rtx = "2050" in gpu_name or "rtx" in gpu_name.lower() or vram_mb >= 3500

            active_profile = PROFILE_GPU_RTX2050 if is_rtx else PROFILE_GPU_RTX2050

            logger.info(
                f"[HARDWARE] NVIDIA GPU detected: {gpu_name} (Driver: {driver_ver}, VRAM: {mem_total}). "
                f"Active Profile: {active_profile}"
            )

            _cached_hardware_info = {
                "profile": active_profile,
                "nvidiaAvailable": True,
                "mode": "gpu",
                "gpuName": gpu_name,
                "driverVersion": driver_ver,
                "totalMemory": mem_total,
                "vramMb": vram_mb,
                "detail": f"{gpu_name} ({mem_total}) - {active_profile}"
            }
            return _cached_hardware_info
        else:
            logger.info("[HARDWARE] nvidia-smi returned non-zero. Using CPU_ONLY profile.")
            _cached_hardware_info = fallback_info
            return fallback_info

    except Exception as e:
        logger.info(f"[HARDWARE] Hardware detection warning: {e}. Using CPU_ONLY profile.")
        _cached_hardware_info = fallback_info
        return fallback_info


def get_hardware_profile() -> str:
    """Convenience getter for active hardware profile (GPU_RTX2050 or CPU_ONLY)."""
    hw = detect_hardware()
    return hw.get("profile", PROFILE_CPU_ONLY)
