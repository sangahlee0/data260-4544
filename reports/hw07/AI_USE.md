# AI Use — HW7

### (1) What you used an AI assistant for and what you did yourself; 
I used an AI assistant to clarify FastAPI, JWT authentication, role-based access control, SQLAlchemy/MySQL schema issues, and the expected format of the verification and screenshot evidence. I also used it to understand error messages related to the existing `users` table and the bcrypt/Passlib dependency mismatch. The METRICS.md was also formatted based on AI recommendations of good markdown practices. I implemented and ran the application myself, seeded the user accounts, updated the database schema as needed, tested the endpoints in Swagger, ran the verification script, and collected the required evidence. I also looked up why I can use SQLite instead of MySQL based on specific needs of the other parts of the assignment.

### (2) One AI-produced output that was wrong/unsuitable, or one thing you independently verified;
I independently verified that an existing MySQL table does not automatically gain new columns merely because the SQLAlchemy model changes. I confirmed this by examining the `Unknown column 'users.username'` error and checking the database schema before making the needed migration. I also independently verified the application behavior through Swagger and the `verify-hw07.py` script than relying only on suggested commands to make sure that the flow was working properly.

### (3) How you detected the problem or verified the result;
I used the traceback, MySQL errors, Swagger response codes, and the verification report to diagnose problems. For example, a `500` login response led me to check the backend setup and dependency versions, while a `404` during the writer-create test showed that the required package record did not exist. I also made sure to verify the final behavior by confirming successful JWT login, invalid-login `401`, unauthenticated and invalid-token `401` responses, reader `403`, writer create `201`, writer delete `403`, moderator delete success, and authenticated list/read `200`.

### (4) What you changed and why it works now;
I updated the database setup so the `users` table matched the HW7 model requirements, including the `username` and `role` fields. I seeded the reader, writer, and moderator accounts, used a compatible bcrypt version, and ensured a package record existed for the create-request test.
These changes work because the application now has the expected database schema, valid password hashes, role-based user accounts, and the supporting data required by the protected API endpoints.

