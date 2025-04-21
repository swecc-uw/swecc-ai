# Declare consumers here
from . import consumer as mq_consumer

import logging
logger = logging.getLogger(__name__)

# Filler function for now
@mq_consumer(
  queue='to-review-queue',
  exchange='ai',
  routing_key='to-review'
)
async def consume_to_review_message(body, properties):
  message = body.decode('utf-8')
  logger.info(f"Received message from to-review queue: {message}")