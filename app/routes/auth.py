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

            flash(
                "Registration successful! Please log in.\n註冊成功！請登入。",
                "success"
            )
            return redirect(url_for("auth.login"))

        except ValueError as e:
            flash(str(e), "error")

    return render_template("register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = auth_service.login(
            form.username.data,
            form.password.data
        )

        if user:
            if user.role == "admin":
                flash(
                    f"Welcome back, {user.username}!\n歡迎回來，{user.username}！",
                    "success"
                )
                return redirect("/dashboard")

            if user.role == "student":
                if getattr(user, "daily_login_reward_added", False):
                    flash(
                        f"Welcome back, {user.username}! Daily login reward: +1 XP.\n"
                        f"歡迎回來，{user.username}！今日登入獎勵：+1 經驗值。",
                        "success"
                    )
                else:
                    flash(
                        f"Welcome back, {user.username}! You have already received today's login reward.\n"
                        f"歡迎回來，{user.username}！你今天已經領取過登入獎勵了。",
                        "success"
                    )

                return redirect(url_for("course.student_course_dashboard"))

            flash(
                f"Welcome back, {user.username}!\n歡迎回來，{user.username}！",
                "success"
            )
            return redirect(url_for("main.index"))

        flash(
            "Invalid username or password.\n使用者名稱或密碼錯誤。",
            "error"
        )

    return render_template("login.html", form=form)


@auth_bp.route("/forgot-password", methods=["GET"])
def forgot_password():
    return render_template("forgot_password.html")


@auth_bp.route("/logout")
@login_required
def logout():
    auth_service.logout()

    flash(
        "You have been logged out.\n你已成功登出。",
        "success"
    )
    return redirect(url_for("main.index"))