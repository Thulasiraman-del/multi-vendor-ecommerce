import asyncio
from getpass import getpass

from sqlalchemy import select, text

from app.core.database import AsyncSessionLocal, engine
from app.core.security import hash_password
from app.models import User


async def create_admin():
    engine.echo = False

    try:
        if engine.dialect.name != "postgresql":
            print("Error: Admin bootstrap requires PostgreSQL.")
            return

        print("\n=== Administrator Bootstrap ===\n")

        full_name = input("Administrator full name: ").strip()
        email = input("Administrator email: ").strip().lower()

        if not full_name or not email or "@" not in email:
            print("Error: Enter a valid name and email.")
            return

        password = getpass("Administrator password (hidden): ")
        confirm_password = getpass("Confirm password (hidden): ")

        if len(password) < 12:
            print("Error: Password must contain at least 12 characters.")
            return

        if password != confirm_password:
            print("Error: Passwords do not match.")
            return

        confirmation = input(
            f"\nCreate the first administrator account for {email}? (yes/no): "
        ).strip().lower()

        if confirmation != "yes":
            print("Administrator creation cancelled.")
            return

        async with AsyncSessionLocal() as session:
            async with session.begin():
                # Serialize concurrent bootstrap attempts.
                await session.execute(
                    text("SELECT pg_advisory_xact_lock(731942681)")
                )

                existing_admin = await session.scalar(
                    select(User).where(User.role == "admin").limit(1)
                )

                if existing_admin:
                    print(
                        "Error: An administrator already exists. "
                        "No changes were made."
                    )
                    return

                existing_user = await session.scalar(
                    select(User).where(User.email == email)
                )

                if existing_user:
                    print(
                        "Error: This email already belongs to an account. "
                        "No account or role was changed."
                    )
                    return

                admin = User(
                    full_name=full_name,
                    email=email,
                    password_hash=hash_password(password),
                    role="admin",
                    is_active=True,
                )

                session.add(admin)
                await session.flush()

                admin_id = admin.id

            print("\nAdministrator created successfully.")
            print(f"User ID: {admin_id}")
            print(f"Email: {email}")
            print("Role: admin")

    except Exception as exc:
        # Do not print exception details or SQL parameters.
        print(f"\nAdministrator creation failed ({type(exc).__name__}).")
        print("Check the database connection and server logs.")

    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(create_admin())
