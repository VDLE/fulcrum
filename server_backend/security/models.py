from flask_sqlalchemy import SQLAlchemy

from flask_security import hash_password
from sqlalchemy import String, Integer, TIMESTAMP, func
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional, List
from app import db
from flask_security import UserMixin, RoleMixin

# db = SQLAlchemy()
from flask_security.models import fsqla_v3 as fsqla

# Association table for user roles
roles_users = db.Table(
    "users_roles",  # match name in db
    db.Column("user_id", db.Integer, db.ForeignKey("user.user_id")),
    db.Column("role_type_id", db.Integer, db.ForeignKey("role_type.role_type_id")),
)


class Role(db.Model, fsqla.FsRoleMixin):
    __tablename__ = "role_type"  # Match the table name in DB

    role_type_id = db.Column(db.Integer, primary_key=True)
    role_type_name = db.Column(db.String(255), unique=True)
    role_type_description = db.Column(db.String(255))
    permissions: Mapped[Optional[str]] = db.Column(db.TEXT, nullable=True)
    update_datetime: Mapped[TIMESTAMP] = db.Column(
        db.TIMESTAMP,
        default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    # Used to make the naming match the expected naming in Flask-Security
    @property
    def id(self):
        return self.role_type_id

    @property
    def name(self):
        return self.role_type_name

    @property
    def description(self):
        return self.role_type_description


class User(db.Model, fsqla.FsUserMixin):
    __tablename__ = "user"

    user_id = db.Column(db.Integer, primary_key=True)
    first_name: Mapped[str] = db.Column(db.String(255))
    last_name: Mapped[str] = db.Column(db.String(255))
    email: Mapped[str] = db.Column(db.String(255), unique=True, nullable=False)
    user_password: Mapped[Optional[str]] = db.Column(db.TEXT, nullable=True)
    created_at: Mapped[TIMESTAMP] = db.Column(
        db.TIMESTAMP, default=func.current_timestamp()
    )
    active: Mapped[bool] = db.Column(db.Boolean, default=True)
    fs_uniquifier: Mapped[str] = db.Column(db.String(255), unique=True, nullable=False)
    fs_webauthn_user_handle: Mapped[Optional[str]] = db.Column(
        db.String(255), unique=True, nullable=True
    )
    mf_recovery_codes: Mapped[Optional[str]] = db.Column(db.Text)
    us_phone_number: Mapped[Optional[str]] = db.Column(db.String(20))
    username: Mapped[Optional[str]] = db.Column(db.String(255))
    us_totp_secrets: Mapped[Optional[str]] = db.Column(db.Text)
    confirmed_at: Mapped[Optional[TIMESTAMP]] = db.Column(db.TIMESTAMP)
    last_login_at: Mapped[Optional[TIMESTAMP]] = db.Column(db.TIMESTAMP)
    current_login_at: Mapped[Optional[TIMESTAMP]] = db.Column(db.TIMESTAMP)
    last_login_ip: Mapped[Optional[str]] = db.Column(db.String(45))
    current_login_ip: Mapped[Optional[str]] = db.Column(db.String(45))
    login_count: Mapped[int] = db.Column(db.Integer, default=0)
    tf_primary_method: Mapped[Optional[str]] = db.Column(db.String(50))
    tf_totp_secret: Mapped[Optional[str]] = db.Column(db.Text)
    tf_phone_number: Mapped[Optional[str]] = db.Column(db.String(20))
    create_datetime: Mapped[TIMESTAMP] = db.Column(
        db.TIMESTAMP, default=func.current_timestamp()
    )
    update_datetime: Mapped[TIMESTAMP] = db.Column(
        db.TIMESTAMP,
        default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    roles: Mapped[List[Role]] = db.relationship(
        "Role",
        secondary=roles_users,  # Association table
        backref=db.backref("users", lazy="dynamic"),
    )

    # Used to make the naming match the expected naming in Flask-Security
    @property
    def id(self):
        return self.user_id

    @property
    def password(self):
        return self.user_password

    @password.setter
    def password(self, value):
        self.user_password = value
