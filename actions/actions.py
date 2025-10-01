from typing import Any

from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher

# 🎵 Hardcoded concert "database"
CONCERTS_DB = [
    {"artist": "The Strokes", "genre": "rock", "date": "2025-09-28"},
    {"artist": "Adele", "genre": "pop", "date": "2025-09-29"},
    {"artist": "Herbie Hancock", "genre": "jazz", "date": "2025-09-28"},
    {"artist": "Imagine Dragons", "genre": "rock", "date": "2025-09-30"},
    {"artist": "Norah Jones", "genre": "jazz", "date": "2025-09-29"},
    {"artist": "Billie Eilish", "genre": "pop", "date": "2025-09-30"},
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
        artist = tracker.get_slot("artist")
        genre = tracker.get_slot("genre")
        start_date_str = tracker.get_slot("start_date")
        end_date_str = tracker.get_slot("end_date")
        exclude_keywords = tracker.get_slot("exclude_keywords")

        try:
            # Parse exclusion keywords
            excluded = []
            if exclude_keywords and exclude_keywords != "default":
                excluded = [kw.strip().lower() for kw in exclude_keywords.split()]

            # Filter concerts
            matching_concerts = []
            for concert in CONCERTS_DB:
                # Check artist match (if specified)
                if artist and artist != "any":
                    if concert["artist"].lower() != artist.lower():
                        continue

                # Check genre match (if specified)
                if genre and genre != "any":
                    if concert["genre"].lower() != genre.lower():
                        continue

                # Check date match (if specified) - LLM provides dates in YYYY-MM-DD format
                if (
                    start_date_str
                    and start_date_str != "any"
                    and end_date_str
                    and end_date_str != "any"
                ):
                    if not (start_date_str <= concert["date"] <= end_date_str):
                        continue

                # Check exclusions
                if any(
                    ex in concert["artist"].lower() or ex in concert["genre"].lower()
                    for ex in excluded
                ):
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
                if (
                    start_date_str
                    and start_date_str != "any"
                    and end_date_str
                    and end_date_str != "any"
                ):
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


class ActionBookConcertTicket(Action):
    def name(self) -> str:
        return "action_book_concert_ticket"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: dict[str, Any],
    ) -> list[dict[str, Any]]:
        selected_concert = tracker.get_slot("selected_concert")
        name = tracker.get_slot("name")
        email = tracker.get_slot("email")

        if not all([selected_concert, name, email]):
            dispatcher.utter_message(
                text="I need a few more details to complete your booking."
            )
            return []

        message = (
            f"🎫 Your ticket for *{selected_concert}* has been booked under the name *{name}*.\n"
            f"A confirmation email will be sent to: {email}"
        )

        dispatcher.utter_message(text=message)
        return []
