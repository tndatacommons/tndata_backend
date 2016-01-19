Places are named locations. They may be pre-defined or user-defined.
Each place contains the following fields:

* `id`: The unique database id of the place.
* `name`: The unique name of the place.
* `slug`: A slugified version of the name (unique)
* `primary`: Primary places should be used to generate menus. This endpoint
  currently _only_ displays primary places (so this is always True).
* `updated_on`: Date the place was updated.
* `created_on`: Date the place was created.

This is a read-only endpoint. To save a place, see
the [UserPlaces API](/api/users/places/).

----

