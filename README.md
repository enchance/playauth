
Simplified JWT Authentication with FastAPI-Users
======================================================


Files to check out:

- **/main.py:**  Sample routes
- **/_app/auth/\_\_init\_\_.py:** Configuration for FastAPI-Users. I placed this here so it's easilly accessible just by calling `from app.auth import <module>`.

Helper methods:
---------------------

### `format_expiresiso(expiresiso: str)`
Converts an isoformat datetime into the format used by cookies. Objects run through`datetime.
  isoformat()` returns a string which is perfect for saving to cache. But if you're saving to any RDBMS (postgres, 
  mysql, etc.) instead of to cache then this is unnecessary since you can save it directly as a
  `datetime` object. **Saving to RDBMS is ok for development but _not_ for production.**

### `expiry_diff_minutes(expiresiso: str)`
Checks how many minutes are left before the refresh token expires. The `expiresiso` is taken from cache which is why 
it's a `str`. If you saved it to RDBMS then this is probabaly a `datetime`. This helper exists so I can check if the 
expiry date is less than 3 hours away.

- **expiry date > 180 mins:** Change the refresh token, keep expiry date
- **0 < expiry date <= 180:** Change the refresh token, change the expiry date
- **expiry date <= 0:** kick the user out, delete refresh token from cache/db. Frontend redirects to login page.

### `fetch_cached_reftoken(refresh_token: str)`
Fetch the refresh token from storage. If the refresh token doesn't exist then return an [Error 401: Unauthorized][401].

[401]: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/401

### `refresh_cookie_generator(*, expiresiso: Optional[str] = None, **kwargs)`
The data to be used when creating the cookie which will store the refresh token.

`cachedata` is inserted in the dictionary which isn't a part of the cookie. This contains data used to update 
the cache/db. `cachedata` is eventually removed with `pop()`. In short, it merely hitched a ride with the dict so 
it'll be a part of the return value.


Dependency Injection
----------------------------

- **current_user:** Alias for `fusers.current_user()`.
- **super_user:** Alias for `fusers.current_user()`. Currently not in use.