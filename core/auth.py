from config import ADMIN_IDS

from database import (
    save_user,
    get_user_status,
    set_user_status
)


def is_admin(user_id):
    """
    Check if a Telegram user is an administrator.
    """

    try:
        return int(user_id) in ADMIN_IDS

    except (TypeError, ValueError):

        return False


def register_user(user):
    """
    Register or update a Telegram user.
    """

    if not user:
        return

    save_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name
    )


def get_status(user_id):
    """
    Return the user's current status.
    """

    return get_user_status(
        user_id
    )


def has_access(user_id):
    """
    Admins always have access.

    Normal users need approved status.
    """

    if is_admin(user_id):

        return True

    status = get_user_status(
        user_id
    )

    return status == "approved"


def approve_user(user_id):

    set_user_status(
        user_id,
        "approved"
    )


def reject_user(user_id):

    set_user_status(
        user_id,
        "rejected"
    )


def block_user(user_id):

    set_user_status(
        user_id,
        "blocked"
    )
