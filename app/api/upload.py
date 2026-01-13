from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import tempfile
import os
import traceback

from app.ingestion.ingest_financial_files import ingest_financial_file

router = APIRouter()

@router.post("/upload")
async def upload_financial_file(
    company_name: str = Form(...),
    file: UploadFile = File(...),
):
    print("🔹 /upload called")
    print("Company name:", company_name)
    print("Filename:", file.filename)

    suffix = os.path.splitext(file.filename)[1]
    print("File suffix:", suffix)

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            contents = await file.read()
            print("File size (bytes):", len(contents))

            tmp.write(contents)
            tmp_path = tmp.name

        print("Temp file path:", tmp_path)

        company_id = ingest_financial_file(
            file_path=tmp_path,
            company_name=company_name,
        )

        print("Ingestion succeeded. Company ID:", company_id)

        return {
            "status": "success",
            "company_id": company_id
        }

    except Exception as e:
        print("❌ ERROR DURING UPLOAD")
        traceback.print_exc()   # 🔑 THIS IS THE KEY LINE
        raise HTTPException(status_code=400, detail=str(e))

    finally:
        if "tmp_path" in locals() and os.path.exists(tmp_path):
            os.remove(tmp_path)
            print("Temp file cleaned up")
