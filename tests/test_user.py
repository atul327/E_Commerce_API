"""
=====================================================
Purpose
-------
Testing User APIs

Current APIs
------------
1. Register
2. Login
3. Profile
4. Update Profile
5. Change Password
6. Delete Account
=====================================================
"""

import pytest


@pytest.mark.asyncio
async def test_register(client):

    response = await client.post(
        "/user/register",
        json={
            "username": "Atul",
            "email": "atul@gmail.com",
            "mob_num": "9999999999",
            "password": "12345678",
            "date_of_birth": "2000-01-01",
            "role": "user",
            "user_address": "Nagpur"
        }
    )

    assert response.status_code == 200

"""
Register Testing

✅ 1. Successful Registration          (Done)
⬜ 2. Duplicate Email
⬜ 3. Invalid Email
⬜ 4. Missing Required Fields
⬜ 5. Weak Password
⬜ 6. Verify Data in Database
⬜ 7. Verify Password is Hashed
⬜ 8. Cleanup & Test Isolation

"""