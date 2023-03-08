# Service for organizing and booking events

## Description

The booking service enables to organize and participate in movie watching events. 
In addition to creating cinema sessions, this service allows to arrange film viewings 
at other locations or create custom venue.

## Functional capabilities
 - Organizing an event with a choice of location, time, movie, duration, etc.
 - Updating event details
 - Cancelling an event 
 - Searching for existing events
 - Booking tickets for created events
 - Cancelling a reservation
 - Adding a venue for an event with the ability to specify the hall configuration
 - Changing the hall configuration
 - Removing a viewing location to prevent events from being organized there

More detailed API documentation can be found [here](0.0.0.0:80/api/openapi)

## Get started
1. Create a **.env** file in the root directory of the project, based on the example [.env.example](.env.example)

2. To run the project, use the command:
   ```bash
    make start-service
    ```
3. To authenticate, pass a JWT token generated based on the key ('JWT_SECRET') you specified in .env:
    
    **Example:**
    ```bash
    import jwt
    jwt.encode({"user_id": 'f2e7425b-746a-4b5f-940f-89da0e7ad9ba'}, "test_Pups_secret", algorithm="HS256")
    ```
### Available make commands
 - **start**: start the server and update the database schema
 - **stop**: stop the service
 - **start-service**: start the service
 - **migration-upgrade**: update the database schema
 - **migration-downgrade**: roll back the migration
 - **make local-start**: start local service
