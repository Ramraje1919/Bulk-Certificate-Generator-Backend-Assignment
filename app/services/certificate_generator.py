from pathlib import Path
from datetime import date
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

from app.core.config import settings
from app.utils.qr_generator import generate_qr_image


class CertificateGenerator:
    """
    Generates high-resolution, beautifully styled landscape A4 PDF certificates
    with dynamic verification QR codes, decorative borders, and institutional branding.
    """

    # Palette
    NAVY = colors.HexColor("#0F172A")       # Deep slate navy
    GOLD = colors.HexColor("#D97706")       # Warm amber/gold
    MUTED_GOLD = colors.HexColor("#F59E0B") # Accent gold
    SLATE = colors.HexColor("#475569")      # Muted body slate
    LIGHT_BG = colors.HexColor("#F8FAFC")   # Cream/off-white background
    BORDER_DARK = colors.HexColor("#1E293B")
    BORDER_GOLD = colors.HexColor("#B45309")

    @classmethod
    def generate_pdf(
        cls,
        output_path: Path,
        recipient_name: str,
        event_name: str,
        issued_by: str,
        issue_date: date,
        certificate_id: str,
        verification_url: Optional[str] = None,
    ) -> Path:
        """
        Render and save the certificate PDF to output_path.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if not verification_url:
            verification_url = f"{settings.BASE_URL}{settings.API_V1_STR}/verify/{certificate_id}"

        # Dimensions: 841.89 x 595.27 points
        page_width, page_height = landscape(A4)
        c = canvas.Canvas(str(output_path), pagesize=landscape(A4))
        c.setTitle(f"Certificate - {recipient_name}")
        c.setAuthor(issued_by)
        c.setSubject(event_name)

        # 1. Background Fill
        c.setFillColor(colors.HexColor("#FCFBF7"))  # Subtle elegant parchment
        c.rect(0, 0, page_width, page_height, stroke=0, fill=1)

        # 2. Decorative Double Border
        # Outer border
        c.setStrokeColor(cls.BORDER_DARK)
        c.setLineWidth(4)
        c.rect(24, 24, page_width - 48, page_height - 48)

        # Inner gold border
        c.setStrokeColor(cls.BORDER_GOLD)
        c.setLineWidth(1.5)
        c.rect(30, 30, page_width - 60, page_height - 60)

        # Subtle decorative inner line
        c.setStrokeColor(colors.HexColor("#E2E8F0"))
        c.setLineWidth(0.5)
        c.rect(34, 34, page_width - 68, page_height - 68)

        # 3. Corner Ornaments (Classic architectural corner brackets)
        cls._draw_corner_accents(c, page_width, page_height)

        # 4. Top Brand / Organization Badge
        center_x = page_width / 2.0

        c.setFillColor(cls.GOLD)
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(center_x, page_height - 75, "★  GLOBAL RECOGNITION OF EXCELLENCE  ★")

        # 5. Header: CERTIFICATE OF COMPLETION
        c.setFillColor(cls.NAVY)
        c.setFont("Helvetica-Bold", 32)
        c.drawCentredString(center_x, page_height - 118, "CERTIFICATE OF COMPLETION")

        # Decorative Divider Line
        c.setStrokeColor(cls.GOLD)
        c.setLineWidth(2)
        c.line(center_x - 140, page_height - 132, center_x + 140, page_height - 132)

        # 6. Presentation Text
        c.setFillColor(cls.SLATE)
        c.setFont("Helvetica", 13)
        c.drawCentredString(center_x, page_height - 165, "THIS IS PROUDLY PRESENTED TO")

        # 7. Recipient Name
        c.setFillColor(cls.NAVY)
        c.setFont("Helvetica-Bold", 28)
        # Handle long recipient names safely
        name_font_size = 28
        if len(recipient_name) > 30:
            name_font_size = 22
        elif len(recipient_name) > 40:
            name_font_size = 18
        c.setFont("Helvetica-Bold", name_font_size)
        c.drawCentredString(center_x, page_height - 215, recipient_name)

        # Underline under name
        c.setStrokeColor(colors.HexColor("#CBD5E1"))
        c.setLineWidth(1)
        name_line_width = min(len(recipient_name) * 12 + 60, 420)
        c.line(center_x - name_line_width / 2, page_height - 225, center_x + name_line_width / 2, page_height - 225)

        # 8. Achievement Description
        c.setFillColor(cls.SLATE)
        c.setFont("Helvetica", 13)
        c.drawCentredString(
            center_x,
            page_height - 255,
            "for successfully completing all curriculum requirements and demonstrating mastery in"
        )

        # 9. Course / Event Name
        c.setFillColor(cls.NAVY)
        c.setFont("Helvetica-Bold", 20)
        # Break into multiple lines if exceptionally long
        if len(event_name) > 55:
            c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(center_x, page_height - 290, event_name)

        # 10. Issuance Metadata (Date & Issued By Signatures)
        formatted_date = issue_date.strftime("%B %d, %Y") if hasattr(issue_date, "strftime") else str(issue_date)

        # Left Signature Column: Issue Date
        c.setStrokeColor(colors.HexColor("#94A3B8"))
        c.setLineWidth(1)
        c.line(90, 140, 250, 140)

        c.setFillColor(cls.NAVY)
        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(170, 150, formatted_date)

        c.setFillColor(cls.SLATE)
        c.setFont("Helvetica", 9)
        c.drawCentredString(170, 126, "DATE OF ISSUANCE")

        # Right Signature Column: Issued By
        c.line(page_width - 250, 140, page_width - 90, 140)

        c.setFillColor(cls.NAVY)
        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(page_width - 170, 150, issued_by)

        c.setFillColor(cls.SLATE)
        c.setFont("Helvetica", 9)
        c.drawCentredString(page_width - 170, 126, "AUTHORIZED SIGNATURE")

        # 11. Center Institutional Seal Graphic
        cls._draw_golden_seal(c, center_x, 145)

        # 12. QR Code & Verification Info (Bottom Center-Left / Bottom Area)
        qr_img = generate_qr_image(verification_url, box_size=4, border=1)
        qr_reader = ImageReader(qr_img)
        qr_x = 55
        qr_y = 45
        qr_size = 55
        c.drawImage(qr_reader, qr_x, qr_y, width=qr_size, height=qr_size)

        # Verification Text beside QR
        c.setFillColor(cls.SLATE)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(qr_x + qr_size + 10, qr_y + 42, "OFFICIAL VERIFICATION")

        c.setFont("Helvetica", 7.5)
        c.drawString(qr_x + qr_size + 10, qr_y + 28, "Scan QR to verify certificate authenticity")
        c.drawString(qr_x + qr_size + 10, qr_y + 14, f"or visit: {verification_url}")

        # 13. Certificate ID (Bottom Right)
        c.setFont("Helvetica-Bold", 8)
        c.setFillColor(cls.SLATE)
        c.drawRightString(page_width - 55, qr_y + 28, f"CERTIFICATE ID: {certificate_id}")
        c.setFont("Helvetica", 7)
        c.drawRightString(page_width - 55, qr_y + 14, "Secured with Tamper-Evident Digital Verification")

        c.save()
        return output_path

    @classmethod
    def _draw_corner_accents(cls, c: canvas.Canvas, width: float, height: float) -> None:
        """
        Draw elegant ornamental geometric corner markings.
        """
        c.setStrokeColor(cls.BORDER_GOLD)
        c.setLineWidth(2)
        offset = 30
        arm = 18

        # Top-Left
        c.line(offset, height - offset - arm, offset, height - offset)
        c.line(offset, height - offset, offset + arm, height - offset)

        # Top-Right
        c.line(width - offset - arm, height - offset, width - offset, height - offset)
        c.line(width - offset, height - offset, width - offset, height - offset - arm)

        # Bottom-Left
        c.line(offset, offset + arm, offset, offset)
        c.line(offset, offset, offset + arm, offset)

        # Bottom-Right
        c.line(width - offset - arm, offset, width - offset, offset)
        c.line(width - offset, offset, width - offset, offset + arm)

    @classmethod
    def _draw_golden_seal(cls, c: canvas.Canvas, cx: float, cy: float) -> None:
        """
        Draw an embossed golden seal emblem in the lower center.
        """
        # Outer gold ring
        c.setFillColor(colors.HexColor("#FEF3C7"))
        c.setStrokeColor(cls.GOLD)
        c.setLineWidth(1.5)
        c.circle(cx, cy, 32, stroke=1, fill=1)

        # Inner ring
        c.setStrokeColor(cls.BORDER_GOLD)
        c.setLineWidth(0.8)
        c.circle(cx, cy, 27, stroke=1, fill=0)

        # Star icon and text inside seal
        c.setFillColor(cls.BORDER_GOLD)
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(cx, cy + 5, "★ VERIFIED ★")
        c.setFont("Helvetica-Bold", 7)
        c.drawCentredString(cx, cy - 8, "EXCELLENCE")
