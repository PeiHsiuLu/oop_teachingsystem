from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required

from app.services.auth_service import AuthService
from app.models.forms import RegistrationForm, LoginForm


auth_bp = Blueprint("auth", __name__)
auth_service = AuthService()


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()

    if form.validate_on_submit():
        try:
            auth_service.register(
                username=form.username.data,
                email=form.email.data,
                password=form.password.data,
                role=form.role.data
            )

            flash("Registration successful! Please log in.", "success")
            return redirect(url_for("auth.login"))

        except ValueError as e:
            flash(str(e), "error")

    return render_template("register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = auth_service.login(form.username.data, form.password.data)

        if user:
            flash("Login successful.", "success")

            if user.role == "admin":
                return redirect("/dashboard")

            if user.role == "student":
                return redirect("/course/student/dashboard")

            return redirect(url_for("main.index"))

        flash("Invalid username or password.", "error")

    return render_template("login.html", form=form)


@auth_bp.route("/forgot-password", methods=["GET"])
def forgot_password():
    return render_template("forgot_password.html")


@auth_bp.route("/logout")
@login_required
def logout():
    auth_service.logout()
    flash("You have been logged out.", "success")
    return redirect(url_for("main.index"))