import sys
import faker
import uuid

def generate_data(n: int, file: str) -> None:
    fake = faker.Faker()
    with open(file, 'a') as f:
        for _ in range(n):
            id = str(uuid.uuid4())
            first_name = fake.first_name()
            second_name = fake.last_name()
            birthdate = fake.date()
            city = fake.city()
            biography = fake.sentence(10)
            line = ','.join((id, first_name, second_name, birthdate, city, biography))
            f.write(line + '\n')


if __name__ == '__main__':
    generate_data(int(sys.argv[1]), sys.argv[2])
