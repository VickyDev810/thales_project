from fastapi import FastAPI, Form, HTTPException, Body, UploadFile, File
import uuid
import shutil
import os
from pydantic import BaseModel
from app.pipeline.anonymizer import anonymize_text, encrypted_store, anonymize_text_combined
from app.pipeline.crypto.utils import decrypt_with_private_key
from app.pipeline.pipeline import detect_pii
from app.image_pii_detector.image_anon import ImageAnonymizer 
from app.rag.rag import Rag
from typing import Optional
from app.llm_integration import LLMIntegration
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import numpy as np
import cv2
from io import BytesIO


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# MODELS
class DetectionRequest(BaseModel):
    text: str
    mode: str = "all"
    public_key: str  # PEM format

class AnonymizationRequest(BaseModel):
    text: str
    mode: str = "all"
    public_key: str

class AnonymizationRequestCustom(BaseModel):
    text: str
    mode: str = "all"
    public_key: str
    path: str

class DeAnonymizationRequest(BaseModel):
    encrypted_text: str  # base64 string
    private_key: str     # PEM format


class LLMProcessingRequest(BaseModel):
    text: str
    mode: str  # e.g., "strict" or "relaxed" for PII detection
    public_key: str
    private_key: str
    provider: str = "gemini"
    model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 1000
    system_prompt: Optional[str] = None



