import os
import subprocess
import psycopg2
import logging
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from Utils import get_time_diff, get_00_time_from, get_date_from, is_int

class postgres_interface:
    
    def __init__(self):
        self.psql_dumps_folder = "W:\\psql_dumps\\"
        self.db_names = self.__get_list_of_resources()

    def __get_list_of_resources(self):
        psql_dumps = []

        for r in os.listdir(self.psql_dumps_folder):
            psql_dumps += [r.split(".sql")[0]]

        return psql_dumps

    def stop_server(self):
        subprocess.call("pg_ctl.exe -D \"W:\crimebb\" stop")
        self.conn.close()

    def start_server(self):
        subprocess.call("pg_ctl.exe -D \"W:\crimebb\" start")
        self.conn = psycopg2.connect(host="localhost", database="postgres", user="postgres", password="postgrespass12345")
        # see https://stackoverflow.com/questions/34484066/create-a-postgres-database-using-python
        # this flag is used to enable the creation of databases (don't really know why it's needed)
        self.conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

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
        except psycopg2.errors.DuplicateDatabase as e:
            logging.error(e)
            # Database already existent, exit method
            # but first, restore path
            os.chdir(curr_folder)
            return

        logging.info("Populating db... " + db_name)
        # Use the psql dump to populate the database
        subprocess.call(["psql", "--username=postgres", "--dbname=" + db_name, "--file=" + res_name + ".sql"])
        logging.info("Done")
        # restore path
        os.chdir(curr_folder)

    # returns a list of strings, each string represting a line that was output while running the command
    def run_command(self, cmd, silent = False):
        if silent == False:
            logging.info("Running " + cmd)

        cur = self.conn.cursor()
        cur.execute(cmd)
        try:
            output = cur.fetchall()
        except psycopg2.ProgrammingError as e:
            # There may be no results to fetch from the command, so just return
            cur.close()
            self.conn.commit()
            return

        if "SELECT" in cmd and silent == False:
            logging.info("The query returned " + str(cur.rowcount) + " entries.")

        for i in range(len(output)):
            aux = ()
            for item in output[i]:
                if type(item) != str:
                    item = str(item)
                
                aux = aux + (item,)

            output[i] = aux

        cur.close()
        self.conn.commit()

        return output

    def init_dbs(self, reset):
        for res in self.db_names:
            self.init_database_from_resource(res, reset)

    # persists a list of accounts from all the databases to the members_file
    # an account is a tuple (ID, Username, Database, TimeSinceLastLogIn)
    # TODO double check that all the changes haven't introduced any bugs
    def persist_accounts_from_all_dbs(self, members_file_root):

        self.id_member = 0
        query_acc = "SELECT \"IdMember\", \"Username\" as uname, \"LastVisitDue\", \"LastParse\" FROM \"Member\" ORDER BY uname ASC;"

        # set this to True whenever you want accounts with the same username to be considered different accounts
        same_username_diff_account = False   
        
        for db_name in self.db_names:
            self.conn.close()
            #TODO consider reading the password from a file stored on the encrypted hard drive
            self.conn = psycopg2.connect(host="localhost", database=db_name, user="postgres", password="postgrespass12345")
            logging.info("Connected to " + db_name + ".")

            try:
                output = self.run_command(query_acc)
            except:
                logging.critical("Command failed to run.")
                exit()

            acc_list = []
            if same_username_diff_account:
                username_list = []
            else:
                username_set = set()

            ref_date = "None"

            # when getting the Member.txt data, instead of fetching the real LastVisitedDue values, retrieve only
            # the time elapsed when compared to the most recent log in on that website. Only store this tuple in
            # the LastVisitedDue field of the Member objects and use it to query the Data object on the set of active
            # users.

            #Every object in the database has a "LastParse" column, so using the first date encountered as a reference
            # may be very wrong. Wait for Ben to reply to the e-mail
            # spoke to Dylan Phelps, and having worked on the project over the summer, told me that "LastParse" should be used, even if it's incosistent in some places.

            for row in output:

                acc_ID   = row[0].strip()
                acc_name = row[1].strip()
                last_visit = row[2].strip().split() # this should now be a list containing info about the last login date and time
                                                    # the first element is the date
                                                    # the second element is the time of that day
                last_parse = row[3].strip().split() # this should be a list of an identical format about the last parse date and time

                # if no last visit time is provided, ignore this user
                if last_visit == ["None"]:
                    continue

                # if no last parse time is provided, ignore this user
                if last_parse == ["None"]:
                    continue
                
                #-----------------last_visit-----------------#
                # obtain the time zone difference (+/- 1 day) as an int, and the time at +00 as a tuple
                (last_visit_to_add, last_visit_time) = get_00_time_from(last_visit[1])
                # obtain the date as a tuple
                last_visit_date = get_date_from(last_visit[0])
                # may have to +/- 1 day due to time zone
                # TODO write a function for this, as it doesn't work all the time (obviously)
                last_visit_date = (last_visit_date[2] + last_visit_to_add,) + last_visit_date[1:]

                for x in last_visit_time:
                    last_visit_date += (x,) # we want date to contain 6 numbers: year, month, day, hour, minute, second

                #-----------------last_parse-----------------#
                # obtain the time zone difference (+/- 1 day) as an int, and the time at +00 as a tuple
                (last_parse_to_add, last_parse_time) = get_00_time_from(last_parse[1])
                # obtain the date as a tuple
                last_parse_date = get_date_from(last_parse[0])
                # may have to +/- 1 day due to time zone
                # TODO write a function for this, as it doesn't work all the time (obviously)
                last_parse_date = (last_parse_date[2] + last_parse_to_add,) + last_parse_date[1:]

                for x in last_parse_time:
                    last_parse_date += (x,) # we want date to contain 6 numbers: year, month, day, hour, minute, second    

                if acc_name == "NONE":
                    continue

                if not same_username_diff_account:

                    # If the same username was found in this database, ignore the current one
                    if acc_name not in username_set:
                        username_set.add(acc_name)

                        # how long has this user been inactive for? (time since last log in)
                        elapsed_time = get_time_diff(last_parse_date, last_visit_date)
                        # add this member to the list of members
                        acc_list += [(acc_ID, acc_name, db_name, elapsed_time)]
                    else:
                        # TODO can't log usernames that have non-ascii characters
                        logging.warning("Ignored " + str(acc_name.encode("utf-8")) + ". Already seen in this database: " + db_name)
                else:
                    username_list += [acc_name]

                    # how long has this user been inactive for? (time since last log in)
                    elapsed_time = get_time_diff(last_parse_date, last_visit_date)
                    # add this member to the list of members
                    acc_list += [(acc_ID, acc_name, db_name, elapsed_time)]

            members_file_name = members_file_root + "-" + db_name + ".txt"
            members_file_handle = open(members_file_name, "w+", encoding="utf-8")
            self.write_member_data(members_file_handle, acc_list)
            members_file_handle.close()

    # returns a lit of all the posts written by acc_ID
    def get_posts_from(self, acc_ID, db_name):
        # now, obtain all the posts written by this user on this website
        self.conn = psycopg2.connect(host="localhost", database=db_name, user="postgres", password="postgrespass12345")

        query_posts_template = "SELECT \"IdPost\", \"Author\", \"Content\" FROM \"Post\" WHERE \"Author\" = "
        query_curr_post = query_posts_template + str(acc_ID) + " ORDER BY \"IdPost\" DESC LIMIT 10;"

        try:
            posts_output = self.run_command(query_curr_post, silent = True)
        except:
            logging.critical("Command " + query_curr_post + " failed.")
            exit()

        ret = []

        for row in posts_output:

            post_ID   = row[0].strip()
            if not is_int(post_ID):
                continue

            author_ID = row[1].strip()
            if not is_int(author_ID):
                continue

            content = row[2]

            ret += [(post_ID, author_ID, content)]

        self.conn.close()
        return ret


    # writes the data about the members in the "accounts" list
    # the list contains tuples that represent (ID, Username, Database, TimeSinceLastLogIn)
    def write_member_data(self, g, accounts):

        for account in accounts:
            to_write = ""
            to_write += str(self.id_member) + " "
            l = len(account) - 1
            for f in account[1:l]:
                # TODO some usernames contain whitespaces, remove them (the whitespaces) or not?
                # currently removing them
                to_write += f.replace(" ", "") + " "
            f = str(account[l])
            to_write += f.replace(" ", "") + "\n"

            self.id_member += 1
            g.write(to_write)


if __name__ == "__main__":
    logging.basicConfig(filename='log_psql_interface.txt', filemode="w", level=logging.DEBUG)
    pi = postgres_interface()
    pi.start_server()
    
    # ONLY USE WHEN ADDING NEW DATABASES (careful not to set reset to True and wipe everything for no reason)
    pi.init_dbs(reset = False)
   
    members_file_root = os.path.join(os.getcwd(), "..\\res\\Members\\Members")
    logging.info("Writing members data...")
    pi.persist_accounts_from_all_dbs(members_file_root)
    logging.info("Done!")

    pi.stop_server()


