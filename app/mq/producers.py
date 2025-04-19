from . import producer as mq_producer

# Testing purposes only
@mq_producer(
    exchange='ai',
    routing_key='to-review'
)
async def produce_test_message(message):
    return message