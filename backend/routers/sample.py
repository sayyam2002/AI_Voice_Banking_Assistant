from passlib.context import CryptContext

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
hashed = pwd_ctx.hash("1111")
print(hashed)
print(pwd_ctx.verify("1111", hashed))