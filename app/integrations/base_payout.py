from abc import ABC, abstractmethod
from typing import Dict, Any


class BasePayoutProvider(ABC):

    @abstractmethod
    def create_contact(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def create_fund_account(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def initiate_payout(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        pass