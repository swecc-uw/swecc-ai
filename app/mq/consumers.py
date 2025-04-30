# Declare consumers here
from . import consumer as mq_consumer
import json
import logging
logger = logging.getLogger(__name__)
from ..aws.s3 import S3Client
from ..llm.gemini import Gemini
from .producers import finish_review


RESUME_PROMPT = """
You are a hiring manager for a software engineering team. You are reviewing a candidate's resume and you need to provide feedback on the resume.
Please provide a detailed review of the resume, including strengths and weaknesses. Also, provide a score from 1 to 10 based on the following criteria:
1. Technical Skills: How well does the candidate's technical skills match the job requirements?
2. Experience: Does the candidate have relevant experience for the position?
3. Communication: How well does the candidate communicate their skills and experience?
4. Overall Impression: What is your overall impression of the candidate based on the resume?
Please provide your feedback in a structured format, including the score and a summary of your review.
The resume is in PDF format. Please extract the text from the PDF and use it as the input for your review.
"""

@mq_consumer(
  queue='ai.to-review-queue',
  exchange='swecc-ai-exchange',
  routing_key='to-review'
)
async def consume_to_review_message(body, properties):
  message_str = body.decode('utf-8')
  message: dict = json.loads(message_str)

  logger.info(f"Received message: {message}")

  file_key = message['key']
  s3_client = S3Client()
  file_content = s3_client.retrieve_object(file_key)

  gemini_client = Gemini()
  response = await gemini_client.prompt_file(bytes=file_content, prompt=RESUME_PROMPT, mime_type="application/pdf")

  logger.info(f"Gemini response: {response}")

  await finish_review({
    "feedback": response,
    "key": file_key
  })
