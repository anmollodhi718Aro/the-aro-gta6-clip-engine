# Backend

Backend implementation has not started yet.

Planned first module sequence:
1. typed data models for sources, permissions, and events
2. permission validation service
3. timestamp normalization
4. deterministic chat-spike detector
5. clip decision-list serializer
6. tests for each module

Keep provider adapters separate from the core detection logic. The core should be testable without network access or API credentials.
