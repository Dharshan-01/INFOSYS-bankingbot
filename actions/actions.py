from typing import Any, Text, Dict, List, Optional
from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import AllSlotsReset
import re
import logging

logger = logging.getLogger(__name__)


class PayBillForm(FormValidationAction):
    def name(self) -> Text:
        return "pay_bill_form"

    def _extract_amount(self, text: Optional[Text]) -> Optional[str]:
        if not text:
            return None
        text = text.replace(",", "")
        m = re.search(r"(\d+(?:\.\d+)?)", text)
        if not m:
            return None
        try:
            amount = float(m.group(1))
            if amount <= 0:
                return None
            # canonicalize: integer without .0
            if amount.is_integer():
                return str(int(amount))
            return str(amount)
        except ValueError:
            return None

    def _extract_bill_type(self, text: Optional[Text]) -> Optional[str]:
        if not text:
            return None
        val = text.lower()
        allowed = {
            "electricity": "electricity",
            "water": "water",
            "phone": "phone",
            "mobile": "phone",
            "internet": "internet",
            "gas": "gas",
            "credit card": "credit card",
            "creditcard": "credit card",
            "card": "credit card",
        }
        for k in allowed:
            if k in val:
                return allowed[k]
        return None

    def validate_bill_type(
        self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> Dict[Text, Any]:
        # Prefer explicit entity/slot value
        if slot_value:
            v = str(slot_value).strip()
            extracted = self._extract_bill_type(v)
            if extracted:
                return {"bill_type": extracted}

        # Try latest message text
        latest = tracker.latest_message.get("text")
        extracted = self._extract_bill_type(latest)
        if extracted:
            return {"bill_type": extracted}

        # ask again
        dispatcher.utter_message(response="utter_ask_bill_type")
        return {"bill_type": None}

    def validate_amount_of_money(
        self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> Dict[Text, Any]:
        # Prefer explicit entity/slot value
        if slot_value:
            v = str(slot_value).strip()
            amt = self._extract_amount(v)
            if amt:
                return {"amount_of_money": amt}

        # Try latest message text
        latest = tracker.latest_message.get("text")
        amt = self._extract_amount(latest)
        if amt:
            return {"amount_of_money": amt}

        dispatcher.utter_message(response="utter_ask_amount_of_money")
        return {"amount_of_money": None}


class LoanApplicationForm(FormValidationAction):
    def name(self) -> Text:
        return "loan_application_form"

    def validate_loan_type(
        self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> Dict[Text, Any]:
        if slot_value:
            v = str(slot_value).strip().lower()
            allowed = ["personal", "home", "auto", "car", "student"]
            for a in allowed:
                if a in v:
                    return {"loan_type": a}
            # if free text not matching, accept as-is (user intention)
            return {"loan_type": slot_value}
        dispatcher.utter_message(response="utter_ask_loan_type")
        return {"loan_type": None}

    def validate_applicant_name(
        self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> Dict[Text, Any]:
        if slot_value and len(str(slot_value).strip()) >= 2:
            return {"applicant_name": str(slot_value).strip()}
        dispatcher.utter_message(response="utter_ask_applicant_name")
        return {"applicant_name": None}


class ActionPayBillSubmit(Action):
    def name(self) -> Text:
        return "action_pay_bill_submit"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        bill_type = tracker.get_slot("bill_type")
        amount = tracker.get_slot("amount_of_money")

        missing = []
        if not bill_type:
            missing.append("bill_type")
            dispatcher.utter_message(response="utter_ask_bill_type")
        if not amount:
            missing.append("amount_of_money")
            dispatcher.utter_message(response="utter_ask_amount_of_money")

        if missing:
            logger.info("action_pay_bill_submit: missing slots %s", missing)
            # Let the form continue to collect missing info
            return []

        # Confirm and process (placeholder for real payment integration)
        dispatcher.utter_message(response="utter_bill_payment_details", bill_type=bill_type, amount_of_money=amount)
        dispatcher.utter_message(text=f"Processing payment of {amount} for your {bill_type} bill... ✓ Payment successful.")
        return [AllSlotsReset()]


class ActionLoanApplySubmit(Action):
    def name(self) -> Text:
        return "action_loan_apply_submit"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        loan_type = tracker.get_slot("loan_type")
        applicant = tracker.get_slot("applicant_name")

        missing = []
        if not loan_type:
            missing.append("loan_type")
            dispatcher.utter_message(response="utter_ask_loan_type")
        if not applicant:
            missing.append("applicant_name")
            dispatcher.utter_message(response="utter_ask_applicant_name")

        if missing:
            logger.info("action_loan_apply_submit: missing slots %s", missing)
            return []

        dispatcher.utter_message(response="utter_loan_details", loan_type=loan_type)
        dispatcher.utter_message(text=f"Thanks {applicant}. Your {loan_type} loan application has been submitted.")
        return [AllSlotsReset()]


class ActionTransferMoney(Action):
    def name(self) -> Text:
        return "action_transfer_money"

    def _extract_amount(self, text: Optional[Text]) -> Optional[str]:
        if not text:
            return None
        text = text.replace(",", "")
        m = re.search(r"(\d+(?:\.\d+)?)", text)
        if not m:
            return None
        try:
            amount = float(m.group(1))
            if amount <= 0:
                return None
            if amount.is_integer():
                return str(int(amount))
            return str(amount)
        except ValueError:
            return None

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        recipient = tracker.get_slot("recipient_name")
        amount = tracker.get_slot("amount_of_money")
        account = tracker.get_slot("account_type")

        # if user typed "transfer 500 to John" it may have filled slots already; if missing, ask
        if not recipient:
            dispatcher.utter_message(text="Who would you like to transfer money to?")
            return []
        if not amount:
            dispatcher.utter_message(text="How much would you like to transfer?")
            return []
        if not account:
            dispatcher.utter_message(text="Which account should the money come from (savings/checking)?")
            return []

        # Process transfer (placeholder)
        dispatcher.utter_message(text=f"Transferring {amount} from your {account} account to {recipient}... ✓ Transfer successful.")
        return [AllSlotsReset()]


class ActionGreet(Action):
    def name(self) -> Text:
        return "action_greet"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(response="utter_greet")
        return []