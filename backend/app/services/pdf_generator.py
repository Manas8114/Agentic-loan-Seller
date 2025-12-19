"""
PDF Generator Service

Generates professional sanction letter PDFs using ReportLab.
"""

from datetime import datetime
from typing import Optional, Tuple
from uuid import UUID
from io import BytesIO

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.loan_application import LoanApplication, ApplicationStatus
from app.models.customer import Customer
from app.schemas.loan import SanctionLetterResponse
from app.core.logging import get_logger


logger = get_logger(__name__)


class SanctionLetterGenerator:
    """Service for generating sanction letter PDFs."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def generate(self, application_id: UUID) -> SanctionLetterResponse:
        """
        Generate sanction letter for an approved application.
        
        Returns SanctionLetterResponse with download URL.
        """
        # Fetch application with customer
        result = await self.db.execute(
            select(LoanApplication).where(LoanApplication.id == application_id)
        )
        application = result.scalar_one_or_none()
        
        if not application:
            raise ValueError(f"Application not found: {application_id}")
        
        if application.status != ApplicationStatus.APPROVED:
            raise ValueError("Sanction letter can only be generated for approved applications")
        
        # Generate sanction ID
        sanction_id = self._generate_sanction_id(application.application_number)
        
        # Generate PDF
        pdf_bytes = await self._create_pdf(application, sanction_id)
        
        # In production, upload to S3 and get URL
        download_url = f"/api/v1/sanction/download/{sanction_id}"
        
        # Update application
        application.sanction_id = sanction_id
        application.sanction_letter_url = download_url
        application.sanctioned_at = datetime.utcnow()
        application.status = ApplicationStatus.SANCTIONED
        
        await self.db.commit()
        
        return SanctionLetterResponse(
            application_id=application_id,
            sanction_id=sanction_id,
            download_url=download_url,
            generated_at=datetime.utcnow()
        )
    
    async def get_pdf(self, application_id: UUID) -> Tuple[bytes, str]:
        """
        Get PDF bytes for download.
        
        Returns tuple of (pdf_bytes, filename).
        """
        result = await self.db.execute(
            select(LoanApplication).where(LoanApplication.id == application_id)
        )
        application = result.scalar_one_or_none()
        
        if not application or not application.sanction_id:
            raise ValueError("Sanction letter not found")
        
        pdf_bytes = await self._create_pdf(application, application.sanction_id)
        filename = f"sanction_letter_{application.sanction_id}.pdf"
        
        return pdf_bytes, filename
    
    async def get_preview_data(self, application_id: UUID) -> dict:
        """Get preview data for sanction letter."""
        result = await self.db.execute(
            select(LoanApplication).where(LoanApplication.id == application_id)
        )
        application = result.scalar_one_or_none()
        
        if not application:
            raise ValueError("Application not found")
        
        return {
            "application_number": application.application_number,
            "customer_name": application.customer.name if application.customer else "N/A",
            "approved_amount": application.approved_amount,
            "interest_rate": float(application.interest_rate) if application.interest_rate else None,
            "emi": application.emi,
            "tenure_months": application.tenure_months,
            "status": application.status.value
        }
    
    async def verify_sanction(self, sanction_id: str) -> Optional[object]:
        """Verify sanction letter authenticity."""
        result = await self.db.execute(
            select(LoanApplication).where(LoanApplication.sanction_id == sanction_id)
        )
        application = result.scalar_one_or_none()
        
        if not application:
            return None
        
        from types import SimpleNamespace
        return SimpleNamespace(
            application_number=application.application_number,
            customer_name=application.customer.name if application.customer else "N/A",
            amount=application.approved_amount,
            issued_date=application.sanctioned_at
        )
    
    def _generate_sanction_id(self, application_number: str) -> str:
        """Generate unique sanction ID."""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        return f"SL-{application_number}-{timestamp}"
    
    async def _create_pdf(self, application: LoanApplication, sanction_id: str) -> bytes:
        """
        Create PDF sanction letter.
        
        Uses ReportLab for PDF generation.
        """
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch, cm
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
            from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_JUSTIFY
        except ImportError:
            logger.warning("ReportLab not installed, returning placeholder PDF")
            return self._create_placeholder_pdf(application, sanction_id)
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*cm, bottomMargin=1*cm)
        
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Heading1'],
            fontSize=18,
            alignment=TA_CENTER,
            spaceAfter=20
        )
        
        heading_style = ParagraphStyle(
            'Heading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceBefore=15,
            spaceAfter=10
        )
        
        body_style = ParagraphStyle(
            'Body',
            parent=styles['Normal'],
            fontSize=11,
            alignment=TA_JUSTIFY,
            spaceAfter=8
        )
        
        right_style = ParagraphStyle(
            'Right',
            parent=styles['Normal'],
            fontSize=11,
            alignment=TA_RIGHT
        )
        
        story = []
        
        # Header
        story.append(Paragraph("LOAN SANCTION LETTER", title_style))
        story.append(Spacer(1, 0.3*inch))
        
        # Sanction details
        story.append(Paragraph(f"<b>Sanction ID:</b> {sanction_id}", body_style))
        story.append(Paragraph(f"<b>Date:</b> {datetime.utcnow().strftime('%d %B %Y')}", body_style))
        story.append(Paragraph(f"<b>Application No:</b> {application.application_number}", body_style))
        story.append(Spacer(1, 0.3*inch))
        
        # Customer details
        customer_name = application.customer.name if application.customer else "N/A"
        customer_address = "Address on record"
        
        story.append(Paragraph(f"<b>To,</b>", body_style))
        story.append(Paragraph(f"{customer_name}", body_style))
        story.append(Paragraph(customer_address, body_style))
        story.append(Spacer(1, 0.3*inch))
        
        # Subject
        story.append(Paragraph(
            f"<b>Subject: Sanction of Personal Loan of ₹{application.approved_amount:,}</b>",
            body_style
        ))
        story.append(Spacer(1, 0.2*inch))
        
        # Body
        story.append(Paragraph(
            f"Dear {customer_name.split()[0]},",
            body_style
        ))
        story.append(Paragraph(
            "We are pleased to inform you that your application for a Personal Loan has been "
            "sanctioned. The details of your loan are as follows:",
            body_style
        ))
        story.append(Spacer(1, 0.2*inch))
        
        # Loan details table
        loan_data = [
            ["Particulars", "Details"],
            ["Sanctioned Amount", f"₹{application.approved_amount:,}"],
            ["Interest Rate", f"{application.interest_rate}% p.a."],
            ["Tenure", f"{application.tenure_months} months"],
            ["EMI Amount", f"₹{application.emi:,}"],
            ["Processing Fee", f"₹{int(application.approved_amount * 0.02):,} (2%)"],
            ["Total Repayment", f"₹{application.emi * application.tenure_months:,}"],
        ]
        
        table = Table(loan_data, colWidths=[3*inch, 3*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a365d')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f7fafc')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 11),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ]))
        
        story.append(table)
        story.append(Spacer(1, 0.3*inch))
        
        # Terms and conditions
        story.append(Paragraph("<b>Terms and Conditions:</b>", heading_style))
        terms = [
            "This sanction is valid for 30 days from the date of issuance.",
            "The loan amount will be disbursed after completion of all documentation.",
            "EMI will be debited on the 5th of every month via standing instruction.",
            "Prepayment is allowed after 6 months with no prepayment charges.",
            "Late payment will attract a penalty of 2% on the overdue EMI amount.",
            "This loan is subject to standard terms as per the loan agreement.",
        ]
        
        for i, term in enumerate(terms, 1):
            story.append(Paragraph(f"{i}. {term}", body_style))
        
        story.append(Spacer(1, 0.5*inch))
        
        # Signature
        story.append(Paragraph("For Agentic Financial Services", body_style))
        story.append(Spacer(1, 0.5*inch))
        story.append(Paragraph("____________________", body_style))
        story.append(Paragraph("<b>Authorized Signatory</b>", body_style))
        
        # Footer
        story.append(Spacer(1, 0.5*inch))
        story.append(Paragraph(
            "<i>This is a system-generated document and does not require physical signature.</i>",
            ParagraphStyle('Footer', parent=styles['Normal'], fontSize=9, alignment=TA_CENTER)
        ))
        
        # Build PDF
        doc.build(story)
        
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return pdf_bytes
    
    def _create_placeholder_pdf(self, application: LoanApplication, sanction_id: str) -> bytes:
        """Create a simple placeholder when ReportLab is not available."""
        content = f"""
        LOAN SANCTION LETTER
        ====================
        
        Sanction ID: {sanction_id}
        Date: {datetime.utcnow().strftime('%d %B %Y')}
        Application: {application.application_number}
        
        LOAN DETAILS
        ------------
        Amount: INR {application.approved_amount:,}
        Rate: {application.interest_rate}% p.a.
        Tenure: {application.tenure_months} months
        EMI: INR {application.emi:,}
        
        This is a system-generated sanction letter.
        """
        
        return content.encode('utf-8')
