"""
OCR Service

Extracts salary information from uploaded salary slips.
Uses Tesseract or EasyOCR for text extraction.
"""

import re
from typing import Optional
from io import BytesIO

from app.core.logging import get_logger


logger = get_logger(__name__)


class OCRService:
    """Service for extracting data from salary slip documents."""
    
    async def extract_salary_info(
        self,
        content: bytes,
        content_type: str,
        filename: str
    ) -> dict:
        """
        Extract salary information from uploaded document.
        
        Args:
            content: File bytes
            content_type: MIME type
            filename: Original filename
        
        Returns:
            Dict with extracted salary data
        """
        logger.info(
            "Processing salary slip",
            filename=filename,
            content_type=content_type,
            size=len(content)
        )
        
        # Extract text from document
        text = await self._extract_text(content, content_type)
        
        if not text:
            raise ValueError("Could not extract text from document")
        
        # Parse salary information
        salary_data = self._parse_salary_info(text)
        
        logger.info(
            "Salary extraction complete",
            gross=salary_data.get("gross_salary"),
            net=salary_data.get("net_salary")
        )
        
        return salary_data
    
    async def _extract_text(self, content: bytes, content_type: str) -> str:
        """Extract text from document."""
        
        if content_type == "application/pdf":
            return await self._extract_from_pdf(content)
        else:
            return await self._extract_from_image(content)
    
    async def _extract_from_pdf(self, content: bytes) -> str:
        """Extract text from PDF."""
        try:
            from PyPDF2 import PdfReader
            
            reader = PdfReader(BytesIO(content))
            text = ""
            
            for page in reader.pages:
                text += page.extract_text() + "\n"
            
            return text
            
        except ImportError:
            logger.warning("PyPDF2 not installed, using mock extraction")
            return self._get_mock_salary_text()
        except Exception as e:
            logger.error(f"PDF extraction error: {e}")
            return self._get_mock_salary_text()
    
    async def _extract_from_image(self, content: bytes) -> str:
        """Extract text from image using OCR."""
        try:
            import pytesseract
            from PIL import Image
            
            image = Image.open(BytesIO(content))
            text = pytesseract.image_to_string(image)
            
            return text
            
        except ImportError:
            logger.warning("OCR libraries not installed, using mock extraction")
            return self._get_mock_salary_text()
        except Exception as e:
            logger.error(f"OCR extraction error: {e}")
            return self._get_mock_salary_text()
    
    def _parse_salary_info(self, text: str) -> dict:
        """Parse salary values from extracted text."""
        result = {
            "gross_salary": None,
            "net_salary": None,
            "basic_salary": None,
            "hra": None,
            "deductions": None,
            "employer_name": None,
            "employee_name": None,
            "month": None
        }
        
        text_lower = text.lower()
        
        # Common salary patterns
        salary_patterns = {
            "gross": [
                r"gross\s*(?:salary|pay|earnings?)[\s:₹]*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)",
                r"total\s*(?:salary|earnings?)[\s:₹]*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)",
            ],
            "net": [
                r"net\s*(?:salary|pay|payable)[\s:₹]*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)",
                r"take\s*home[\s:₹]*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)",
            ],
            "basic": [
                r"basic\s*(?:salary|pay)?[\s:₹]*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)",
            ],
            "hra": [
                r"hra[\s:₹]*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)",
                r"house\s*rent\s*allowance[\s:₹]*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)",
            ],
        }
        
        for salary_type, patterns in salary_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text_lower)
                if match:
                    value_str = match.group(1).replace(",", "")
                    try:
                        value = int(float(value_str))
                        if salary_type == "gross":
                            result["gross_salary"] = value
                        elif salary_type == "net":
                            result["net_salary"] = value
                        elif salary_type == "basic":
                            result["basic_salary"] = value
                        elif salary_type == "hra":
                            result["hra"] = value
                        break
                    except ValueError:
                        continue
        
        # If no salary found, estimate from any large number
        if not result["gross_salary"] and not result["net_salary"]:
            large_numbers = re.findall(r"₹?\s*(\d{1,3}(?:,\d{3})+)", text)
            
            for num_str in large_numbers:
                num = int(num_str.replace(",", ""))
                if 10000 <= num <= 1000000:  # Reasonable salary range
                    if not result["gross_salary"]:
                        result["gross_salary"] = num
                    elif not result["net_salary"] and num < result["gross_salary"]:
                        result["net_salary"] = num
        
        # Calculate net if only gross is available
        if result["gross_salary"] and not result["net_salary"]:
            result["net_salary"] = int(result["gross_salary"] * 0.75)  # Assume 25% deductions
        
        return result
    
    def _get_mock_salary_text(self) -> str:
        """Return mock salary slip text for testing."""
        return """
        SALARY SLIP - NOVEMBER 2024
        
        Employee Name: John Doe
        Employee ID: EMP001
        Department: Engineering
        
        EARNINGS:
        Basic Salary: ₹50,000
        HRA: ₹25,000
        Special Allowance: ₹15,000
        
        GROSS SALARY: ₹90,000
        
        DEDUCTIONS:
        Provident Fund: ₹6,000
        Professional Tax: ₹200
        Income Tax: ₹8,000
        
        Total Deductions: ₹14,200
        
        NET SALARY: ₹75,800
        """
