from typing import Any

from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher

# 🎵 Hardcoded concert "database"
CONCERTS_DB = [
    {"artist": "The Strokes", "genre": "rock", "date": "2025-10-28"},
    {"artist": "Adele", "genre": "pop", "date": "2025-10-29"},
    {"artist": "Herbie Hancock", "genre": "jazz", "date": "2025-10-28"},
    {"artist": "Imagine Dragons", "genre": "rock", "date": "2025-10-30"},
    {"artist": "Norah Jones", "genre": "jazz", "date": "2025-10-29"},
    {"artist": "Billie Eilish", "genre": "pop", "date": "2025-10-30"},
]


class ActionFindConcertsByGenreAndDate(Action):
    def name(self) -> str:
        return "action_find_concerts_by_genre_and_date"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: dict[str, Any],
    ) -> list[dict[str, Any]]:
        start_date_str = tracker.get_slot("start_date")
        end_date_str = tracker.get_slot("end_date")

        try:
            # Filter concerts
            matching_concerts = []
            for concert in CONCERTS_DB:
                # Check date match (if specified) - LLM provides dates in YYYY-MM-DD format
                if start_date_str and end_date_str:
                    if not (start_date_str <= concert["date"] <= end_date_str):
                        continue

                matching_concerts.append(concert)

            # Format results
            if matching_concerts:
                concert_list = "\n".join(
                    [
                        f"{c['artist']} ({c['genre']}) on {c['date']}"
                        for c in matching_concerts
                    ]
                )
                date_info = ""
                if start_date_str and end_date_str:
                    date_info = f" between {start_date_str} and {end_date_str}"

                dispatcher.utter_message(
                    text=f"🎶 Here are the concerts I found{date_info}:\n{concert_list}"
                )
                return [SlotSet("matched_concerts", concert_list)]
            else:
                return [SlotSet("matched_concerts", [])]

        except Exception as e:
            dispatcher.utter_message(
                text=f"Sorry, I encountered an error searching for concerts: {str(e)}"
            )
            return [SlotSet("matched_concerts", [])]
