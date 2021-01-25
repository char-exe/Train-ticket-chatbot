import sqlite3
import csv

# Path to database
static = 'static/stations.csv'

# Connect to database
conn = sqlite3.connect('static/stations.db')

# Create cursor to execute SQL commands
cur = conn.cursor()

# Create new station name and station code tables if they don't exist
create_station_table = "CREATE TABLE IF NOT EXISTS stations(name STRING PRIMARY KEY)"
create_code_table = "CREATE TABLE IF NOT EXISTS station_codes(code STRING PRIMARY KEY)"

# Execute above commands
cur.execute(create_station_table)
cur.execute(create_code_table)


# Populate tables with station names and codes using 'stations.csv'
def populate_station_tables() -> None:
    with open(static) as csvFile:
        reader = csv.reader(csvFile, delimiter=',')
        row_iterator = iter(reader)
        # Skips first line (column headers)
        next(row_iterator)
        for row in row_iterator:
            for column in range(0, len(row)):
                item = row[column]
                if item != '':
                    # If entire station name is in upper case, it is a station code (e.g. NRW)
                    if item.isupper():
                        # Insert station code into station code table if it's not already in there
                        cur.execute("INSERT OR IGNORE INTO station_codes VALUES(?)", [item])

                    else:
                        # Insert station name into station name table if it's not already in there
                        cur.execute("INSERT OR IGNORE INTO stations VALUES(?)", [item])
                else:
                    continue
    conn.commit()


# Checks if tables have been populated yet (for testing purposes)
def check_if_tables_empty() -> bool:
    check_if_stations_empty = "SELECT count(*) FROM stations"
    cur.execute(check_if_stations_empty)
    check_if_stations_empty = cur.fetchall()[0][0]

    check_if_codes_empty = "SELECT count(*) FROM station_codes"
    cur.execute(check_if_codes_empty)
    check_if_codes_empty = cur.fetchall()[0][0]

    if check_if_stations_empty == 0 or check_if_codes_empty == 0:
        return True
    return False


# Gets all station names and codes and returns them in a tuple of two lists
def get_station_data() -> (list, list):
    if not check_if_tables_empty():
        station_names = [name[0] for name in cur.execute("SELECT name FROM stations")]
        station_codes = [code[0] for code in cur.execute("SELECT code FROM station_codes")]
        return station_names, station_codes
