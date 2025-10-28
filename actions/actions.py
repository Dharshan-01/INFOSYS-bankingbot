# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions

from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

class ActionHandleSpecificLoan(Action):
    """
    A custom action to handle specific loan questions.
    It checks for the 'loan_type' entity and provides a specific
    response, or a general one if no entity is found.
    """

    def name(self) -> Text:
        return "action_handle_specific_loan"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # Get the latest entity value for 'loan_type'
        loan_type = next(tracker.get_latest_entity_values("loan_type"), None)

        if not loan_type:
            # If no specific loan type is mentioned, give the general response
            dispatcher.utter_message(response="utter_ask_loan_info")
            return []

        # Normalize the entity value (e.g., 'home loan' -> 'home')
        loan_type = loan_type.lower()

        if "home" in loan_type or "house" in loan_type:
            dispatcher.utter_message(response="utter_loan_details_home")
        elif "auto" in loan_type or "car" in loan_type:
            dispatcher.utter_message(response="utter_loan_details_auto")
        elif "personal" in loan_type:
            dispatcher.utter_message(response="utter_loan_details_personal")
        else:
            # If the entity is something else, give the general response
            dispatcher.utter_message(response="utter_ask_loan_info")

        return []