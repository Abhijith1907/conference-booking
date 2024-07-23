from fastapi import APIRouter, Request, status
from models.conference import Conference, ConferenceBookingPayload, BookingStatus
from models.exceptions import (
    ConferenceExists,
    ConferenceDoesNotExist,
    UserDoesNotExist,
    NoSlotsInConference,
    ConferenceAlreadyStarted,
    BookingDoesNotExist,
    TimeToConfirmBookingExceeded,
)
from starlette.responses import JSONResponse
from app.api.v1.user import user_registry
from uuid import uuid4

from datetime import datetime

from app.utils.db_utils import LocalDB


router = APIRouter()

conference_registry = LocalDB("conference")

booking_registry = LocalDB("booking")

waitlist_registry = LocalDB("waitlist")

waitlist_confirmation_registry = LocalDB("waitlist_confirmation")


@router.get("{conference_name}")
def get_conference(conference_name: str):
    """
    gets conference
    """
    try:

        conference_exists = conference_registry.get_record(conference_name)
        if conference_exists == False:
            raise ConferenceDoesNotExist()

        resp = {"data": conference_exists}
        status_code = status.HTTP_200_OK

    except ConferenceDoesNotExist as e:
        resp = {"error": {"code": 404, "message": "Conference does not exists"}}
        status_code = status.HTTP_404_NOT_FOUND

    return JSONResponse(resp, status_code)


@router.post("")
def create_conference(conference: Conference, request: Request):
    """
    Creates a new conference with the given payload
    """
    conference = conference.dict(exclude_unset=True)

    try:
        start_time = datetime.strptime(
            conference["timing"]["start_ts"], "%Y-%m-%d %H:%M:%S"
        )
        end_time = datetime.strptime(
            conference["timing"]["end_ts"], "%Y-%m-%d %H:%M:%S"
        )
        if start_time > end_time:
            raise ValueError("start time cannot be greate than endtime")

        duration = end_time - start_time
        hours_difference = duration.total_seconds() / 3600
        if hours_difference > 12:
            raise ValueError("duration cannot be graeter than 12")

        conference_exists = conference_registry.get_record(conference["name"])
        if conference_exists == False:
            conference_record = conference_registry.create_record(conference, "name")
        else:
            raise ConferenceExists()

        resp = {"data": conference_record}
        status_code = status.HTTP_201_CREATED

    except ConferenceExists as e:
        resp = {"error": {"code": 409, "message": "Conference already exists"}}
        status_code = status.HTTP_409_CONFLICT

    return JSONResponse(resp, status_code=status_code)


@router.post("/{conference_name}/book")
def book_conference(conference_name: str, booking_payload: ConferenceBookingPayload):
    """
    Books a conference
    """

    try:
        booking_payload = booking_payload.dict(exclude_none=True)

        conference_exists = conference_registry.get_record(conference_name)
        if conference_exists == False:
            raise ConferenceDoesNotExist()

        user_exists = user_registry.get_record(booking_payload["user_id"])
        if user_exists == False:
            raise UserDoesNotExist()

        start_time = datetime.strptime(
            conference_exists["timing"]["start_ts"], "%Y-%m-%d %H:%M:%S"
        )
        if start_time < datetime.now():
            raise ConferenceAlreadyStarted()

        if conference_exists["available_slots"] < 1:
            booking_id = str(uuid4())
            booking_payload["booking_id"] = booking_id
            booking_payload["conference"] = conference_name
            booking_payload["status"] = BookingStatus.wailist
            booking_record = booking_registry.create_record(
                booking_payload, "booking_id"
            )

            waitlist_registry_exists = waitlist_registry.get_record(conference_name)
            if waitlist_registry_exists == False:
                waitlist_record = {
                    "conference": conference_name,
                    "booking_queue": [booking_id],
                }
                waitlist_registry.create_record(waitlist_record, "conference")
            else:
                waitlist_registry_exists["booking_queue"].append(booking_id)
                waitlist_registry.update_record(
                    conference_name, waitlist_registry_exists
                )

            raise NoSlotsInConference()

        booking_id = str(uuid4())
        booking_payload["booking_id"] = booking_id
        booking_payload["conference"] = conference_name
        booking_payload["status"] = BookingStatus.confirmed
        booking_record = booking_registry.create_record(booking_payload, "booking_id")

        conference_exists["available_slots"] -= 1
        update_conference = conference_registry.update_record(
            conference_exists["name"], conference_exists
        )

        resp = {"data": {"booking_id": booking_id}}
        status_code = status.HTTP_201_CREATED

    except ConferenceDoesNotExist as e:
        resp = {"error": {"code": 404, "message": "Conference does not exists"}}
        status_code = status.HTTP_404_NOT_FOUND

    except UserDoesNotExist as e:
        resp = {"error": {"code": 404, "message": "User does not exists"}}
        status_code = status.HTTP_404_NOT_FOUND

    except NoSlotsInConference as e:
        resp = {
            "error": {
                "code": 406,
                "message": f"no slots left in the conference added to the waitlist. use this booking id {booking_id} to track status",
            }
        }
        status_code = status.HTTP_406_NOT_ACCEPTABLE

    except ConferenceAlreadyStarted as e:
        resp = {"error": {"code": 406, "message": "Conference already started"}}
        status_code = status.HTTP_406_NOT_ACCEPTABLE

    return JSONResponse(resp, status_code)


