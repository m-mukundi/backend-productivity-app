import random

from faker import Faker

from app import create_app
from extensions import db
from models import User, Task, VALID_STATUSES

fake = Faker()


def seed():
    app = create_app()
    with app.app_context():
        print("Clearing existing data...")
        Task.query.delete()
        User.query.delete()
        db.session.commit()

        print("Seeding users...")
        users = []

        demo = User(username="demo")
        demo.password = "password123"
        users.append(demo)
        db.session.add(demo)

        for _ in range(4):
            user = User(username=fake.unique.user_name())
            user.password = "password123"
            users.append(user)
            db.session.add(user)

        db.session.commit()

        print("Seeding tasks...")
        for user in users:
            for _ in range(random.randint(5, 12)):
                task = Task(
                    title=fake.sentence(nb_words=4).rstrip("."),
                    description=fake.paragraph(nb_sentences=2),
                    status=random.choice(VALID_STATUSES),
                    user_id=user.id,
                )
                db.session.add(task)

        db.session.commit()
        print(f"Seeded {len(users)} users with tasks (demo login: demo / password123).")


if __name__ == "__main__":
    seed()
