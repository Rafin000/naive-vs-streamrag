# Server-Sent Events
Server-Sent Events (SSE) is a one-way streaming transport where the server pushes text events to
the browser over a single HTTP connection. It is simpler than WebSockets when only the server
needs to send data, which fits streaming model tokens to a client. This project sends token and
metrics events over SSE so the frontend can render an answer as it arrives.
