from pathlib import Path
from datetime import date
from PIL import Image

from app.services.certificate_generator import CertificateGenerator
from app.utils.qr_generator import generate_qr_image
from app.utils.id_generator import generate_certificate_id, generate_verification_token


def test_id_generator():
    cert_id = generate_certificate_id()
    assert cert_id.startswith("CERT-")
    assert len(cert_id) > 15

    token = generate_verification_token()
    assert len(token) >= 32


def test_qr_generator():
    test_url = "https://example.com/api/v1/verify/CERT-12345"
    img = generate_qr_image(test_url)
    assert isinstance(img, Image.Image)
    assert img.size[0] > 0 and img.size[1] > 0


def test_certificate_pdf_generation(tmp_path: Path):
    target_pdf = tmp_path / "test_cert.pdf"
    result = CertificateGenerator.generate_pdf(
        output_path=target_pdf,
        recipient_name="Marie Curie",
        event_name="Quantum Computing Fellowship",
        issued_by="National Research Institute",
        issue_date=date(2026, 10, 7),
        certificate_id="CERT-TEST-998877",
        verification_url="http://localhost:8000/api/v1/verify/CERT-TEST-998877",
    )

    assert result.exists()
    assert result.stat().st_size > 1000  # PDF should be well-formed and non-trivial
    with open(result, "rb") as f:
        header = f.read(5)
        assert header == b"%PDF-"
