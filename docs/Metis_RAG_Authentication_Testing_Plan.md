# Metis RAG Authentication Testing Plan

This plan details the testing strategy for the implemented authentication and authorization system for the Metis RAG application. It covers the components outlined in Phases 1-4 of the `Metis_RAG_Authentication_Implementation_Detailed_Plan.md` and focuses on the testing tasks listed in Phase 5 and the persistent user-document relationship requirements.

**Guiding Principles:**

*   **Coverage:** Ensure all critical authentication and authorization paths are tested.
*   **Isolation:** Use unit tests for isolated logic (e.g., JWT functions).
*   **Interaction:** Use integration tests for component interactions (e.g., API endpoints + DB).
*   **User Flows:** Use end-to-end (e2e) tests for complete user scenarios.
*   **Security Focus:** Include tests specifically designed to probe for security vulnerabilities (e.g., unauthorized access attempts).
*   **Persistence:** Verify that user-data relationships remain intact across various authentication events (e.g., password resets, token refreshes).

**Proposed Test Structure (within `tests/` directory):**

```
tests/
├── unit/
│   ├── test_security_utils.py  # For JWT and password hashing functions (Phase 5.1)
│   └── ... (other unit tests)
├── integration/
│   ├── test_auth_endpoints.py    # For /login, /register, /refresh, password reset (Phase 5.1)
│   ├── test_permissions_db.py    # For RLS, document_permissions table (Phase 5.2)
│   ├── test_permissions_vector.py # For vector metadata filtering (Phase 5.2)
│   ├── test_rbac.py              # For role creation, assignment, checking (Phase 4 / 5.2)
│   ├── test_sharing.py           # For document sharing API & logic (Phase 4 / 5.2)
│   ├── test_multi_tenancy.py     # For organization isolation (Phase 4 / 5.2)
│   └── ... (other integration tests)
├── e2e/
│   ├── test_auth_flows.py        # Full login, register, use protected resource flows
│   ├── test_permission_scenarios.py # Complex scenarios involving multiple users, roles, sharing
│   └── ... (other e2e tests)
└── conftest.py                 # Fixtures for setting up users, roles, docs, etc.
```

**Detailed Test Areas Overview:**

```mermaid
graph TD
    subgraph TestingPlan [Authentication Testing Plan]
        direction LR

        subgraph Phase5_1 [Phase 5.1: Authentication Core]
            direction TB
            T1_1[Unit: JWT Functions] --> T1_2(test_security_utils.py);
            T1_3[Integration: Auth Endpoints] --> T1_4(test_auth_endpoints.py);
            T1_5[E2E: User Auth Flows] --> T1_6(test_auth_flows.py);
        end

        subgraph Phase5_2 [Phase 5.2: Permission System]
            direction TB
            T2_1[Integration: DB Permissions (RLS)] --> T2_2(test_permissions_db.py);
            T2_3[Integration: Vector DB Permissions] --> T2_4(test_permissions_vector.py);
            T2_5[Integration: RBAC] --> T2_6(test_rbac.py);
            T2_7[Integration: Sharing] --> T2_8(test_sharing.py);
            T2_9[Integration: Multi-Tenancy] --> T2_10(test_multi_tenancy.py);
            T2_11[E2E: Complex Permission Scenarios] --> T2_12(test_permission_scenarios.py);
        end

        subgraph Persistence [Persistent Relationships]
            direction TB
            P1[Integration: Password Reset] --> T1_4;
            P2[Integration: Account Deactivation/Reactivation] --> T1_4;
            P3[Integration: Token Refresh & Expiry] --> T1_4;
            P4[Unit/Integration: Verify Data Links] --> T2_2 & T2_4;
        end

        subgraph Phase5_3 [Phase 5.3: Security Hardening (Verification)]
             direction TB
             SH1[Manual/Config Review: Rate Limiting] --> SH_Verify(Verification Steps);
             SH2[Manual/Config Review: Monitoring/Logging] --> SH_Verify;
             SH3[Manual/Automated: Security Review (Scans, Audits)] --> SH_Verify;
        end

    end
```

**I. Authentication Core Testing (Phase 5.1 & Persistence)**

*   **Location:** `tests/unit/test_security_utils.py`, `tests/integration/test_auth_endpoints.py`, `tests/e2e/test_auth_flows.py`
*   **Unit Tests (`test_security_utils.py`):**
    *   Verify `create_access_token`, `create_refresh_token` output structure and claims (iss, aud, exp, sub, jti).
    *   Verify `verify_password` against known hashes.
    *   Verify `get_password_hash` produces valid hashes.
    *   Test token validation logic (`decode_token`) for:
        *   Valid tokens.
        *   Expired tokens.
        *   Tokens with invalid signatures.
        *   Tokens with incorrect audience/issuer (if re-enabled).
        *   Malformed tokens.
