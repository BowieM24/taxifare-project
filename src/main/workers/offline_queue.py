import asyncio
import json
import logging
from aiobreaker import CircuitBreakerError

from src.main.database_src.redis import redis_client
from src.main.core.electrum_gateway import charge_commuter_account_via_electrum

logger = logging.getLogger("offline_queue_worker")

async def process_offline_transactions():
    """
    Continuous background loop that monitors Redis for offline transactions
    and attempts to process them when the Electrum gateway is healthy.
    """
    logger.info("[WORKER] Offline transaction queue worker started.")

    while True:
        try:
            # brpop blocks for 5 seconds waititng for a new transaction in the queue
            item = await redis_client.brpop("offline_ussd_transactions", timeout=5)

            if item:
                # item is a tuple: (queue_name, data)
                _, payload_str = item
                payload = json.loads(payload_str)

                try:
                    logger.info(f"[WORKER] Attempting to process queued fare for: {payload['phone_number']}")

                    # Attempt to hit the live gateway again
                    await charge_commuter_account_via_electrum(
                        amount=payload["amount"],
                        phone_number=payload["phone_number"],
                        vehicle_id=payload["vehicle_id"]
                    )
                    logger.info(f"[WORKER] SUCCESS - Cleared queued fare for {payload['phone_number']}")

                except CircuitBreakerError:
                    logger.warning(f"[WORKER] Gateway still down. Re-queueing {payload['phone_number']}...")
                    # Gateway is still failing. Push it back to the right side of the queue (FIFO)
                    await redis_client.lpush("offline_ussd_transactions", payload_str)

                    # Sleep for 60 seconds to give the bank time to recover before retrying
                    await asyncio.sleep(60)

                except Exception as e:
                    logger.error(f"[WORKER] FATAL ERROR processing transaction for {payload['phone_number']}: {e}", exc_info=True)
                    # Push unrecoverable errors to a dead-letter queue for manual developer review
                    await redis_client.lpush("dead_letter_ussd_transactions", payload_str)

        except asyncio.CancelledError:
            logger.info("[WORKER] Worker shutting down gracefully.")
            break
        except Exception as e:
            logger.error(f"[WORKER ERROR] Unexpected failure in queue loop: {e}")
            # Prevent rapid spinning on unexpected systemic failures
            await asyncio.sleep(5)