@router.get("/{booking_id}/status")
def get_booking_status(booking_id):
    """
    gets the booking status for the given booking id
    """
    resp = {}
    try:
        booking_exists = booking_registry.get_record(booking_id)
        if booking_exists == False:
            raise BookingDoesNotExist()
        if booking_exists["status"] == BookingStatus.wailist:
            can_book = waitlist_confirmation_registry.get_record(booking_id)
            if can_book != False:
                moved_to_wailist = datetime.strptime(
                    can_book[booking_id], "%Y-%m-%d %H:%M:%S"
                )
                booking_time_left = datetime.now() - moved_to_wailist
                hours_difference = booking_time_left.total_seconds() / 3600
                if hours_difference > 1:
                    waitlist_confirmation_registry.delete_record(booking_id)
                    raise TimeToConfirmBookingExceeded()
                else:
                    booking_exists["time_left_confirm"] = booking_time_left

            elif can_book == False:
                waitlist = waitlist_registry.get_record(booking_exists["conference"])
                queue_num = waitlist["booking_queue"].index(booking_id)
                booking_exists["queue_number"] = queue_num

        resp = {"data": booking_exists}
        status_code = status.HTTP_200_OK

    except BookingDoesNotExist as e:
        resp = {"error": {"code": 404, "message": "Booking does not exist"}}
        status_code = status.HTTP_404_NOT_FOUND

    except TimeToConfirmBookingExceeded as e:
        resp = {"error": {"code": 404, "message": "Time to confirm booking exceeded"}}
        status_code = status.HTTP_406_NOT_ACCEPTABLE

    return JSONResponse(resp, status_code)


@router.delete("/{booking_id}/booking")
def cancel_booking(booking_id: str):
    """
    Cancels the booking for the given booking id
    """

    try:
        booking_exists = booking_registry.get_record(booking_id)
        if booking_exists == False:
            raise BookingDoesNotExist()

        if booking_exists["status"] == BookingStatus.confirmed:
            conference_name = booking_exists["conference"]
            conference = conference_registry.get_record(conference_name)
            conference["available_slots"] += 1
            conference_registry.update_record(conference_name, conference)

            waitlist = waitlist_registry.get_record(conference_name)
            first_booking = waitlist["booking_queue"].pop(0)
            time_now = datetime.now()
            current_time = time_now.strftime("%Y-%m-%d %H:%M:%S")
            waitlist_confirmation_record = {
                "booking_id": booking_id,
                "time": current_time,
            }
            waitlist_confirmation_registry.create_record(
                waitlist_confirmation_record, "booking_id"
            )

        elif booking_exists["status"] == BookingStatus.wailist:
            waitlist = waitlist_registry.get_record(conference_name)
            waitlist["booking_queue"].remove(booking_id)

        resp = {"message": f"cancelled booking {booking_id}"}
        status_code = status.HTTP_202_ACCEPTED

    except BookingDoesNotExist as e:
        resp = {"error": {"code": 404, "message": "Booking does not exists"}}
        status_code = status.HTTP_404_NOT_FOUND

    return JSONResponse(resp, status_code)


@router.post("/{booking_id}/confirm")
def confirm_booking(booking_id: str):
    """
    confirms the waitlisted booking
    """

    try:
        booking_exists = booking_registry.get_record(booking_id)
        if booking_exists == False:
            raise BookingDoesNotExist()

        if booking_exists["status"] == BookingStatus.confirmed:
            raise ValueError("booking already confirmed")

        elif booking_exists["status"] == BookingStatus.wailist:
            can_book = waitlist_confirmation_registry.get_record(booking_id)
            if can_book != False:
                moved_to_wailist = datetime.strptime(
                    can_book[booking_id], "%Y-%m-%d %H:%M:%S"
                )
                booking_time_left = datetime.now() - moved_to_wailist
                hours_difference = booking_time_left.total_seconds() / 3600
                if hours_difference > 1:
                    waitlist_confirmation_registry.delete_record(booking_id)
                    raise TimeToConfirmBookingExceeded()
                else:
                    booking_exists["status"] = BookingStatus.confirmed
                    update_booking = booking_registry.update_record(
                        booking_id, booking_exists
                    )

                    conference_name = booking_exists["conference"]
                    conference = conference_registry.get_record(conference_name)
                    conference["available_slots"] -= 1
                    conference_registry.update_record(
                        conference_name, conference_registry
                    )

                    waitlist_confirmation_registry.delete_record(booking_id)

            elif can_book == False:
                raise ValueError("cannot book now")

    except BookingDoesNotExist as e:
        resp = {"error": {"code": 404, "message": "Booking does not exists"}}
        status_code = status.HTTP_404_NOT_FOUND
