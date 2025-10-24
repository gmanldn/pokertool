"""Ensemble OCR combining Tesseract and EasyOCR."""
import logging
from typing import Tuple, Optional
import numpy as np

logger = logging.getLogger(__name__)

class EnsembleOCR:
    """Combine multiple OCR engines for better accuracy."""
    
    def __init__(self):
        self.engines = ['tesseract', 'easyocr']
        self.weights = {'tesseract': 0.6, 'easyocr': 0.4}
    
    def recognize_text(self, image: np.ndarray) -> Tuple[str, float]:
        """Recognize text using ensemble of OCR engines."""
        results = []
        
        # Tesseract result
        tesseract_text, tesseract_conf = self._tesseract_ocr(image)
        results.append((tesseract_text, tesseract_conf, self.weights['tesseract']))
        
        # EasyOCR result (if available)
        try:
            easyocr_text, easyocr_conf = self._easyocr_ocr(image)
            results.append((easyocr_text, easyocr_conf, self.weights['easyocr']))
        except:
            pass
        
        # Combine results
        best_text, best_conf = self._combine_results(results)
        return best_text, best_conf
    
    def _tesseract_ocr(self, image: np.ndarray) -> Tuple[str, float]:
        """Run Tesseract OCR."""
        try:
            import pytesseract
            text = pytesseract.image_to_string(image)
            return text.strip(), 0.85
        except:
            return "", 0.0
    
    def _easyocr_ocr(self, image: np.ndarray) -> Tuple[str, float]:
        """Run EasyOCR."""
        try:
            import easyocr
            reader = easyocr.Reader(['en'])
            results = reader.readtext(image)
            if results:
                return results[0][1], results[0][2]
        except:
            pass
        return "", 0.0
    
    def _combine_results(self, results) -> Tuple[str, float]:
        """Combine OCR results with weighted voting."""
        if not results:
            return "", 0.0
        
        # Return result with highest weighted confidence
        best = max(results, key=lambda x: x[1] * x[2])
        return best[0], best[1]
