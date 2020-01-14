import os
import subprocess

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

    def init_database_from_resource(self, res_name):
        curr_folder = os.getcwd()
        os.chdir(self.psql_dumps_folder)
        # TODO what does "-1" do as an argument to psql?

        db_name = res_name.split(".sql")[0]

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
        print(output)

        return str(output)

    def get_list_of_resources(self):
        psql_dumps = []

        for r in os.listdir(self.psql_dumps_folder):
            psql_dumps += [r.split(".sql")[0]]

        return psql_dumps


if __name__ == "__main__":
    pi = postgres_interface()
    pi.connect()

    # for res in pi.get_list_of_resources():
    pi.init_database_from_resource("crimebb-freehacks-2020-01-02")

    try:
        command = "SELECT \"Username\" FROM \"Member\" LIMIT 4000;"
        db_name = "crimebb-freehacks-2020-01-02"
        output = pi.run_command(command, db_name)
    finally:
        pi.disconnect()

    members_file = os.path.join(os.getcwd(), "..\\res\\Members.txt")
    g = open(members_file, "w+")
    g.write(output)
    g.close()

    