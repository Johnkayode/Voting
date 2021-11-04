from functools import wraps
from flask import session, flash, redirect, url_for
from .models import Admin

def is_admin(function):
    @wraps(function)
    def wrap(*args, **kwargs):

        admin_email = session.get("admin", "")
        admin = Admin.query.filter_by(email=admin_email).first()
        if admin:
                return function(*args, **kwargs)
        flash("You don't have necessary permissions for this action", "danger")
        return redirect(url_for("admin_login"))

    return wrap