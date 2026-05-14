def user_serializer(user):
    print("TRIGGERED")
    return {
        "id": user.id,
        "email": user.email,
        "authentication_token": user.get_auth_token(),  # THIS IS KEY
        "roles": [r.name for r in user.roles],
    }
