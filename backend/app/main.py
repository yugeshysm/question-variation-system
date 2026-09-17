from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from backend.app.schemas import (
    VariationRequest,
    VariationResponse,
    VerifyRequest,
    VerifyResponse
)

from ai.question_analyzer import analyze_question
from ai.variation_generator import generate_variations
from ai.reliability_analyzer import verify_content

from database.connection import get_db
from database.crud import create_question, create_variation


# ============================================================
# FastAPI Application
# ============================================================

app = FastAPI(
    title="AI Assessment Generation & Reliability System",
    description=(
        "Integrated PS8 Question Variation Generation "
        "and PS2 AI Reliability Verification System"
    ),
    version="1.0.0"
)


from fastapi.responses import FileResponse
import os

# ============================================================
# Root Endpoint
# ============================================================

@app.get("/")
def root():
    frontend_path = os.path.join(os.path.dirname(__file__), "frontend", "index.html")
    if os.path.exists(frontend_path):
        return FileResponse(frontend_path)
    return {
        "message": "AI Assessment Generation & Reliability System API is running"
    }


# ============================================================
# PS8 — Question Variation Generation
# ============================================================

@app.post("/generate")
def generate_question_variations(
    request: VariationRequest,
    db: Session = Depends(get_db)
):
    """
    Generate question variations using PS8.
    """

    # Analyze seed question
    analysis = analyze_question(request.question)

    # Generate variations
    variations = generate_variations(
        request.question,
        request.num_variations,
        analysis
    )

    # Save seed question
    saved_question = create_question(
        db=db,
        seed_question=request.question,
        analysis=analysis,
        requested_variations=request.num_variations
    )

    # Save generated variations
    saved_variations = []

    for variation in variations:
        saved_variation = create_variation(
            db=db,
            question_id=saved_question.id,
            variation=variation
        )

        saved_variations.append(saved_variation)

    return {
        "seed_question": request.question,
        "question_id": saved_question.id,
        "requested_variations": request.num_variations,
        "analysis": analysis,
        "variations": variations,
        "saved_variations": len(saved_variations),
        "status": "generated_and_saved"
    }


# ============================================================
# PS2 — AI Reliability Verification
# ============================================================

@app.post(
    "/api/v1/verify",
    response_model=VerifyResponse
)
def verify_ai_content(request: VerifyRequest):
    """
    Analyze AI-generated content for reliability,
    hallucination, contradictions and unsupported claims.
    """

    result = verify_content(
        question=request.question,
        generated_answer=request.generated_answer,
        reference_text=request.reference_text
    )

    return result


# ============================================================
# PS2 — Health Endpoint
# ============================================================

@app.get("/api/v1/health")
def health_check():
    return {
        "status": "healthy",
        "service": "PS2 AI Reliability Verification"
    }