import re
from datetime import datetime, timedelta
from typing import Any

import dateparser
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
        genre = tracker.get_slot("genre")
        raw_date = tracker.get_slot("date")

        if not genre or not raw_date:
            dispatcher.utter_message(
                text="Please specify both a music genre and a date or time range."
            )
            return []

        start_date, end_date = self.parse_date_or_range(raw_date)
        if not start_date or not end_date:
            dispatcher.utter_message(
                text=f"Sorry, I couldn't understand the date or range '{raw_date}'."
            )
            return []

        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")

        # Filter concerts by genre and date range
        matching_concerts = [
            concert
            for concert in CONCERTS_DB
            if concert["genre"].lower() == genre.lower()
            and start_date <= datetime.strptime(concert["date"], "%Y-%m-%d") <= end_date
        ]

        if matching_concerts:
            concert_list = "\n".join(
                [
                    f"{c['artist']} ({c['genre']}) on {c['date']}"
                    for c in matching_concerts
                ]
            )
            dispatcher.utter_message(
                text=f"🎶 Here are the concerts I found between {start_str} and {end_str}:\n{concert_list}"
            )
            return [
                SlotSet("matched_concerts", concert_list),
                SlotSet("date", f"{start_str} to {end_str}"),
            ]
        else:
            dispatcher.utter_message(
                text=f"Sorry, I couldn't find any {genre} concerts between {start_str} and {end_str}."
            )
            return [
                SlotSet("matched_concerts", []),
                SlotSet("date", f"{start_str} to {end_str}"),
            ]

    def parse_date_or_range(self, text: str) -> tuple[datetime, datetime]:
        now = datetime.now()

        # Check for "September" or "September 2025"
        month_match = re.search(
            r"\b(january|february|march|april|may|june|july|august|september|october|november|december)\b(?:\s+(\d{4}))?",
            text,
            re.IGNORECASE,
        )
        if month_match:
            month_name = month_match.group(1)
            year = int(month_match.group(2)) if month_match.group(2) else now.year
            month = datetime.strptime(month_name, "%B").month

            start_date = datetime(year, month, 1)
            if month == 12:
                end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = datetime(year, month + 1, 1) - timedelta(days=1)
            return start_date, end_date

        # Handle "this weekend"
        if "weekend" in text.lower():
            today = now.date()
            saturday = today + timedelta((5 - today.weekday()) % 7)
            sunday = saturday + timedelta(days=1)
            return datetime.combine(saturday, datetime.min.time()), datetime.combine(
                sunday, datetime.max.time()
            )

        # Handle "this week" or "next week"
        if "week" in text.lower():
            parsed = dateparser.parse(text)
            if parsed:
                start = parsed - timedelta(days=parsed.weekday())  # Monday
                end = start + timedelta(days=6)  # Sunday
                return start, end

        # Fallback: parse a single date
        parsed_date = dateparser.parse(text, settings={"PREFER_DATES_FROM": "future"})
        if parsed_date:
            return parsed_date, parsed_date

        return None, None


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
        date = tracker.get_slot("date")
        name = tracker.get_slot("name")
        email = tracker.get_slot("email")

        if not all([selected_concert, name, email]):
            dispatcher.utter_message(
                text="I need a few more details to complete your booking."
            )
            return []

        message = (
            f"🎫 Your ticket for *{selected_concert}* on {date} has been booked under the name *{name}*.\n"
            f"A confirmation email will be sent to: {email}"
        )

        dispatcher.utter_message(text=message)
        return []
