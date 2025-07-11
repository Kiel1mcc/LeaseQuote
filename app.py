import re
from io import BytesIO

import streamlit as st
from PIL import Image
from pyzbar.pyzbar import decode
import numpy as np
import easyocr

# Try to import the live camera component. The app still works if it's missing.
try:
    from streamlit_camera_input_live import camera_input_live
    HAS_LIVE = True
except Exception:
    HAS_LIVE = False

VIN_PATTERN = re.compile(r"^[A-HJ-NPR-Z0-9]{17}$")


def decode_barcode(image: Image.Image) -> str | None:
    """Return a VIN from a barcode if found."""
    for barcode in decode(image):
        value = barcode.data.decode("utf-8").strip().upper()
        if VIN_PATTERN.match(value):
            return value
    return None


@st.cache_resource
def get_ocr_reader():
    """Load the EasyOCR reader only once."""
    return easyocr.Reader(["en"], gpu=False)


def ocr_vin(image: Image.Image) -> str | None:
    """Extract a VIN from text in the image using OCR."""
    reader = get_ocr_reader()
    result = reader.readtext(np.array(image))
    for _, text, _ in result:
        candidate = text.upper().strip().replace(" ", "").replace("-", "")
        if VIN_PATTERN.match(candidate):
            return candidate
    return None


def process_image(image: Image.Image, method: str) -> None:
    """Decode VIN from the image using the selected method."""
    vin = decode_barcode(image) if method == "Barcode" else ocr_vin(image)
    if vin:
        st.success(f"Detected VIN: {vin}")
        st.session_state.vin = vin
    else:
        st.warning("No valid VIN detected. Try again.")


def main() -> None:
    st.title("VIN Scanner")
    st.write(
        "Scan a Vehicle Identification Number directly from your phone's camera."
    )

    method = st.radio("Detection method", ["Barcode", "OCR"], horizontal=True)

    live_label = (
        "Real-Time" if HAS_LIVE else "Real-Time (install streamlit-camera-input-live)"
    )
    mode = st.radio("Camera mode", ["Snapshot", live_label], horizontal=True)

    st.text_input("Detected VIN", key="vin")
    if st.button("Reset"):
        st.session_state.vin = ""
        st.experimental_rerun()

    if mode == "Snapshot" or not HAS_LIVE:
        picture = st.camera_input("Take a photo of the VIN")
        if picture:
            image = Image.open(picture)
            process_image(image, method)
    else:
        frame = camera_input_live()
        if frame:
            image = Image.open(BytesIO(frame))
            vin = decode_barcode(image) if method == "Barcode" else ocr_vin(image)
            if vin:
                st.session_state.vin = vin
                st.experimental_rerun()


if __name__ == "__main__":
    main()