*   **Integration Tests (`test_auth_endpoints.py`):**
    *   `/register`: Success, duplicate username/email, invalid input.
    *   `/login`: Success (correct credentials), failure (incorrect password, non-existent user), inactive user login attempt.
    *   `/refresh`: Success (valid refresh token), failure (invalid/expired refresh token).
    *   Password Reset Flow: Request reset, validate token, set new password, login with new password, ensure old password fails. **(Persistence)**
    *   Account Deactivation/Reactivation: Deactivate user, verify login fails, verify data relationships persist, reactivate user, verify login succeeds. **(Persistence)**
    *   Token Expiry: Simulate token expiry, verify protected endpoint access fails, refresh token, verify access succeeds. **(Persistence)**
*   **E2E Tests (`test_auth_flows.py`):**
    *   Simulate a full user journey: Register -> Login -> Access Protected Resource -> Refresh Token -> Access Protected Resource -> Logout.

**II. Permission System Testing (Phase 5.2, Phase 4 Features & Persistence)**

*   **Location:** `tests/integration/test_permissions_db.py`, `tests/integration/test_permissions_vector.py`, `tests/integration/test_rbac.py`, `tests/integration/test_sharing.py`, `tests/integration/test_multi_tenancy.py`, `tests/e2e/test_permission_scenarios.py`
*   **Database Permissions (`test_permissions_db.py`):** (Requires setting `app.current_user_id` in test session context)
    *   Test RLS policies for `documents` and `chunks`:
        *   Owner can SELECT, UPDATE, DELETE own documents.
        *   Non-owner cannot access private documents.
        *   Any authenticated user can SELECT public documents (`is_public=true`).
        *   User can SELECT documents shared via `document_permissions`.
        *   User can UPDATE documents shared with 'write'/'admin' permission.
        *   User cannot UPDATE documents shared with 'read' permission.
        *   Verify access to `chunks` mirrors access to parent `document`.
    *   Test `document_permissions` table logic: Granting, revoking, listing permissions.
*   **Vector DB Permissions (`test_permissions_vector.py`):**
    *   Verify vector search results only include chunks where the user has access (own, public, shared) based on `user_id` and permission metadata.
    *   Test post-retrieval filtering correctly removes any chunks that might have slipped through pre-filtering.
    *   Test scenarios preventing cross-user data leakage via vector search.
    *   Verify persistence: Ensure vector metadata links (`user_id`) remain correct after auth events (password reset etc.). **(Persistence)**
*   **RBAC (`test_rbac.py`):**
    *   Test role creation, assignment, removal.
    *   Test permission checking logic based on roles (e.g., admin actions vs. viewer actions).
    *   Verify interaction with RLS (if roles influence RLS policies).
*   **Sharing (`test_sharing.py`):**
    *   Test document sharing API endpoints (grant, revoke, list collaborators).
    *   Verify notifications are triggered (mock notification service).
    *   Test access control based on sharing permissions.
*   **Multi-Tenancy (`test_multi_tenancy.py`):**
    *   Test organization creation, member management.
    *   Verify document association with organizations.
    *   Test RLS policies enforcing organization boundaries (users in Org A cannot see Org B's private documents).
    *   Test cross-organization sharing rules (if applicable).
*   **E2E Tests (`test_permission_scenarios.py`):**
    *   Scenario 1: User A uploads doc, User B cannot see it. User A shares with User B (read). User B can query, User B cannot update. User A revokes access. User B cannot query.
    *   Scenario 2: Admin user creates roles, assigns roles. Verify users with different roles have appropriate access levels to documents and system features.
    *   Scenario 3: User in Org A uploads doc. User in Org B cannot access it. Admin shares across orgs (if feature exists). Verify access.

**III. Security Hardening Verification (Phase 5.3)**

*   **Location:** Primarily manual review, configuration checks, potentially automated scans.
*   **Rate Limiting:**
    *   Verify configuration of rate limiting middleware (e.g., limits on `/login`, `/register`).
    *   Manually test exceeding limits to confirm blocking/throttling.
    *   Check for account lockout mechanism after repeated failures.
*   **Monitoring & Logging:**
    *   Review logging configuration.
    *   Manually trigger auth events (login success/fail, token refresh, permission denied) and verify logs capture relevant information.
    *   Check if alerting mechanisms are configured for suspicious activities (requires setup).
*   **Security Review:**
    *   Run dependency vulnerability scans (e.g., `safety check`, `pip-audit`).
    *   Review JWT configuration (`app/core/config.py`) for strong secrets, appropriate expiry, algorithm choice. (Note: Plan mentions audience verification disabled - flag this as a production risk).
    *   Review database security settings and RLS policies for potential bypasses.
    *   Review password hashing implementation (`app/core/security.py`).