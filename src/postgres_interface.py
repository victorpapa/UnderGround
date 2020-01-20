import os
import subprocess
from Utils import get_time_diff, get_00_time_from, get_date_from

class postgres_interface:
    
    def __init__(self):
        self.psql_dumps_folder = "W:\\psql_dumps\\"
        self.db_names = self.__get_list_of_resources()

    def __get_list_of_resources(self):
        psql_dumps = []

        for r in os.listdir(self.psql_dumps_folder):
            psql_dumps += [r.split(".sql")[0]]

        return psql_dumps

    def disconnect(self):
        subprocess.call("pg_ctl.exe -D \"W:\crimebb\" stop")

    def connect(self):
        subprocess.call("pg_ctl.exe -D \"W:\crimebb\" start")

    def init_database_from_resource(self, res_name, reset):
        curr_folder = os.getcwd()
        os.chdir(self.psql_dumps_folder)
        # TODO what does "-1" do as an argument to psql?

        db_name = res_name.split(".sql")[0]
        # Use when you want to reset the database
        if reset == True:
            try:
                self.run_command("DROP DATABASE \"" + db_name + "\";")
            except:
                pass

        try:
            # Create the database
            self.run_command("CREATE DATABASE \"" + db_name + "\";")
        except:
            # Database already existent, exit method
            # but first, restore path
            os.chdir(curr_folder)
            return

        # Use the psql dump to populate the database
        subprocess.call(["psql", "--username=postgres", "--dbname=" + db_name, "--file=" + res_name + ".sql"])

        # restore path
        os.chdir(curr_folder)

    def run_command(self, cmd, db_name = "postgres"):
        print("Running " + cmd + " ...")
        output = subprocess.check_output(["psql", "--username=postgres", "--dbname=" + db_name, "-c", cmd])

        # the output returned by check_output is of type "bytes", which needs to be decoded
        output = output.decode("utf-8")

        return output

    def init_dbs(self, reset):
        for res in self.db_names:
            pi.init_database_from_resource(res, reset)

    # returns a list of accounts from all the databases
    # an account is a tuple (ID, Username, Database, TimeSinceLastLogIn)
    def get_accounts_from_all_dbs(self, query):

        accounts = []

        for db_name in self.db_names:
            print(db_name)

            try:
                output = pi.run_command(query, db_name)
            except:
                continue

            output = output.split("\r\n")
            aux = []
            ref_date = "None"

            # when getting the Member.txt data, instead of fetching the real LastVisitedDue values, retrieve only
            # the time elapsed when compared to the most recent log in on that website. Only store this tuple in
            # the LastVisitedDue field of the Member objects and use it to query the Data object on the set of active
            # users.

            # iterate from 2, because the first two lines are the title and a delimiting line ------
            # stop at len(output) - 4, because the last 2 are just empty strings, and the one before contains the number of
            # rows, e.g. "(1064 rows)"
            print(output[len(output) - 3])

            for i in range(2, len(output) - 3):
                row = output[i].split("|")

                if len(row) != 3:
                    # Some names contain " | ", so we have to re-build them
                    for i in range(2, len(row) - 1):
                        row[1] += "|" + row[i]
                    row[2] = row[len(row) - 1]
                    row = row[:3]

                    print(row[1])

                ID   = row[0].strip()
                name = row[1].strip()
                last_visit = row[2].strip().split() # this should now be a list containing info about the last login date and time
                                                    # the first element is the date
                                                    # the second element is the time of that day

                # if no last visit time is provided, ignore this user
                if last_visit == []:
                    continue
                
                # obtain the time zone difference (+/- 1 day) as an int, and the time at +00 as a tuple
                (to_add, time) = get_00_time_from(last_visit[1])
                # obtain the date as a tuple
                date = get_date_from(last_visit[0])
                # may have to +/- 1 day due to time zone
                date = (date[0] + to_add,) + date[1:]

                for x in time:
                    date += (x,) # we want date to contain 6 numbers: year, month, day, hour, minute, second

                # the first date and time present in the database will be the references to the other dates and times
                if ref_date == "None":
                    ref_date = date

                if name != "NONE":
                    # how long has this user been inactive for? (time since last log in)
                    elapsed_time = get_time_diff(ref_date, date)
                    aux += [(ID, name, db_name, elapsed_time)]

            accounts += aux

        return accounts


# writes the data about the members in the "accounts" list
# the list contains tuples that represent (ID, Username, Database, TimeSinceLastLogIn)
def write_member_data(members_file, accounts):
    g = open(members_file, "w+", encoding="utf-8")

    print("Writing members data...")
    id_member = 0
    for account in accounts:
        to_write = ""
        to_write += str(id_member) + " "
        l = len(account) - 1
        for f in account[1:l]:
            # TODO some usernames contain whitespaces, remove them or not?
            to_write += f.replace(" ", "") + " "
        f = str(account[l])
        to_write += f.replace(" ", "") + "\n"

        id_member += 1
        g.write(to_write)
        
    print("Done!")
    g.close()


if __name__ == "__main__":
    pi = postgres_interface()
    pi.connect()
    
    # pi.init_dbs(reset = False)
    query = "SELECT \"IdMember\", \"Username\", \"LastVisitDue\" as lv  FROM \"Member\" ORDER BY lv DESC;"
    accounts = pi.get_accounts_from_all_dbs(query)

    pi.disconnect()

    members_file = os.path.join(os.getcwd(), "..\\res\\Members.txt")
    write_member_data(members_file, accounts)
    

    
