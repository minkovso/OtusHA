import json
import sys
import faker
from random import randint

def generate_data(n: int) -> None:
    fake = faker.Faker()
    cases = []
    for _ in range(n):
        first_name = fake.first_name()[:randint(1, 3)]
        second_name = fake.last_name()[:randint(1, 3)]
        case = {'first_name': first_name, 'second_name': second_name}
        cases.append(case)
    print(json.dumps(cases))

if __name__ == '__main__':
    generate_data(int(sys.argv[1]))
