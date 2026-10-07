import qrcode
from PIL import Image


def generate_qr_image(url: str, box_size: int = 10, border: int = 2) -> Image.Image:
    """
    Generate a crisp QR code PIL Image for a given URL.
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=box_size,
        border=border,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#1E293B", back_color="white")
    return img.convert("RGB")
