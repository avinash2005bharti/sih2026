"""
API routes for dedicated OCR and Moondream vision services.
Provides exact OCR text extraction and multimodal scene analysis.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import base64

from multimodal.vision import vision_service
from ocr.ocr_service import ocr_service
from multimodal.multimodal_orchestrator import multimodal_orchestrator
from core.logging import logger

router = APIRouter()


class MultimodalAnalysisRequest(BaseModel):
    """Request payload for multimodal image analysis."""
    image: Optional[str] = Field(None, description="Base64-encoded image data or file path")
    prompt: Optional[str] = Field(None, description="Optional instruction or query about the image")
    filename: Optional[str] = Field("uploaded_image.jpg", description="Image file name")


class MultimodalAnalysisResponse(BaseModel):
    """Response payload for combined OCR + Vision multimodal analysis."""
    success: bool
    filename: str
    ocr: Dict[str, Any]
    vision: Dict[str, Any]
    combined_context: str
    duration_seconds: Optional[float] = None


class ImageAnalysisRequest(BaseModel):
    """Request to analyze an image."""
    image: str = Field(..., description="Base64-encoded image data or file path")
    prompt: Optional[str] = Field("Describe this image", description="Question/prompt about the image")
    task_type: str = Field(default="analysis", description="Type of analysis (analysis, ocr, classify, diagram)")


class ImageAnalysisResponse(BaseModel):
    """Response from image analysis."""
    result: str
    model: str
    task_type: str


class TextExtractionRequest(BaseModel):
    """Request to extract text from image using dedicated OCR."""
    image: str = Field(..., description="Base64-encoded image data or file path")


class ClassificationRequest(BaseModel):
    """Request to classify an image."""
    image: str = Field(..., description="Base64-encoded image data or file path")
    categories: Optional[List[str]] = Field(None, description="Optional categories to classify into")


class ClassificationResponse(BaseModel):
    """Response from image classification."""
    classification: str
    model: str


# =====================================================================
# MULTIMODAL COMBINED ENDPOINTS (/api/v1/vision/analyze & /api/vision/analyze)
# =====================================================================

@router.post("/api/v1/vision/analyze", response_model=MultimodalAnalysisResponse, summary="Analyze image with OCR + Moondream")
@router.post("/api/vision/analyze/combined", response_model=MultimodalAnalysisResponse, summary="Analyze image with OCR + Moondream")
async def analyze_multimodal_v1(
    file: Optional[UploadFile] = File(None),
    image: Optional[str] = Form(None),
    prompt: Optional[str] = Form(None),
    json_payload: Optional[MultimodalAnalysisRequest] = None
):
    """
    Combined Multimodal Analysis:
    1. Dedicated OCR (PaddleOCR) extracts exact factual text.
    2. Vision Service (Moondream via Ollama) provides visual scene understanding.
    3. Both outputs are combined into a Unified Context.
    """
    try:
        image_source = None
        filename = "inspection.jpg"
        effective_prompt = None

        if file:
            image_source = await file.read()
            filename = file.filename or "inspection.jpg"
            effective_prompt = prompt
        elif image:
            image_source = image
            effective_prompt = prompt
        elif json_payload:
            image_source = json_payload.image
            filename = json_payload.filename or "inspection.jpg"
            effective_prompt = json_payload.prompt

        if not image_source:
            raise HTTPException(status_code=400, detail="No image provided. Please upload a file or supply base64 image data.")

        result = await multimodal_orchestrator.analyze(
            image_source=image_source,
            user_prompt=effective_prompt,
            filename=filename
        )

        return MultimodalAnalysisResponse(
            success=result["success"],
            filename=result["filename"],
            ocr={
                "text": result["ocr"]["text"],
                "confidence": result["ocr"]["confidence"]
            },
            vision={
                "description": result["vision"]["description"]
            },
            combined_context=result["combined_context"],
            duration_seconds=result.get("duration_seconds")
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Multimodal analysis endpoint error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Multimodal analysis error: {str(e)}")


# Standard /api/vision/analyze supporting both multimodal synthesis and task routing
@router.post("/api/vision/analyze", summary="Analyze image (multimodal)")
async def analyze_image(request: ImageAnalysisRequest):
    """
    Analyze image endpoint supporting task types:
    - **analysis** or **multimodal**: Combined OCR + Moondream
    - **ocr**: Dedicated OCR only
    - **classify**: Image classification
    - **diagram**: Diagram analysis
    """
    try:
        logger.info(f"Image analysis request | task_type={request.task_type}")

        if request.task_type == "ocr":
            ocr_res = ocr_service.extract_text(request.image)
            return ImageAnalysisResponse(
                result=ocr_res.get("text", ""),
                model=ocr_service._engine_name,
                task_type="ocr"
            )

        if request.task_type == "classify":
            classification_result = await vision_service.classify_image(request.image)
            return ImageAnalysisResponse(
                result=classification_result["classification"],
                model=classification_result["model"],
                task_type="classify"
            )

        if request.task_type == "diagram":
            result = await vision_service.analyze_diagram(request.image)
            return ImageAnalysisResponse(
                result=result,
                model=vision_service.model,
                task_type="diagram"
            )

        # Default: Multimodal analysis (OCR + Moondream unified)
        multi_result = await multimodal_orchestrator.analyze(
            image_source=request.image,
            user_prompt=request.prompt
        )

        return {
            "success": multi_result["success"],
            "result": multi_result["combined_context"],
            "model": "paddleocr+moondream",
            "task_type": request.task_type,
            "ocr": multi_result["ocr"],
            "vision": multi_result["vision"],
            "combined_context": multi_result["combined_context"]
        }

    except Exception as e:
        logger.error(f"Image analysis error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")


# =====================================================================
# DEDICATED OCR EXTRACTION ENDPOINT
# =====================================================================

@router.post("/api/vision/extract-text", summary="Extract exact text from image using dedicated OCR")
async def extract_text(request: TextExtractionRequest):
    """
    Extract exact text using dedicated on-premise OCR engine (PaddleOCR).
    Does NOT use Moondream for OCR text transcription.
    """
    try:
        logger.info("[API] Dedicated text extraction request")
        result = ocr_service.extract_text(request.image)

        return {
            "success": result.get("success", False),
            "result": result.get("text", ""),
            "confidence": result.get("confidence", 0.0),
            "blocks": result.get("blocks", []),
            "model": ocr_service._engine_name,
            "task_type": "ocr"
        }

    except Exception as e:
        logger.error(f"Text extraction error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Extraction error: {str(e)}")


# =====================================================================
# CLASSIFICATION ENDPOINT
# =====================================================================

@router.post("/api/vision/classify", response_model=ClassificationResponse, summary="Classify image")
async def classify_image(request: ClassificationRequest):
    """Classify an image into categories."""
    try:
        logger.info("Image classification request")
        result = await vision_service.classify_image(request.image, request.categories)
        return ClassificationResponse(
            classification=result["classification"],
            model=result["model"]
        )
    except Exception as e:
        logger.error(f"Classification error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Classification error: {str(e)}")
