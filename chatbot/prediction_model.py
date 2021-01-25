import pickle
from collections import defaultdict

file = 'static/prediction.sav'

# any invalid user input will return a 0
departure_dummy_encoder = defaultdict(int)
arrival_dummy_encoder = defaultdict(int)

departure_list = [('Colchester', [1, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
                  ('Diss', [0, 1, 0, 0, 0, 0, 0, 0, 0, 0]),
                  ('Ipswich', [0, 0, 1, 0, 0, 0, 0, 0, 0, 0]),
                  ('Manningtree', [0, 0, 0, 1, 0, 0, 0, 0, 0, 0]),
                  ('Marks Tey', [0, 0, 0, 0, 1, 0, 0, 0, 0, 0]),
                  ('Norwich', [0, 0, 0, 0, 0, 1, 0, 0, 0, 0]),
                  ('Shenfield', [0, 0, 0, 0, 0, 0, 1, 0, 0, 0]),
                  ('Stowmarket', [0, 0, 0, 0, 0, 0, 0, 1, 0, 0]),
                  ('Stratford', [0, 0, 0, 0, 0, 0, 0, 0, 1, 0]),
                  ('Whitham', [0, 0, 0, 0, 0, 0, 0, 0, 0, 1])]

arrival_list = [('Colchester', [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
                ('Diss', [0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
                ('Ipswich', [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0]),
                ('London Liverpool Street', [0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0]),
                ('Manningtree', [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0]),
                ('Marks Tey', [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0]),
                ('Norwich', [0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0]),
                ('Shenfield', [0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0]),
                ('Stowmarket', [0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0]),
                ('Stratford', [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0]),
                ('Witham', [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1])]

# Creates dictionaries out of lists of tuples above
for station, dummy_code in departure_list:
    departure_dummy_encoder[station] = dummy_code

for station, dummy_code in arrival_list:
    arrival_dummy_encoder[station] = dummy_code

# Reads KNN regression model saved in 'static/prediction.sav' and stores it as an object
with open(file, "rb") as f:
    unpickler = pickle.Unpickler(f)
    model = unpickler.load()


def predict(current_delay: int, is_off_peak: bool, travel_hour: int,
            dep_station: str, arr_station: str) -> int:
    out = [current_delay, is_off_peak, travel_hour]

    # if user input is not a valid station stored in the dictionaries, return none as the model will throw an error
    if departure_dummy_encoder[dep_station] == 0 or arrival_dummy_encoder[arr_station] == 0:
        return None

    # Each 'bit' in departure and arrival station's dummy code is appended sequentially into 'out' as this is the
    # correct order that the model expects the input to be in
    [out.append(item) for item in departure_dummy_encoder[dep_station]]
    [out.append(item) for item in arrival_dummy_encoder[arr_station]]

    return int(model.predict([out])[0][0])
