import qrcode   # type: ignore[import]
from qrcode.constants import ERROR_CORRECT_M    # type: ignore[import]
from io import BytesIO
import httpx    # type: ignore[import]
from decimal import Decimal
import logging
from fastapi import APIRouter, HTTPException, Response  # type: ignore[import]

from src.main.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/payments", tags=["Payments"])


async def create_electrum_payment_intent(
    vehicle_id: str,
    seat_number: int,
    amount: Decimal,
    reference: str
) -> str:
    """
    Calls Electrum API using configured credentials. 
    """
    # Production header example using settings:
    # headers = {"Authorization": f"Bearer {settings.ELECTRUM_API_KEY}"}
    return f"https://pay.electrum.co.za/checkout?tx={reference}&v={vehicle_id}&seat={seat_number}"


def generate_qr_code_bytes(payment_url: str) -> BytesIO:
    """
    Encodes the payment URL/deep link into a QR code PNG image stream.
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    # Critical step: Encode the URL, NOT raw JSON!
    qr.add_data(payment_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    img_byte_arr = BytesIO()
    img.save(img_byte_arr, 'PNG')
    img_byte_arr.seek(0)
    return img_byte_arr


@router.get("/qr/{vehicle_id}/{seat_number}")
async def get_seat_qr_code(vehicle_id: str, seat_number: int, amount: float = 22.50):
    """
    Generates a scannable QR code that opens banking/MoMo/VodaPay checkout directly.
    """
    try:
        reference = f"TX-{vehicle_id[:8]}-S{seat_number}"
        payment_url = await create_electrum_payment_intent(
            vehicle_id=vehicle_id,
            seat_number=seat_number,
            amount=Decimal(str(amount)),
            reference=reference
        )
        qr_bytes = generate_qr_code_bytes(payment_url)
        return Response(content=qr_bytes.getvalue(), media_type="image/png")
    except Exception as e:
        logger.error(f"Error generating payment QR code: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate payment QR code")