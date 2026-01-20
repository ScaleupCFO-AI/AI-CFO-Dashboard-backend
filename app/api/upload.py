from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import tempfile
import os
import traceback

from app.ingestion.ingest_financial_files import ingest_financial_file
from app.queries.fetch_recent_facts import fetch_recent_facts
from app.queries.fetch_recent_summaries import fetch_recent_summaries

router = APIRouter()


@router.post("/upload")
async def upload_financial_file(
    company_name: str = Form(...),
    user_email: str = Form(...),      # 🔑 REQUIRED
    file: UploadFile = File(...),
):
    print("🔹 /upload called")
    print("Company name:", company_name)
    print("User email:", user_email)
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

        result = ingest_financial_file(
            file_path=tmp_path,
            user_email=user_email,       # 🔑 PASS IT
            company_name=company_name,
            source_type="csv",           # explicit, deterministic
            source_grain="monthly",
        )

        print("Ingestion succeeded. Company ID:", result["company_id"])

        facts = fetch_recent_facts(result["company_id"], limit=20)
        summaries = fetch_recent_summaries(result["company_id"], limit=5)

        return {
            "status": "success",
            "company_id": result["company_id"],
            "message": result["message"],
            "preview": {
                "facts_inserted": facts,
                "summaries_generated": summaries,
            },
        }

    

    except Exception as e:
        print("❌ ERROR DURING UPLOAD")
        traceback.print_exc()

        raise HTTPException(
            status_code=400,
            detail={
                "error_type": e.__class__.__name__,
                "message": str(e) or "Unknown error",
            },
        )


    finally:
        if "tmp_path" in locals() and os.path.exists(tmp_path):
            os.remove(tmp_path)
            print("Temp file cleaned up")
