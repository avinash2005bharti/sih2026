"""
Dedicated On-Premise OCR Service for Sovereign AI Workbench.
Primary Engine: RapidOCR (ONNX Runtime, fast, local, native Windows/Linux CPU/GPU).
Secondary Fallback: PaddleOCR / Pytesseract / Vision LLM OCR.
Extracts exact alphanumeric text facts from equipment nameplates, gauges, and industrial documents.
"""

import os
import time
import gc
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import numpy as np
from PIL import Image

# Disable remote model source check to guarantee instant local offline startup
os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"

from core.config import settings
from core.logging import logger
from core.hardware import detect_hardware
from ocr.preprocessing import image_preprocessor


class OCRService:
    """Industrial OCR service for exact text extraction using local ONNX / PaddleOCR engines."""

    def __init__(self):
        self._engine = None
        self._engine_name = "rapidocr"
        self._is_initialized = False
        self._initialization_error: Optional[str] = None
        self._use_gpu = False

    def _determine_gpu_usage(self) -> bool:
        """Determine whether GPU acceleration can safely be enabled."""
        if not getattr(settings, "OCR_USE_GPU", False):
            return False
        hw = detect_hardware()
        return bool(hw.get("nvidiaAvailable", False))

    def _initialize_engine(self):
        """Lazy initialization of RapidOCR / PaddleOCR to keep initial FastAPI startup instantaneous."""
        if self._is_initialized:
            return

        self._use_gpu = self._determine_gpu_usage()
        device_mode = "gpu" if self._use_gpu else "cpu"

        # 1. Try RapidOCR (ONNX Runtime - fastest, fully local, perfectly stable on Windows)
        try:
            logger.info(f"[OCR] Initializing RapidOCR engine (ONNX Runtime, device='{device_mode}')...")
            from rapidocr_onnxruntime import RapidOCR

            self._engine = RapidOCR()
            self._engine_name = "rapidocr"
            self._is_initialized = True
            self._initialization_error = None
            logger.info("[OCR] [OK] RapidOCR engine successfully initialized (ONNX Runtime active)")
            return
        except ImportError as e:
            logger.warning(f"[OCR] RapidOCR import failed: {e}. Trying PaddleOCR...")
        except Exception as e:
            logger.warning(f"[OCR] RapidOCR initialization error: {e}. Trying PaddleOCR...")

        # 2. Try PaddleOCR (if installed)
        try:
            logger.info(f"[OCR] Attempting PaddleOCR engine on device='{device_mode}'...")
            from paddleocr import PaddleOCR

            self._engine = PaddleOCR(
                lang="en",
                device=device_mode,
                enable_mkldnn=False,
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=True
            )
            self._engine_name = "paddleocr"
            self._is_initialized = True
            self._initialization_error = None
            logger.info(f"[OCR] [OK] PaddleOCR engine successfully initialized ({device_mode.upper()} mode active)")
            return
        except ImportError as e:
            logger.warning(f"[OCR] PaddleOCR dependencies missing: {e}. Trying pytesseract fallback...")
        except Exception as e:
            logger.warning(f"[OCR] Failed to initialize PaddleOCR: {e}. Trying pytesseract fallback...")

        # 3. Try Pytesseract
        try:
            import pytesseract
            # Test if tesseract binary exists
            pytesseract.get_tesseract_version()
            self._engine = pytesseract
            self._engine_name = "pytesseract"
            self._is_initialized = True
            self._initialization_error = None
            logger.info("[OCR] [OK] Pytesseract engine successfully initialized")
            return
        except Exception as te:
            logger.warning(f"[OCR] Pytesseract unavailable: {te}")

        # Degraded fallback mode
        self._is_initialized = True
        self._engine = None
        self._engine_name = "vision_llm_fallback"
        self._initialization_error = "Dedicated OCR engines unavailable; will use local Vision LLM fallback"
        logger.warning(f"[OCR] Operating with engine='{self._engine_name}'")

    @property
    def is_available(self) -> bool:
        """Check if OCR engine is available."""
        if not self._is_initialized:
            self._initialize_engine()
        return True

    def get_status(self) -> Dict[str, Any]:
        """Return engine status for health checks."""
        if not self._is_initialized:
            self._initialize_engine()
        return {
            "status": "ok",
            "engine": self._engine_name,
            "gpu_mode": self._use_gpu,
            "error": self._initialization_error
        }

    def _sort_ocr_blocks(self, blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Sort detected OCR bounding boxes into natural reading order:
        primarily Top-to-Bottom (with line grouping tolerance), secondarily Left-to-Right.
        """
        if not blocks:
            return []

        # Sort with line tolerance (14px)
        blocks.sort(key=lambda b: (round(b.get("y_center", 0) / 14.0), b.get("x_min", 0)))

        clean_blocks = []
        for b in blocks:
            clean_blocks.append({
                "text": b["text"],
                "confidence": b.get("confidence", 0.95),
                "bbox": b.get("bbox", [0, 0, 0, 0]),
                "y_center": b.get("y_center", 0),
                "x_min": b.get("x_min", 0)
            })
        return clean_blocks

    def extract_text(self, image_source: Union[str, bytes, Image.Image]) -> Dict[str, Any]:
        """
        Extract exact text from an image or PDF document.

        Args:
            image_source: Base64 data string, local file path (image or PDF), raw bytes, or PIL Image.

        Returns:
            Structured dictionary with detected text, blocks, confidence, and status.
        """
        if not self._is_initialized:
            self._initialize_engine()

        # Check if source is a PDF file or bytes
        if isinstance(image_source, str) and (image_source.strip().lower().endswith(".pdf") or "application/pdf" in image_source):
            return self.extract_pdf(image_source)
        if isinstance(image_source, bytes) and image_source.startswith(b"%PDF"):
            return self.extract_pdf(image_source)
        if hasattr(image_source, "suffix") and getattr(image_source, "suffix", "").lower() == ".pdf":
            return self.extract_pdf(str(image_source))

        start_time = time.time()
        logger.info(f"[OCR] Starting OCR with engine='{self._engine_name}'")

        np_img = None
        pil_img = None
        try:
            # 1. Preprocess image
            np_img, pil_img = image_preprocessor.preprocess(image_source)

            blocks = []

            # -----------------------------------------------------------------
            # Engine A: RapidOCR (Primary, fast ONNX)
            # -----------------------------------------------------------------
            if self._engine_name == "rapidocr" and self._engine is not None:
                ocr_res, elapse = self._engine(np_img)
                if ocr_res:
                    for item in ocr_res:
                        if not item or len(item) < 3:
                            continue
                        box, text, score = item[0], item[1], item[2]
                        clean_text = str(text).strip()
                        if not clean_text:
                            continue
                        try:
                            conf = round(float(score), 3)
                        except Exception:
                            conf = 0.95

                        # box is 4 points: [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
                        xs = [p[0] for p in box]
                        ys = [p[1] for p in box]
                        x_min, x_max = int(min(xs)), int(max(xs))
                        y_min, y_max = int(min(ys)), int(max(ys))

                        blocks.append({
                            "text": clean_text,
                            "confidence": conf,
                            "bbox": [x_min, y_min, x_max, y_max],
                            "y_center": (y_min + y_max) / 2.0,
                            "x_min": x_min
                        })

            # -----------------------------------------------------------------
            # Engine B: PaddleOCR
            # -----------------------------------------------------------------
            elif self._engine_name == "paddleocr" and self._engine is not None:
                if hasattr(self._engine, "predict"):
                    raw_results = list(self._engine.predict(np_img))
                else:
                    raw_results = self._engine.ocr(np_img)

                if raw_results and len(raw_results) > 0:
                    first_res = raw_results[0]
                    if isinstance(first_res, dict) and "rec_texts" in first_res:
                        rec_texts = first_res.get("rec_texts", [])
                        rec_scores = first_res.get("rec_scores", [])
                        rec_boxes = first_res.get("rec_boxes", [])
                        for i, text in enumerate(rec_texts):
                            clean_text = str(text).strip()
                            if not clean_text:
                                continue
                            conf = round(float(rec_scores[i]), 3) if i < len(rec_scores) else 0.95
                            if i < len(rec_boxes):
                                box = rec_boxes[i]
                                if len(box) == 4 and not isinstance(box[0], (list, np.ndarray)):
                                    x_min, y_min, x_max, y_max = [int(v) for v in box]
                                else:
                                    xs = [p[0] for p in box]
                                    ys = [p[1] for p in box]
                                    x_min, y_min, x_max, y_max = int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))
                            else:
                                x_min, y_min, x_max, y_max = 0, 0, 0, 0

                            blocks.append({
                                "text": clean_text,
                                "confidence": conf,
                                "bbox": [x_min, y_min, x_max, y_max],
                                "y_center": (y_min + y_max) / 2.0,
                                "x_min": x_min
                            })
                    elif isinstance(first_res, list):
                        for item in first_res:
                            if not item or len(item) != 2:
                                continue
                            box, (text, confidence) = item
                            xs = [p[0] for p in box]
                            ys = [p[1] for p in box]
                            blocks.append({
                                "text": str(text).strip(),
                                "confidence": round(float(confidence), 3),
                                "bbox": [int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))],
                                "y_center": (min(ys) + max(ys)) / 2.0,
                                "x_min": min(xs)
                            })

            # -----------------------------------------------------------------
            # Engine C: Pytesseract
            # -----------------------------------------------------------------
            elif self._engine_name == "pytesseract" and self._engine is not None:
                import pytesseract
                text_data = pytesseract.image_to_string(pil_img or Image.fromarray(np_img))
                for line in text_data.splitlines():
                    clean = line.strip()
                    if clean:
                        blocks.append({
                            "text": clean,
                            "confidence": 0.90,
                            "bbox": [0, 0, 0, 0],
                            "y_center": 0.0,
                            "x_min": 0
                        })

            # -----------------------------------------------------------------
            # Engine D: Vision LLM fallback (when no traditional OCR engine available)
            # -----------------------------------------------------------------
            else:
                try:
                    import asyncio
                    from llm.ollama_client import ollama_client
                    import base64
                    import io

                    buf = io.BytesIO()
                    (pil_img or Image.fromarray(np_img)).save(buf, format="PNG")
                    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

                    v_model = getattr(settings, "GPU_VISION_MODEL", "qwen3-vl:4b")
                    prompt = "Extract and transcribe all visible text, numbers, labels, and serial numbers in this image exactly as written. Return only the extracted text lines."
                    
                    try:
                        loop = asyncio.get_running_loop()
                    except RuntimeError:
                        loop = None

                    if loop and loop.is_running():
                        import concurrent.futures
                        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                            reply = executor.submit(asyncio.run, ollama_client.chat(
                                model=v_model,
                                messages=[{"role": "user", "content": prompt, "images": [b64]}]
                            )).result()
                    else:
                        reply = asyncio.run(ollama_client.chat(
                            model=v_model,
                            messages=[{"role": "user", "content": prompt, "images": [b64]}]
                        ))

                    for line in reply.splitlines():
                        c_line = line.strip()
                        if c_line:
                            blocks.append({
                                "text": c_line,
                                "confidence": 0.92,
                                "bbox": [0, 0, 0, 0],
                                "y_center": 0.0,
                                "x_min": 0
                            })
                except Exception as llm_ocr_err:
                    logger.warning(f"[OCR] Vision LLM OCR fallback error: {llm_ocr_err}")

            # 3. Sort into natural reading order
            sorted_blocks = self._sort_ocr_blocks(blocks)

            # 4. Formulate full text
            full_text_lines = [b["text"] for b in sorted_blocks if b["text"]]
            full_text = "\n".join(full_text_lines)

            # Average confidence
            confidences = [b["confidence"] for b in sorted_blocks]
            avg_confidence = round(sum(confidences) / len(confidences), 3) if confidences else 0.0

            duration = round(time.time() - start_time, 2)
            logger.info(f"[OCR] Completed in {duration}s | detected_lines={len(sorted_blocks)} | avg_conf={avg_confidence} | engine={self._engine_name}")

            return {
                "success": True,
                "text": full_text,
                "confidence": avg_confidence,
                "blocks": sorted_blocks,
                "lines": sorted_blocks,
                "line_count": len(sorted_blocks),
                "duration_seconds": duration,
                "engine": self._engine_name
            }

        except Exception as e:
            duration = round(time.time() - start_time, 2)
            logger.error(f"[OCR] OCR processing error after {duration}s: {e}", exc_info=True)
            return {
                "success": False,
                "text": "",
                "confidence": 0.0,
                "blocks": [],
                "error": str(e),
                "engine": self._engine_name
            }

        finally:
            del np_img
            del pil_img
            gc.collect()

    def extract_text_from_bytes(self, image_bytes: bytes) -> Dict[str, Any]:
        """Convenience method to extract text from raw bytes."""
        return self.extract_text(image_bytes)

    def extract_pdf(self, pdf_source: Union[str, bytes], max_pages: int = 30) -> Dict[str, Any]:
        """Extract text from multi-page scanned PDF using pypdfium2 page rendering + OCR."""
        start_time = time.time()
        logger.info(f"[OCR] Starting PDF OCR extraction: {pdf_source if isinstance(pdf_source, str) else 'raw bytes'}")
        if not self.is_available:
            return {
                "success": False,
                "text": "",
                "confidence": 0.0,
                "blocks": [],
                "error": self._initialization_error or "OCR engine is not available",
                "engine": self._engine_name
            }

        try:
            import pypdfium2 as pdfium
            if isinstance(pdf_source, bytes):
                doc = pdfium.PdfDocument(pdf_source)
            else:
                p = Path(str(pdf_source).strip())
                if not p.exists():
                    from rag.document_store import CANDIDATE_SEARCH_DIRS, BASE_DIR
                    found_p = None
                    for c_dir in CANDIDATE_SEARCH_DIRS + [BASE_DIR, BASE_DIR / "workspace", BASE_DIR / "workspace" / "reports", BASE_DIR.parent]:
                        cand = (c_dir / p.name).resolve()
                        if cand.exists() and cand.is_file():
                            found_p = cand
                            break
                    if found_p:
                        p = found_p
                    else:
                        return {"success": False, "text": "", "error": f"PDF file not found: {pdf_source}"}
                doc = pdfium.PdfDocument(str(p.resolve()))

            all_page_texts = []
            all_blocks = []
            confidences = []
            total_pages = len(doc)
            pages_to_process = min(total_pages, max_pages)

            for idx in range(pages_to_process):
                page = doc[idx]
                pil_img = page.render(scale=2.0).to_pil()
                page_res = self.extract_text(pil_img)
                if page_res.get("text"):
                    all_page_texts.append(f"--- Page {idx + 1} ---\n{page_res['text']}")
                for b in page_res.get("blocks", []):
                    b_copy = dict(b)
                    b_copy["page"] = idx + 1
                    all_blocks.append(b_copy)
                if page_res.get("confidence"):
                    confidences.append(page_res["confidence"])

            combined_text = "\n\n".join(all_page_texts).strip()
            avg_conf = round(sum(confidences) / len(confidences), 3) if confidences else 0.0
            duration = round(time.time() - start_time, 2)
            logger.info(f"[OCR] PDF extraction completed: {pages_to_process}/{total_pages} pages in {duration}s | text_len={len(combined_text)}")

            return {
                "success": True,
                "text": combined_text,
                "confidence": avg_conf,
                "blocks": all_blocks,
                "lines": all_blocks,
                "line_count": len(all_blocks),
                "page_count": total_pages,
                "pages_processed": pages_to_process,
                "duration_seconds": duration,
                "engine": self._engine_name
            }
        except Exception as e:
            logger.error(f"[OCR] PDF extraction error: {e}", exc_info=True)
            return {
                "success": False,
                "text": "",
                "confidence": 0.0,
                "blocks": [],
                "error": str(e),
                "engine": self._engine_name
            }


# Global singleton OCR service instance
ocr_service = OCRService()
