from fastapi import FastAPI, File, UploadFile, HTTPException
import whisper
import tempfile
import os
import logging

# Configure logging to output to stdout
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # Ensures logs go to stdout
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI()

# Log on startup to confirm logging works
logger.info("Starting Whisper API...")

model = whisper.load_model("medium")

@app.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    logger.info(f"Received file: {file.filename}, size: {file.size} bytes")
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
            contents = await file.read()
            tmp.write(contents)
            tmp_path = tmp.name
            logger.info(f"Saved file to {tmp_path}")
    except Exception as e:
        logger.error(f"Failed to save uploaded file: {e}")
        raise HTTPException(status_code=500, detail="Failed to save uploaded file") from e

    try:
        logger.info("Starting transcription...")
        result = model.transcribe(tmp_path, language="en", fp16=True)  # FP16 should work with GPU now
        logger.info("Transcription complete")
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {e}")
    finally:
        os.remove(tmp_path)

    logger.info(f"Transcription result: {result['text']}")
    return {"transcription": result["text"]}