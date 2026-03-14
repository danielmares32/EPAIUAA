# app/utils/utils.py
from bcrypt import hashpw, gensalt, checkpw

def hash_password(password):
    return hashpw(password.encode('utf-8'), gensalt())

def verify_password(hashed_password, password):
    return checkpw(password.encode('utf-8'), hashed_password)