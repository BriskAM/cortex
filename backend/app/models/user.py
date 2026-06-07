from flask_security import UserMixin, RoleMixin
from backend.app.extensions import db

# Define association table for User and Role relationship
roles_users = db.Table(
    'roles_users',
    db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
    db.Column('role_id', db.Integer(), db.ForeignKey('role.id'))
)

class Role(db.Model, RoleMixin):
    __tablename__ = 'role'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    active = db.Column(db.Boolean(), default=True)
    _github_token = db.Column('github_token', db.Text, nullable=True) # Encrypted OAuth token in DB
    fs_uniquifier = db.Column(db.String(64), unique=True, nullable=False)
    
    @property
    def github_token(self):
        """Decrypt token when reading."""
        from backend.app.utils.encryption import decrypt_token
        return decrypt_token(self._github_token)

    @github_token.setter
    def github_token(self, value):
        """Encrypt token when writing."""
        from backend.app.utils.encryption import encrypt_token
        self._github_token = encrypt_token(value)

    
    roles = db.relationship(
        'Role',
        secondary=roles_users,
        backref=db.backref('users', lazy='dynamic')
    )
