import logging
from pathlib import Path
from typing import List
import qrcode  # type: ignore[import]
from qrcode.constants import ERROR_CORRECT_H  # type: ignore[import]
from PIL import Image, ImageDraw  # type: ignore[import]

logger = logging.getLogger(__name__)

# Directory where generated stickers and PDFs are stored
ASSETS_OUTPUT_DIR = Path("generated_fleet_assets")


def generate_seat_sticker_image(vehicle_id: str, seat_number: int) -> Image.Image:
    """
    Creates a high-contrast, printable seat sticker image containing the
    actionable Electrum/TaxiFare payment deep link QR code and seat label.
    """
    reference = f"TX-{vehicle_id[:8].upper()}-S{seat_number}"
    checkout_url = (
        f"https://pay.electrum.co.za/checkout"
        f"?tx={reference}&v={vehicle_id}&seat={seat_number}"
    )

    # High error correction (H) ensures QR still scans if scratched in a taxi
    qr = qrcode.QRCode(
        version=1,
        error_correction=ERROR_CORRECT_H,
        box_size=12,
        border=4,
    )
    qr.add_data(checkout_url)
    qr.make(fit=True)

    # Extract the underlying PIL Image from the QRCode wrapper safely
    raw_qr = qr.make_image(ill_color="black", back_color="white")
    base_image: Image.Image = getattr(raw_qr, "_img", raw_qr)
    qr_img = Image.Image = base_image.convert("RGB")

    # Read dimensions as a tuple attribute (width, height)
    qr_width, qr_height = qr_img.size

    # Create a taller canvas to include branding and seat number text
    header_height = 80
    footer_height = 70
    canvas_height = qr_height + header_height + footer_height
    canvas = Image.new("RGB", (qr_width, canvas_height), "white")

    # Paste QR code onto the center of the canvas
    canvas.paste(qr_img, (0, header_height))

    # Draw text labels
    draw = ImageDraw.Draw(canvas)
    
    # Header: Brand & Vehicle ID
    draw.text(
        (qr_width // 2, 25),
        f"TaxiFare™ | {vehicle_id.upper()}",
        fill="black",
        anchor="mm"
    )
    draw.text(
        (qr_width // 2, 55),
        f"SCAN TO PAY FOR SEAT {seat_number}",
        fill="black",
        anchor="mm"
    )

    # Footer: USSD Fallback instruction
    draw.text(
        (qr_width // 2, qr_height + header_height + 30),
        f"No Data? Dial *120*8294# and enter Seat {seat_number}",
        fill="black",
        anchor="mm"
    )

    return canvas


def auto_generate_fleet_assets(vehicle_id: str, seat_count: int) -> dict:
    """
    Background worker task invoked by POST /fleet/register.
    Generates individual PNG stickers for each seat (1..seat_count)
    and compiles them into a single printable PDF manifest.
    """
    try:
        vehicle_dir = ASSETS_OUTPUT_DIR / vehicle_id
        vehicle_dir.mkdir(parents=True, exist_ok=True)

        sticker_images: List[Image.Image] = []

        for seat_num in range(1, seat_count + 1):
            sticker_img = generate_seat_sticker_image(vehicle_id, seat_num)
            
            # Save individual seat PNG
            png_path = vehicle_dir / f"seat_{seat_num:02d}_qr.png"
            sticker_img.save(png_path, format="PNG")
            sticker_images.append(sticker_img)

        # Compile all seat stickers into a single multi-page printable PDF
        pdf_path = vehicle_dir / f"{vehicle_id}_printable_stickers.pdf"
        if sticker_images:
            sticker_images[0].save(
                pdf_path,
                save_all=True,
                append_images=sticker_images[1:],
                resolution=300.0
            )

        logger.info(
            f"✓ Generated {seat_count} QR stickers and PDF sheet for {vehicle_id} at {vehicle_dir}"
        )
        return {
            "vehicle_id": vehicle_id,
            "stickers_generated": seat_count,
            "pdf_manifest": str(pdf_path)
        }

    except Exception as e:
        logger.error(f"Failed to generate fleet QR assets for {vehicle_id}: {e}")
        raise