@app.post("/detect_pii")
def detect_endpoint(req: DetectionRequest):
    try:
        results = detect_pii(req.text, req.mode)
        return results
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/anonymize_pii")
def anonymize_endpoint(req: AnonymizationRequest):
    try:
        detection = detect_pii(req.text, req.mode)
        pii_results = []
        for results in detection.values():
            pii_results.extend(results)

        anonymized_text = anonymize_text(req.text, pii_results, req.public_key)
        return {"anonymized_text": anonymized_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.post("/denonymize_pii")
def denonymize_endpoint(req: DeAnonymizationRequest):
    try:
        text = req.encrypted_text
        # Replace placeholders with decrypted original values
        for placeholder, encrypted_val in encrypted_store.items():
            decrypted_val = decrypt_with_private_key(req.private_key, encrypted_val)
            text = text.replace(placeholder, decrypted_val)

        return {"deanonymized_text": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from fastapi import UploadFile, File

# In-memory "session"
PII_MAP_SESSIONS = {}

@app.post("/custom_pii_using_rag")
async def detect_pii_file(file: UploadFile = File(...)):
    temp_filename = f"/tmp/{uuid.uuid4()}.txt"
    with open(temp_filename, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    rag = Rag(temp_filename)
    session_id = str(uuid.uuid4())
    PII_MAP_SESSIONS[session_id] = rag.output_path

    os.remove(temp_filename)
    return {"session_id": session_id}


@app.post("/anonymize_pii_custom")
def anonymize_custom_endpoint(req: AnonymizationRequestCustom, session_id: str = Form(...)):
    try:
        path = PII_MAP_SESSIONS.get(session_id)
        if not path:
            raise HTTPException(status_code=404, detail="Invalid session ID or expired session.")

        detection = detect_pii(req.text, req.mode)
        pii_results = []
        for results in detection.values():
            pii_results.extend(results)

        anonymized_custom = anonymize_text_combined(
            text=req.text,
            builtin_pii_results=pii_results,
            public_key_pem=req.public_key,
            custom_pii_json_path=path
        )

        return {"anonymized_text": anonymized_custom}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process_secure_query")
def process_secure_llm(req: LLMProcessingRequest):
    try:
        # Step 1: Detect PII
        detection = detect_pii(req.text, req.mode)
        pii_results = [pii for group in detection.values() for pii in group]

        # Step 2: Anonymize the text
        anonymized_text = anonymize_text_combined(
            text=req.text,
            builtin_pii_results=pii_results,
            public_key_pem=req.public_key,
            custom_pii_json_path="/tmp/d02a0839-0c12-4345-a90f-371b5c695dc7.txt_pii_map.json"
        )
        # anonymized_text = anonymize_text(
        #     text = req.text,
        #     pii_results= pii_results,
        #     public_key_pem=req.public_key
        # )

        # Step 3: Generate LLM Response using placeholders
        llm = LLMIntegration(provider=req.provider, model=req.model)
        system_prompt = req.system_prompt or "You are a helpful assistant."
        llm_response = llm.generate_response(
            prompt=anonymized_text,
            system_message=system_prompt,
            temperature=req.temperature,
            max_tokens=req.max_tokens
        )

        # Step 4: Deanonymize the LLM response
        deanonymized_response = llm_response
        for placeholder, encrypted_val in encrypted_store.items():
            decrypted_val = decrypt_with_private_key(req.private_key, encrypted_val)
            deanonymized_response = deanonymized_response.replace(placeholder, decrypted_val)

        return {
            "original_text": req.text,
            "anonymized_text": anonymized_text,
            "llm_response": llm_response,
            "final_response": deanonymized_response
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/anonymize_image")
async def anonymize_image(
    file: UploadFile = File(...),
    mode: str = "regex",
    mask_type: str = "blur",
    ignore_safety: bool = False,
):
    try:
        # Read uploaded image into NumPy array
        contents = await file.read()
        np_img = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(np_img, cv2.IMREAD_COLOR)

        if image is None:
            raise HTTPException(status_code=400, detail="Invalid image file.")

        # Create an anonymizer and apply it
        anonymizer = ImageAnonymizer(mode=mode)
        masked_image = anonymizer.anonymize_image_array(
            image=image,
            mask_type=mask_type,
            ignore_safety=ignore_safety
        )

        # Convert masked image to streamable JPEG
        success, buffer = cv2.imencode(".jpg", masked_image)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to encode masked image.")

        return StreamingResponse(BytesIO(buffer.tobytes()), media_type="image/jpeg")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# @app.get("/query/{query}", response_model=FullQueryResponse)
# async def process_query_get(
#     query: str,
#     provider: Optional[str] = None,
#     model: Optional[str] = None,
#     temperature: Optional[float] = None,
#     max_tokens: Optional[int] = None,
#     anonymizer: NLPDataAnonymizer = Depends(get_anonymizer),
#     llm: LLMIntegration = Depends(get_llm),
#     prompt_generator: PromptGenerator = Depends(get_prompt_generator)
# ):
#     """Simple GET route to process a query passed directly in the path."""
#     try:
#         # Override LLM settings if provided
#         if provider:
#             llm = LLMIntegration(provider=provider, model=model)
#             prompt_generator = PromptGenerator(provider=provider)
            
#         # 1. Analyze and anonymize the query
#         sensitivity_report = anonymizer.analyze_sensitivity(query)
#         anonymized_query = anonymizer.anonymize(query)
        
#         # 2. Generate prompts for the LLM
#         system_prompt = prompt_generator.generate_system_prompt(sensitivity_report)
#         user_prompt = prompt_generator.generate_user_prompt(anonymized_query)
        
#         # 3. Get response from LLM
#         temp = temperature or config.get("llm", {}).get("temperature", 0.7)
#         tokens = max_tokens or config.get("llm", {}).get("max_tokens", 1000)
        
#         llm_response = llm.generate_response(
#             prompt=user_prompt,
#             system_message=system_prompt,
#             temperature=temp,
#             max_tokens=tokens
#         )
        
#         # 4. Deanonymize the response
#         deanonymized_response = anonymizer.deanonymize(llm_response)
        
#         # 5. Save mappings
#         if config.get("anonymizer", {}).get("save_mappings", True):
#             save_anonymizer_state(anonymizer)
        
#         return {
#             "original_query": query,
#             "anonymized_query": anonymized_query,
#             "sensitivity_report": sensitivity_report,
#             "placeholder_mapping": get_placeholder_mapping(anonymizer),
#             "formatted_report": format_sensitivity_report(sensitivity_report),
#             "llm_response": llm_response,
#             "deanonymized_response": deanonymized_response
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")
