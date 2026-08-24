import abc
import time
import uuid
from typing import Dict, Any, Optional

from security.capability_token import CapabilityPayload
from execution.schema import ExecutionReceipt

class PaymentExecutionProvider(abc.ABC):
    @abc.abstractmethod
    async def execute(self, capability: CapabilityPayload, args: Dict[str, Any]) -> ExecutionReceipt:
        pass

    @abc.abstractmethod
    async def get_health(self) -> Dict[str, Any]:
        pass
