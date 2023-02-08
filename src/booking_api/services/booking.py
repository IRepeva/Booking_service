from datetime import datetime
import uuid
from http import HTTPStatus

from fastapi import HTTPException
from sqlalchemy import desc, delete, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.future import select

from booking_api.models.booking import EventShemaList, SeatSchema, BookingInput, BookingSchema, \
    BookingInfoSchema
from booking_api.services.service_mixin import ServiceMixin
from db.tables.booking import BookingObject, BookingStatus
from db.tables import Seat, Host
from db.tables import PurchasedMovie
from db.tables import Location
from db.tables import Event


class BookingService(ServiceMixin):

    async def get_events(self) -> list[EventShemaList]:
        query_seats = (
            select(BookingObject.seat_id).filter(BookingObject.event_id == Event.id)
        )

        query = (select(
            Event.id, Event.name, Event.start, Event.duration,
            PurchasedMovie.movie_name, Location.name.label('location_name'),
            Seat.id.label('seat_id'), Seat.row, Seat.seat, Seat.type
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
            Event.start > datetime.now(),
            ~Seat.id.in_(query_seats)
        )
                 .order_by(Event.start)
                 )
        events = await self.session.execute(query)
        results = []
        for result in events:
            event_id = result.id
            event_dict = EventShemaList(
                id=event_id,
                name=result.name,
                start=result.start,
                duration=result.duration,
                movie_name=result.movie_name,
                location_name=result.location_name,
                seats=[
                    SeatSchema(
                        seat_id=result.seat_id,
                        row=result.row,
                        seat=result.seat,
                        type=result.type,
                    )]
            ).dict()
            for event in results:
                if event['id'] == event_id:
                    event['seats'].extend(event_dict['seats'])
                    break
            else:
                event_dict['seats'] = event_dict['seats']
                results.append(event_dict)

        return results

    async def get_event(self, event_id) -> EventShemaList:
        query = (
            select(
                Event.id, Event.name, Event.start, Event.duration,
                PurchasedMovie.movie_name, Location.name.label('location_name'),
                Seat.id.label('seat_id'), Seat.row, Seat.seat, Seat.type
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
                Event.start > datetime.now(),
                Event.id == event_id
            )
                .order_by(desc(Event.start))
        )
        events = await self.session.execute(query)

        results = {}
        for result in events:
            event_dict = EventShemaList(
                id=result.id,
                name=result.name,
                start=result.start,
                duration=result.duration,
                movie_name=result.movie_name,
                location_name=result.location_name,
                seats=[
                    SeatSchema(
                        seat_id=result.seat_id,
                        row=result.row,
                        seat=result.seat,
                        type=result.type
                    )]
            ).dict()

            event_id = result.id
            if event_id in results:
                results[event_id]['seats'].extend(event_dict['seats'])
            else:
                results[event_id] = event_dict

        return results.get(event_id)

    async def create(self, data: BookingInput, user_id: uuid) -> BookingSchema:
        event = await self.get_event(data.event_id)
        if not event:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Event not found")
        if not any(seat.get("seat_id") for seat in event.get("seats")):
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Seat not found")
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
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,
                detail="This booking already exists"
            )
        return BookingSchema.from_orm(booking)

    async def get_booking(self, booking_id) -> BookingInfoSchema:
        query = (
            select(
                BookingObject.id, BookingObject.status, BookingObject.event_id,
                BookingObject.seat_id,
                BookingObject.price, BookingObject.guest_id, Event.id.label('event_id'),
                Event.name.label('event_name'), Event.start.label('event_start'),
                Event.duration.label('event_duration'),
                Seat.row.label('seat_row'), Seat.seat.label('seat_seat'),
                Seat.type.label('seat_type')
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
            ))

        booking = await self.session.execute(query)
        booking = booking.first()
        return BookingInfoSchema.from_orm(booking)

    async def get_bookings(self, user_id) -> list[BookingInfoSchema]:
        query = (
            select(
                BookingObject.id, BookingObject.status, BookingObject.event_id,
                BookingObject.seat_id,
                BookingObject.price, BookingObject.guest_id, Event.id.label('event_id'),
                Event.name.label('event_name'), Event.start.label('event_start'),
                Event.duration.label('event_duration'),
                Seat.row.label('seat_row'), Seat.seat.label('seat_seat'),
                Seat.type.label('seat_type')
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
            ))

        bookings = await self.session.execute(query)
        bookings = bookings.all()
        return [BookingInfoSchema.from_orm(booking) for booking in bookings]

    async def delete_booking(self, booking_id, user_id) -> dict:
        booking = await self.session.execute(
            select(BookingObject.id, BookingObject.guest_id)
                .where(
                BookingObject.id == booking_id)
        )
        booking = booking.first()
        if not booking:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Booking not found")
        if str(booking.guest_id) != str(user_id):
            raise HTTPException(status_code=HTTPStatus.FORBIDDEN, detail="Delete not allowed")
        query = (delete(BookingObject)
                 .where(BookingObject.id == booking_id)
                 )
        await self.session.execute(query)
        await self.session.commit()
        return {"msg": 'booking was deleted'}

    async def update_booking_status(self, booking_id: int, user_id: int, new_status: str) -> dict:
        booking = await self.session.execute(
            select(BookingObject.id, BookingObject.guest_id, BookingObject.status)
                .where(
                BookingObject.id == booking_id)
        )
        booking = booking.first()
        if not booking:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Booking not found")
        query = (update(BookingObject)
                 .where(BookingObject.id == booking_id)
                 .values(status=new_status)
                 )
        await self.session.execute(query)
        await self.session.commit()
        return {"msg": 'booking status was updated'}
