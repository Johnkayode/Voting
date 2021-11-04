from . import db
from .vote import hashing
from sqlalchemy import func

class Admin(db.Model):
    # Admin

    __tablename__ = "administrators"

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(40), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    created_at = db.Column(db.DateTime, default=func.now())


class Election(db.Model):
    # Election

    __tablename__ = "elections"

    id = db.Column(db.Integer, primary_key=True)

    admin_id = db.Column(db.Integer, db.ForeignKey("administrators.id"), nullable=False)
    admin = db.relationship("Admin", backref=db.backref("elections", lazy="dynamic"))

    title = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(150), index=True, nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=func.now())
    voters =  db.Column(db.Text, nullable=False)
    is_open = db.Column(db.Boolean, default=True)

    @property
    def get_absolute_url(self):
        return f"/elections/{self.slug}"


class Candidate(db.Model):
    # Election Candidate

    __tablename__ = "candidates"

    id = db.Column(db.Integer, primary_key=True)

    election_id = db.Column(db.Integer, db.ForeignKey("elections.id"), nullable=False)
    election = db.relationship("Election", backref=db.backref("candidates", lazy="dynamic"))

    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    manifesto = db.Column(db.Text, nullable=False)

    address = db.Column(db.String(50), nullable=False)
    passphrase = db.Column(db.String(250), nullable=False)
    votes = db.Column(db.Integer, default=0)


class Voter(db.Model):
    # Voter

    __tablename__ = "voters"
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    matric_no = db.Column(db.String(50), nullable=False, unique=True)
    department = db.Column(db.String(100), nullable=False)

