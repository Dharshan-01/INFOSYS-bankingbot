from typing import Any, Text, Dict, List
import logging
from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, AllSlotsReset

logger = logging.getLogger(__name__)

class ActionGreet(Action):
    def name(self) -> Text:
        return "action_greet"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(response="utter_greet")
        return []

class ActionCheckBalance(Action):
    def name(self) -> Text:
        return "action_check_balance"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        acct = tracker.get_slot("account_type")
        if not acct:
            dispatcher.utter_message(response="utter_ask_account_type")
            return [SlotSet("last_action", "check_balance")]
        balances = {"savings": 10000.0, "checking": 5000.0}
        bal = balances.get(str(acct).lower(), 0.0)
        dispatcher.utter_message(text=f"Your {acct} account balance is ${bal:,.2f}")
        return [SlotSet("last_action", None)]

class ValidateTransferMoneyForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_transfer_money_form"

    def validate_recipient_name(
        self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> Dict[Text, Any]:
        if slot_value and isinstance(slot_value, str) and slot_value.strip():
            return {"recipient_name": slot_value.strip()}
        dispatcher.utter_message(text="Please tell me the recipient's name.")
        return {"recipient_name": None}

    def validate_amount_of_money(
        self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> Dict[Text, Any]:
        try:
            amount = float(slot_value)
            if amount <= 0:
                dispatcher.utter_message(text="Amount must be greater than zero.")
                return {"amount_of_money": None}
            return {"amount_of_money": amount}
        except Exception:
            dispatcher.utter_message(text="Please provide a numeric amount (e.g. 500).")
            return {"amount_of_money": None}

    def validate_account_type(
        self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> Dict[Text, Any]:
        if not slot_value:
            dispatcher.utter_message(response="utter_ask_account_type")
            return {"account_type": None}
        if str(slot_value).lower() in ["savings", "checking"]:
            return {"account_type": str(slot_value).lower()}
        dispatcher.utter_message(text="Please choose 'savings' or 'checking'.")
        return {"account_type": None}

class ActionTransferMoneySubmit(Action):
    def name(self) -> Text:
        return "action_transfer_money_submit"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        recipient = tracker.get_slot("recipient_name")
        amount = tracker.get_slot("amount_of_money")
        account = tracker.get_slot("account_type") or "savings"
        if not recipient or not amount:
            dispatcher.utter_message(text="Transfer cancelled — missing info.")
            return []
        dispatcher.utter_message(response="utter_transfer_confirm", **{"recipient_name": recipient, "amount_of_money": amount, "account_type": account})
        return [AllSlotsReset()]

class ActionPayBillSubmit(Action):
    def name(self) -> Text:
        return "action_pay_bill_submit"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(text="Bill payment processed (mock).")
        return [AllSlotsReset()]

class ActionLoanApplySubmit(Action):
    def name(self) -> Text:
        return "action_loan_apply_submit"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(text="Loan application received (mock).")
        return [AllSlotsReset()]