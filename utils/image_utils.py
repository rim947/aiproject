# utils/image_utils.py
from PIL import Image
import io

def resize_and_compress_image(image_bytes: bytes, max_size: int = 1024) -> bytes:
    image = Image.open(io.BytesIO(image_bytes))
    
    # 이미지 리사이징 및 압축 처리
    image.thumbnail((max_size, max_size))
    output = io.BytesIO()
    image.save(output, format="JPEG", quality=85)
    
    return output.getvalue()
