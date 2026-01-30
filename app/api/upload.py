from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import tempfile
import os
import traceback
import psycopg2
from dotenv import load_dotenv

from app.ingestion.ingest_financial_files import ingest_financial_file
from app.queries.fetch_recent_facts import fetch_recent_facts
from app.queries.fetch_recent_summaries import fetch_recent_summaries

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

router = APIRouter()


@router.post("/upload")
async def upload_financial_file(
    company_name: str = Form(...),
    user_email: str = Form(...),
    file: UploadFile = File(...),
):
    print("🔹 /upload called")
    print("Company name:", company_name)
    print("User email:", user_email)
    print("Original filename:", file.filename)

    suffix = os.path.splitext(file.filename)[1]

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            contents = await file.read()
            tmp.write(contents)
            tmp_path = tmp.name

        print("Temp file path:", tmp_path)

        # 1️⃣ Ingest file (DO NOT pass source_name)
        result = ingest_financial_file(
            file_path=tmp_path,
            user_email=user_email,
            company_name=company_name,
            source_type="csv",
            source_grain="monthly",
        )

        # 2️⃣ Attach ORIGINAL filename for evidence display
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE source_documents
                    SET original_filename = %s
                    WHERE id = (
                        SELECT id
                        FROM source_documents
                        WHERE company_id = %s
                        ORDER BY uploaded_at DESC
                        LIMIT 1
                    );

                    """,
                    (file.filename, result["company_id"])
                )
                conn.commit()

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
