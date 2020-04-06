import os
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pycountry
from Utils import get_dict_keys, get_dict_values

if __name__ == "__main__":
    os.chdir(os.path.join("..", *["res", "Members_metadata"]))
    metadata_files = os.listdir(os.getcwd())

    age = {}
    time_spent = {}
    location = {}

    for metadata_file in metadata_files:
        metadata_file_handler = open(metadata_file, "r", encoding="utf-8")

        for metadata_row in metadata_file_handler:
            metadata_fields = metadata_row.split()

            for i in range(len(metadata_fields)):
                curr_field = metadata_fields[i]

                if i == 0: # Age
                    if curr_field == "0":
                        continue

                    if curr_field in age:
                        age[curr_field] += 1
                    else:
                        age[curr_field] = 1
                elif i == 1: # TimeSpent
                    if curr_field == "0E-10":
                        continue

                    if curr_field in time_spent:
                        time_spent[curr_field] += 1
                    else:
                        time_spent[curr_field] = 1
                elif i == 2: # Location
                    if curr_field.lower() == "none":
                        continue

                    if curr_field in location:
                        location[curr_field] += 1
                    else:
                        location[curr_field] = 1

    age = similar_dbs_dict = {k: v for k, v in sorted(age.items(), key=lambda x: x[0], reverse=False)}
    time_spent = {k: v for k, v in sorted(time_spent.items(), key=lambda x: x[0], reverse=True)}
    location = {k: v for k, v in sorted(location.items(), key=lambda x: x[1], reverse=True)}
    location = {k: location[k] for k in location if k in [country.name for country in list(pycountry.countries)]}


    plt.plot(get_dict_keys(age), get_dict_values(age))
    plt.xlabel("Age")
    plt.ylabel("Number of Members")
    plt.show()

    plt.plot(get_dict_keys(time_spent), get_dict_values(time_spent))
    plt.xticks(get_dict_keys(time_spent)[::len(time_spent) // 10])
    plt.xlabel("Time Spent")
    plt.ylabel("Number of Members")
    plt.show()
    
    plt.plot(get_dict_keys(location)[:10], get_dict_values(location)[:10])
    plt.xlabel("Location")
    plt.ylabel("Number of Members")
    plt.show()