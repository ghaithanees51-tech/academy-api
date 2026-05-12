from google import genai
from django.conf import settings


def extract_arabic_text_from_pdf(pdf_path: str) -> dict:
    client = genai.Client(api_key=settings.GEMINI_API_KEY)

    uploaded_file = client.files.upload(file=pdf_path)

    prompt = """
    You are reading an Arabic PDF document.

    Extract the Arabic text from this PDF.
    Then create a short Arabic summary.

    Return the result in this exact format:

    ARABIC_TEXT:
    extracted text here

    SUMMARY:
    summary here
    """

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            uploaded_file,
            prompt,
        ],
    )

    text = response.text or ""

    arabic_text = text
    summary = ""

    if "SUMMARY:" in text:
        parts = text.split("SUMMARY:", 1)
        arabic_text = parts[0].replace("ARABIC_TEXT:", "").strip()
        summary = parts[1].strip()

    return {
        "arabic_text": arabic_text,
        "summary": summary,
    }


_MAX_TEXT_CHARS = 40_000  # ~20k Arabic tokens — well within Gemini's context window


def answer_question_from_arabic_text(*, arabic_text: str, question: str, title: str = "") -> str:
    client = genai.Client(api_key=settings.GEMINI_API_KEY)

    # Truncate to avoid hitting token/payload limits on large extractions
    truncated = arabic_text[:_MAX_TEXT_CHARS]
    if len(arabic_text) > _MAX_TEXT_CHARS:
        truncated += "\n\n[... النص مقتطع لأغراض المعالجة ...]"

    prompt = f"""أنت مساعد متخصص في الإجابة عن الأسئلة المتعلقة بالمطبوعات العربية.

عنوان الإصدار:
{title or "غير معروف"}

استخدم النص العربي المستخرج أدناه فقط للإجابة عن سؤال المستخدم.
إذا لم تتوفر الإجابة في النص، أفد بأن النص لا يحتوي على معلومات كافية.
أجب باللغة العربية بشكل موجز وواضح.

النص العربي المستخرج:
{truncated}

سؤال المستخدم:
{question}
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    return (response.text or "").strip()