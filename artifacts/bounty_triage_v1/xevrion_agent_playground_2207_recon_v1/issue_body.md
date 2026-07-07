POST /users currently trusts arbitrary request bodies. A client can send a custom id and extra fields, and the API returns them in the created user response. User creation should generate ids server-side, require a valid email, normalize optional names, and reject invalid JSON shapes.

Acceptance criteria:
- Reject non-object JSON bodies. In
- Require a valid email.
- Normalize email/name values.
- Ignore client-controlled id and unrelated fields.
- Add regression tests for these cases.

/bounty $250

References #33