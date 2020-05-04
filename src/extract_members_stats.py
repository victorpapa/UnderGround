import os
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pycountry
import regex
from Main import create_members_df
from Utils import get_dict_keys, get_dict_values, get_date_from, get_00_time_from, get_time_diff

def plot_since_last_login():
    members_folder = os.path.join(os.getcwd(), *["..", "res", "Members"])
    df = create_members_df(members_folder, limit = 0)
    all_members = df.get_members()
    active_members = df.get_active_members() # list of Member objects
    time_distr = {}

    for member in active_members:
        days_since_last_login = member.LastVisitDue[2]
        # this number may be negative but it just means that the number of days is 0
        if days_since_last_login < 0:
            days_since_last_login = 0

        if days_since_last_login in time_distr:
            time_distr[days_since_last_login] += 1
        else:
            time_distr[days_since_last_login] = 1
    
    time_distr = {k: v for k, v in sorted(time_distr.items(), key=lambda x: x[0], reverse=True)}

    plt.plot(get_dict_keys(time_distr), get_dict_values(time_distr))
    plt.xlabel("Days since last log in")
    plt.ylabel("Number of Members")
    plt.show()

def plot_time_since_registration(since_registration):
    plt.plot(get_dict_keys(since_registration), get_dict_values(since_registration))
    plt.xlabel("Days since registration")
    plt.ylabel("Number of Members")
    plt.show()

def plot_age(age):
    plt.plot(get_dict_keys(age), get_dict_values(age))
    # plt.xticks([k for k in get_dict_keys(age) if int(k) % 10 == 0 or k == "2"])
    plt.xlabel("Age")
    plt.ylabel("Number of Members")
    plt.show()

def plot_time_spent(time_spent):
    plt.plot(get_dict_keys(time_spent), get_dict_values(time_spent))
    plt.xticks(get_dict_keys(time_spent)[::len(time_spent) // 10])
    plt.xlabel("Time Spent")
    plt.ylabel("Number of Members")
    plt.show()
    
def plot_location(location):    
    plt.plot(get_dict_keys(location)[:7], get_dict_values(location)[:7])
    plt.xlabel("Location")
    plt.ylabel("Number of Members")
    plt.show()

def has_digits(string):
    return any(char.isdigit() for char in string)

def dash_count(string):
    return string.count("-")

if __name__ == "__main__":

    os.chdir(os.path.join("..", *["out", "Members_metadata"]))
    metadata_files = os.listdir(os.getcwd())

    age = {}
    time_spent = {}
    location = {}
    since_registration = {}

    for metadata_file in metadata_files:
        metadata_file_handler = open(metadata_file, "r", encoding="utf-8")

        for metadata_row in metadata_file_handler:
            metadata_fields = metadata_row.split()

            # offset used for keeping track of the number of location parts
            offset = 0
            i = 0
            while i < len(metadata_fields):
                curr_field = metadata_fields[i]

                if i == 0: # Age
                    if curr_field == "0":
                        i += 1
                        continue

                    if curr_field in age:
                        age[curr_field] += 1
                    else:
                        age[curr_field] = 1

                elif i == 1: # TimeSpent
                    if curr_field == "0E-10":
                        i += 1
                        continue

                    if curr_field in time_spent:
                        time_spent[curr_field] += 1
                    else:
                        time_spent[curr_field] = 1

                elif i == 2: # Location

                    location_name = curr_field

                    curr_field = metadata_fields[i+1]
                    while not (has_digits(curr_field) and dash_count(curr_field) == 2):
                        i += 1
                        location_name += " " + curr_field
                        curr_field = metadata_fields[i+1]
                        offset += 1

                    # if name had more than 1 piece (offset > 0)
                    if offset > 0:
                        i -= 1

                    if location_name in location:
                        location[location_name] += 1
                    else:
                        location[location_name] = 1

                elif i == 3 + offset:
                    registration_date = [metadata_fields[i], metadata_fields[i+1]]

                    # obtain the time zone difference (+/- 1 day) as an int, and the time at +00 as a tuple
                    (registration_date_to_add, registration_time) = get_00_time_from(registration_date[1])
                    # obtain the date as a tuple
                    registration_date = get_date_from(registration_date[0])
                    # may have to +/- 1 day due to time zone

                    # this may overflow the number of possible days in a month, but I don't think it really matters
                    registration_date = registration_date[0:2] + (registration_date[2] + registration_date_to_add,) + registration_date[3:]

                    for x in registration_time:
                       registration_date += (x,) # we want date to contain 6 numbers: year, month, day, hour, minute, second

                    curr_date = (2020, 4, 27, 7, 15, 30)
                    elapsed_time = get_time_diff(curr_date, registration_date)
                    elapsed_days = elapsed_time[2]

                    if elapsed_days in since_registration:
                        since_registration[elapsed_days] += 1
                    else:
                        since_registration[elapsed_days] = 1

                i += 1

    since_registration = {k: v for k, v in sorted(since_registration.items(), key=lambda x: x[0], reverse=True)}
    

    age = similar_dbs_dict = {k: v for k, v in sorted(age.items(), key=lambda x: int(x[0]), reverse=False) if int(k) <= 80}
    time_spent = {k: v for k, v in sorted(time_spent.items(), key=lambda x: float(x[0]), reverse=False)}
    

    # add all country names, and make everything lowercase
    valid_countries = [country.name.lower() for country in list(pycountry.countries)]
    aux = {}
    for k in location:
        if k.lower() in aux:
            aux[k.lower()] += location[k]
        else:
            aux[k.lower()] = location[k]

    location = aux

    # all locations with cyrilic letters should be changed to "Russia"
    # same for all locations containing "Moscow" or ".ru"
    to_delete = []
    to_add = {}
    for k in location:
        if (regex.search(r'\p{IsCyrillic}', k) != None) or ("moscow" in k) or (".ru" in k):
            to_delete.append(k)

            if "russia" in location:
                location["russia"] += location[k]
            else:
                if "russia" in to_add:
                    to_add["russia"] += location[k]
                else:
                    to_add["russia"] = location[k]
                
    location = {k: location[k] for k in location if k not in to_delete}
    location.update(to_add)

    to_delete = []
    to_add = {}
    for k in location:
        for valid_country in valid_countries:
            if valid_country in k:
                to_delete.append(k)
                
                if valid_country in location:
                    location[valid_country] += location[k]
                else:
                    if valid_country in to_add:
                        to_add[valid_country] += location[k]
                    else:
                        to_add[valid_country] = location[k]

                break
                    
    location = {k: location[k] for k in location if k not in to_delete}
    location.update(to_add)

    # print(sorted(valid_countries))

    # location = {k: location[k] for k in location if k in valid_countries}

    location = {k: v for k, v in sorted(location.items(), key=lambda x: x[1], reverse=True) if k != "none"}

    # plot_since_last_login()
    # plot_time_since_registration(since_registration)
    plot_age(age)
    # plot_time_spent(time_spent)
    # plot_location(location)