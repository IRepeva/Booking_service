from datetime import datetime
import uuid
from sqlalchemy import delete, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.future import select

from booking_api.models.booking import (
    EventShemaList, SeatSchema, BookingInput, BookingSchema, BookingInfoSchema
)
from booking_api.services.service_mixin import ServiceMixin
from booking_api.utils.exceptions import (
    ForbiddenException, BookingNotFoundException, EventNotFoundException,
    SeatNotFoundException, UniqueConflictException
)
from db.tables.booking import BookingObject
from db.tables import Seat
from db.tables import PurchasedMovie
from db.tables import Location
from db.tables import Event


class BookingService(ServiceMixin):

    async def get_events(self) -> list[EventShemaList]:
        query_seats = (
            select(BookingObject.seat_id).filter(BookingObject.event_id == Event.id)
        )
        query = (
            select(
                Event.id, Event.name, Event.start, Event.duration,
                PurchasedMovie.movie_name, Location.name.label("location_name"),
                Seat.id.label("seat_id"), Seat.row, Seat.seat, Seat.type
            )
            .select_from(Event)
            .join(
                PurchasedMovie, Event.movie_id == PurchasedMovie.movie_id,
            )
            .join(
                Seat, Seat.location_id == Event.location_id,
            )
            .join(
                Location, Location.id == Event.location_id,
            )
            .where(
                Event.start > datetime.now(),
                ~Seat.id.in_(query_seats)
            )
            .order_by(Event.start)
        )
        events = await self.session.execute(query)
        results = []
        for result in events:
            event_id = result.id
            event_object = EventShemaList(
                id=event_id,
                name=result.name,
                start=result.start,
                duration=result.duration,
                movie_name=result.movie_name,
                location_name=result.location_name,
                seats=[
                    SeatSchema.from_orm(result)
                ]
            )
            if results and results[-1].id == event_id:
                results[-1].seats.extend(event_object.seats)
            else:
                results.append(event_object)

        return results

    async def get_event(self, event_id: str) -> EventShemaList:
        query = (
            select(
                Event.id, Event.name, Event.start, Event.duration,
                PurchasedMovie.movie_name, Location.name.label("location_name"),
                Seat.id.label("seat_id"), Seat.row, Seat.seat, Seat.type
            )
            .select_from(Event)
            .join(
                PurchasedMovie,
                Event.movie_id == PurchasedMovie.movie_id,
            )
            .join(
                Seat,
                Seat.location_id == Event.location_id,
            )
            .join(
                Location,
                Location.id == Event.location_id,
            )
            .where(
                Event.id == event_id
            )
        )
        events = await self.session.execute(query)
        results = {}
        for result in events:
            event_object = EventShemaList(
                id=result.id,
                name=result.name,
                start=result.start,
                duration=result.duration,
                movie_name=result.movie_name,
                location_name=result.location_name,
                seats=[
                    SeatSchema.from_orm(result)
                ]
            )
            event_id = result.id
            if event_id in results:
                results[event_id].seats.extend(event_object.seats)
            else:
                results[event_id] = event_object

        return results.get(event_id)

    async def create(self, data: BookingInput, user_id: str) -> BookingSchema:
        event = await self.get_event(data.event_id)
        if not event:
            raise EventNotFoundException(data.event_id)
        if not any(seat.seat_id == data.seat_id for seat in event.seats):
            raise SeatNotFoundException(data.seat_id)
        try:
            booking = BookingObject(
                id=str(uuid.uuid4()),
                seat_id=data.seat_id,
                event_id=data.event_id,
                guest_id=user_id,
                status=1,
            )
            self.session.add(booking)
            await self.session.commit()
        except IntegrityError as e:
            raise UniqueConflictException(message="This booking already exist")
        return BookingSchema.from_orm(booking)

    async def get_booking(self, booking_id: str) -> BookingInfoSchema:
        query = (
            select(
                BookingObject.id, BookingObject.status, BookingObject.event_id,
                BookingObject.seat_id,
                BookingObject.price, BookingObject.guest_id, Event.id.label("event_id"),
                Event.name.label("event_name"), Event.start.label("event_start"),
                Event.duration.label("event_duration"),
                Seat.row.label("seat_row"), Seat.seat.label("seat_seat"),
                Seat.type.label("seat_type")
            )
            .select_from(BookingObject)
            .outerjoin(
                Event,
                Event.id == BookingObject.event_id,
            )
            .outerjoin(
                Seat,
                Seat.id == BookingObject.seat_id,
            )
            .where(
                BookingObject.id == booking_id
            )
        )
        booking = await self.session.execute(query)
        booking = booking.first()
        return BookingInfoSchema.from_orm(booking)

    async def get_bookings(self, user_id: str) -> list[BookingInfoSchema]:
        query = (
            select(
                BookingObject.id, BookingObject.status, BookingObject.event_id,
                BookingObject.seat_id,
                BookingObject.price, BookingObject.guest_id, Event.id.label("event_id"),
                Event.name.label("event_name"), Event.start.label("event_start"),
                Event.duration.label("event_duration"),
                Seat.row.label("seat_row"), Seat.seat.label("seat_seat"),
                Seat.type.label("seat_type")
            )
            .select_from(BookingObject)
            .join(
                Event,
                Event.id == BookingObject.event_id,
            )
            .join(
                Seat,
                Seat.id == BookingObject.seat_id,
            )
            .where(
                BookingObject.guest_id == user_id
            )
        )
        bookings = await self.session.execute(query)
        bookings = bookings.all()
        return [BookingInfoSchema.from_orm(booking) for booking in bookings]

    async def delete_booking(self, booking_id: str, user_id: str) -> dict:
        booking = await self.check_booking(booking_id)
        if not booking:
            raise BookingNotFoundException(booking_id)
        if booking.guest_id != user_id:
            raise ForbiddenException()
        query = (
            delete(BookingObject)
            .where(BookingObject.id == booking_id)
        )
        await self.session.execute(query)
        await self.session.commit()
        return {"msg": "booking was deleted"}

    async def update_booking_status(self, booking_id: str,
                                    new_status: int, user_id: str) -> dict:
        booking = await self.check_booking(booking_id)
        if not booking:
            raise BookingNotFoundException(booking_id)
        if booking.guest_id != user_id:
            raise ForbiddenException()
        query = (
            update(BookingObject)
            .where(BookingObject.id == booking_id)
            .values(status=new_status)
        )
        await self.session.execute(query)
        await self.session.commit()
        return {"msg": "booking status was updated"}

    async def check_booking(self, booking_id: str):
        booking = await self.session.execute(
            select(BookingObject.id, BookingObject.guest_id, BookingObject.status)
            .where(BookingObject.id == booking_id)
        )
        return booking.first()
