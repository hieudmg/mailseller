import asyncio
from typing import List
from app.models.user import Transaction


class TransactionHistoryProcessor:
    def __init__(self, db_session, interval=1):
        self.db = db_session
        self.interval = interval
        self.queue: List[Transaction] = []
        self.running = False

    def add(self, transaction: Transaction):
        self.queue.append(transaction)

    async def process(self):
        while self.running:
            if self.queue:
                self.db.add_all(self.queue)
                await self.db.commit()
                self.queue.clear()
            await asyncio.sleep(self.interval)

    async def start(self):
        self.running = True
        await self.process()

    def stop(self):
        self.running = False


transaction_history_processor: TransactionHistoryProcessor | None = None


def set_transaction_history_processor(processor: TransactionHistoryProcessor):
    global transaction_history_processor
    transaction_history_processor = processor


def get_transaction_history_processor() -> TransactionHistoryProcessor:
    return transaction_history_processor
