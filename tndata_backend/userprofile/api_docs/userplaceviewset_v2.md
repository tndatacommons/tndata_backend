User Places are Places defined by a user. A `UserPlace` object consists
of the following fields:

* id: The unique database id of the place.
* user: The user's unique database ID.
* profile: The user's unique profile ID (see the
  [/api/userprofiles/](/api/userprofiles/) endpoint)
* place: A hash represnting the name of a place. See the
  [/api/users/places/](/api/users/places/) endpoint.
* latitude: A decimal value representing the latitude of the place.
* longitude: A decimal value representing the longitude of the place.
* updated_on: Date the place was updated.
* created_on: Date the place was created.

## Creating a UserPlace

POST to `/api/users/places/` with the following information:

    {
        "place": "PLACE-NAME"        // e.g. 'Home' or 'Work'
        "latitude": "LATITUDE",      // e.g. '35.1234'
        "longitude": "LONGITUDE",    // e.g. '-89.1234'
    }

## Updating a UserPlace

A UserPlace instance has a unique resource URI based on it's Database ID,
e.g. `/api/users/places/1/`. To update this object, send a PUT request
containing values that you want to update, e.g.:

    {
        "latitude": "27.9881",
        "longitude": "86.9253"
    }

**NOTE**: A user can define only _one Place name_. For example, if a user
sets a `Home` location, they can have only one UserPlace objects where
`place` is set to "Home".

----

