from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from PIL import Image
import io

from oath2 import get_current_user
from model import dekaiImg0,dekaiIMG1

router = APIRouter(
    prefix="/vision",
    tags=["vision"]
)


@router.post("/analyze")
async def analyze_image(
    image: UploadFile = File(...),
    #current_user = Depends(get_current_user)
):
    try:
        print(f"📷 Received file: {image.filename}, type: {image.content_type}")
        
        if not image.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Invalid image type")

        contents = await image.read()
        print(f"📦 File size: {len(contents)} bytes")

        pil_image = Image.open(io.BytesIO(contents)).convert("RGB")
        caption = dekaiIMG1.predict_landmark(pil_image)

        return {
            "engine": "dekai-img-1",
            "The landmark is ": caption
        }

    except Exception as e:
        print(f"🔥 Error in /vision/analyze: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

