from config import OWNER_ID

from database import (
    add_user,
    get_user_status,
    is_approved,
)


def is_owner(user_id):
    """
    Backward-compatible function.
    Returns True if the user is the bot owner/admin.
    """
    return user_id == OWNER_ID


def is_admin(user_id):
    """
    Returns True if the user is the bot admin.
    """
    return user_id == OWNER_ID


def register_user(user):
    """
    Add the user to the database
    if they don't already exist.
    """

    add_user(
        user_id=user.id,
        username=user.username or "",
        first_name=user.first_name or "",
    )


def get_status(user_id):
    """
    Get user's current access status.
    """

    if is_admin(user_id):
        return "admin"

    return get_user_status(user_id)


def has_access(user_id):
    """
    Check whether the user is allowed
    to use the bot.
    """

    if is_admin(user_id):
        return True

    return is_approved(
        user_id,
        OWNER_ID,
    )