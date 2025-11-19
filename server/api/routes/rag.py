from fastapi import APIRouter, HTTPException
from qdrant_client.models import Filter, FieldCondition, MatchValue
from server.models.models import AnalyzeQuery
from server.connections import qdrant, SUPPLIER_DOC_COLLECTION
from server.ingestion.utils import embedder, call_llm, generate_ssr_prompt, parse_risk_assessment, RISK_TEMPLATE

router = APIRouter()


@router.post("/analyze")
def analyze_risk(data: AnalyzeQuery):
    user_query = data.query.strip()
    vendor_ids = data.vendor_ids

    if not user_query:
        raise HTTPException(400, "Query cannot be empty.")

    # SSR Step 1: Generate Hypothetical Analysis Paragraph
    ssr_prompt = generate_ssr_prompt(user_query)
    try:
        hypothetical_analysis = call_llm([{"role": "user", "content": ssr_prompt}], temperature=0.7, max_tokens=200)
    except Exception as e:
        raise HTTPException(500, f"SSR generation error: {e}")

    # SSR Step 2: Embed the Hypothetical Analysis
    ssr_embedding = embedder.embed_query(hypothetical_analysis)

    # SSR Step 3: Build filter for selected vendors
    vendor_filter = None
    if vendor_ids:
        vendor_filter = Filter(
            must=[
                FieldCondition(
                    key="vendor_id",
                    match=MatchValue(value=vid)
                ) for vid in vendor_ids
            ]
        )

    # SSR Step 4: Perform vector search using SSR embedding (top 8 chunks)
    try:
        search_result = qdrant.search(
            collection_name=SUPPLIER_DOC_COLLECTION,
            query_vector=ssr_embedding,
            limit=8,
            query_filter=vendor_filter
        )
    except Exception as e:
        raise HTTPException(500, f"Vector DB search error: {e}")

    if not search_result:
        return {"risk_level": "Low", "evidence": [], "summary": "No relevant material found."}

    # SSR Step 5: Aggregate content and pick top chunks
    scored_chunks = []
    for hit in search_result:
        score = float(hit.score)
        payload = hit.payload
        text = payload.get("text", "")

        # Threshold to avoid weak matches
        if score < 0.10:
            continue

        scored_chunks.append((text, payload.get("source", "Unknown")))

    if not scored_chunks:
        return {"risk_level": "Low", "evidence": [], "summary": "No sufficiently relevant content found."}

    # Keep only first 3 best matches
    context_blocks = [chunk for chunk, src in scored_chunks[:3]]

    # SSR Step 6: Compose final context
    full_context = "\n\n---\n\n".join(context_blocks)

    # SSR Step 7: Build prompt for LLM using Query + Context + Hypothetical Analysis
    prompt = RISK_TEMPLATE.format(
        context=full_context,
        query=user_query
    )

    # SSR Step 8: Call LLM for final risk assessment
    try:
        assessment_text = call_llm([
            {"role": "system", "content": "Provide risk assessment with level, summary, and evidence."},
            {"role": "user", "content": prompt}
        ], temperature=0)
    except Exception as e:
        raise HTTPException(500, f"LLM error: {e}")

    # SSR Step 9: Parse the assessment (simplified parsing)
    risk_level = parse_risk_assessment(assessment_text)

    summary = assessment_text  # For simplicity, use the whole text as summary

    # Extract evidence as document names
    evidence = sorted(list({
        src
        for _, src in scored_chunks[:3]
    }))

    return {
        "risk_level": risk_level,
        "evidence": evidence,
        "summary": summary
    }
