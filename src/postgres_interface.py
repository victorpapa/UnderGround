import os
import subprocess
from Utils import get_time_diff, get_00_time_from, get_date_from

class postgres_interface:
    
    def __init__(self):
        self.psql_dumps_folder = "W:\\psql_dumps\\"

    def disconnect(self):
        subprocess.call("pg_ctl.exe -D \"W:\crimebb\" stop")
        self.is_connected = True

    def connect(self):
        subprocess.call("pg_ctl.exe -D \"W:\crimebb\" start")
        self.is_connected = False
        self.get_list_of_resources()

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

    def get_list_of_resources(self):
        psql_dumps = []

        for r in os.listdir(self.psql_dumps_folder):
            psql_dumps += [r.split(".sql")[0]]

        return psql_dumps

    def init_dbs(self, db_names):
        for res in db_names:
            pi.init_database_from_resource(res, reset)


if __name__ == "__main__":
    pi = postgres_interface()
    pi.connect()
    db_names = pi.get_list_of_resources()
    # pi.init_dbs(db_names, reset = False)

    accounts = []

    for db_name in db_names:
        print(db_name)
        command = "SELECT \"IdMember\", \"Username\", \"LastVisitDue\" as lv  FROM \"Member\" ORDER BY lv DESC LIMIT 2000;"

        try:
            output = pi.run_command(command, db_name)
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
        for i in range(2, len(output) - 3):
            row = output[i].split(" | ")

            if len(row) != 3:
                print(output[i] + " was skipped.")
                continue

            ID   = row[0].strip()
            name = row[1].strip()
            last_visit = row[2].strip().split()

            # if no last visit time is provided, ignore this user
            if last_visit == []:
                continue
            
            if "Money" in last_visit[1]:
                a = 1
                a -= 1
                
            (to_add, time) = get_00_time_from(last_visit[1])
            date = get_date_from(last_visit[0])
            # may have to add/remove one day due to time zone
            date = (date[0] + to_add,) + date[1:]

            for x in time:
                date += (x,)


            if ref_date == "None":
                ref_date = date

            if name != "NONE":
                if (ID, name, db_name) not in accounts:
                    elapsed_time = get_time_diff(ref_date, date)
                    aux += [(ID, name, db_name, elapsed_time)]


        accounts += aux

        

    pi.disconnect()

    members_file = os.path.join(os.getcwd(), "..\\res\\Members.txt")
    g = open(members_file, "w+", encoding="utf-8")

    print("Writing members data...")
    for entry in accounts:
        to_write = ""
        l = len(entry) - 1 
        for i in range(l):
            to_write += str(entry[i]).replace(" ", "") + " "
        to_write += str(entry[l]).replace(" ", "") + "\n"

        g.write(to_write)
        
    print("Done!")
    g.close()

    
