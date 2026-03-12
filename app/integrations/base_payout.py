from abc import ABC, abstractmethod
from typing import Dict, Any


class BasePayoutProvider(ABC):

    # ---------------------------------------------------------
    # Main method used by services
    # ---------------------------------------------------------
    @abstractmethod
    def disburse(
        self,
        amount: float,
        account_number: str,
        ifsc: str,
        name: str,
        reference_id: str
    ) -> Dict[str, Any]:
        """
        Executes payout to beneficiary.
        Must return payout response.
        """
        pass

    # ---------------------------------------------------------
    # Provider-specific methods
    # ---------------------------------------------------------
    @abstractmethod
    def create_contact(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def create_fund_account(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def initiate_payout(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        pass