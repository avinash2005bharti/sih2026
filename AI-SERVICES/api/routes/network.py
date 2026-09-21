"""
Sovereign Network Monitor API Routes
Exposes sovereign air-gap metrics, real-time egress audit logs, and egress test triggers.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from core.network_monitor import network_monitor

router = APIRouter(prefix="/api/network")


class EgressTestRequest(BaseModel):
    destination: Optional[str] = Field("8.8.8.8", description="External destination to attempt")
    port: Optional[int] = Field(53, description="Target port")


@router.get("/status", summary="Get Sovereign Air-Gap Network Status and Proof")
async def get_network_status():
    """
    Returns real-time air-gap network metrics, verifying:
    - Zero external calls permitted or made
    - Total internal enclave socket calls recorded
    - Number of intercepted/blocked external calls
    - Tamper-evident cryptographic proof hash
    """
    return network_monitor.get_status()


@router.get("/audit", summary="Get tamper-evident network audit log")
async def get_network_audit(limit: int = Query(50, ge=1, le=200)):
    """
    Returns the recent tamper-evident connection audit records with timestamps,
    action (ALLOWED_ENCLAVE / BLOCKED_EXTERNAL_EGRESS), and rolling SHA-256 proof hashes.
    """
    return {
        "count": len(network_monitor.audit_log),
        "proof_hash": network_monitor.rolling_proof_hash,
        "records": network_monitor.get_audit_log(limit=limit)
    }


@router.post("/test-egress", summary="Actively test air-gap egress interceptor")
async def test_egress(payload: Optional[EgressTestRequest] = None):
    """
    Deliberately attempts an outbound socket connection to an external address
    to prove that the Sovereign Air-Gap Guard intercepts and blocks it in real-time.
    """
    dest = payload.destination if payload and payload.destination else "8.8.8.8"
    p = payload.port if payload and payload.port else 53
    result = network_monitor.test_egress_block(destination=dest, port=p)
    return result
