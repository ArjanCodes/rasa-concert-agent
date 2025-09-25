from datetime import datetime
from typing import Any

import parsedatetime
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

    def parse_date_or_range(self, date_str: str) -> tuple[datetime, datetime]:
        """
        Parses a date or natural language range using parsedatetime.
        Returns a (start_date, end_date) tuple.
        If it's a single day, start_date == end_date.
        """
        cal = parsedatetime.Calendar()
        time_struct, parse_status = cal.parse(date_str)

        if not parse_status:
            return None, None

        start_dt = datetime(*time_struct[:6])

        # Check if the expression is likely a range
        if "week" in date_str.lower():
            end_dt = start_dt + timedelta(days=6)
        elif "month" in date_str.lower():
            # go to next month, subtract one day to get end of this month
            year = start_dt.year
            month = start_dt.month
            if month == 12:
                end_dt = datetime(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_dt = datetime(year, month + 1, 1) - timedelta(days=1)
        elif "weekend" in date_str.lower():
            # start at Saturday
            weekday = start_dt.weekday()
            delta = (5 - weekday) % 7
            start_dt = start_dt + timedelta(days=delta)
            end_dt = start_dt + timedelta(days=1)  # Saturday + Sunday
        else:
            end_dt = start_dt  # default to single-day

        return start_dt, end_dt

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

        # Parse date or date range
        start_date, end_date = self.parse_date_or_range(raw_date)
        if not start_date or not end_date:
            dispatcher.utter_message(
                text=f"Sorry, I couldn't understand the date or range '{raw_date}'."
            )
            return []

        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")

        # Filter concerts by genre and date range
        matching_concerts = []
        for concert in CONCERTS_DB:
            concert_date = datetime.strptime(concert["date"], "%Y-%m-%d")
            if (
                concert["genre"].lower() == genre.lower()
                and start_date <= concert_date <= end_date
            ):
                matching_concerts.append(concert)

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
