import os
import subprocess
import psycopg2
import logging
from Post import Post
from Member import Member
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT, AsIs
from psycopg2.sql import Identifier, SQL, Literal
from Utils import get_time_diff, get_00_time_from, get_date_from, is_int, timestamped

class Postgres_interface:
    
    def __init__(self):
        self.psql_dumps_folder = "W:\\psql_dumps\\"
        self.db_names = self.__get_list_of_resources()
        self.__fetch_psql_pass()
        self.__define_constants()
        
    def __define_constants(self):
        self.query_posts_template = "SELECT \"Timestamp\", \"Author\", \"Content\" FROM \"Post\" WHERE \"Author\" = %s;"
        self.query_members_w_posts_template = "SELECT \"Author\" FROM \"Post\" WHERE \"Author\" = %s LIMIT 1;"
        self.query_members = "SELECT \"IdMember\", \"Username\" as uname, \"LastVisitDue\", \"LastParse\" FROM \"Member\" ORDER BY uname ASC;"
        self.query_member_metadata = "SELECT \"Age\", \"TimeSpent\", \"Location\", \"RegistrationDate\", \"FirstPostDate\", \"LastPostDate\", \"TotalPosts\" FROM \"Member\" WHERE \"IdMember\" = %s;"
        self.ERR_STRING = "Command above failed to execute. Exiting..."
        
    def __fetch_psql_pass(self):
        pass_file = os.path.join("W:", "Secret.txt")
        pass_file_handler = open(pass_file, "r", encoding="utf-8")
        self.password = pass_file_handler.readline()
        pass_file_handler.close()

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
        
        # default connection encoding is UTF-8
        # self.conn.set_client_encoding("UTF8")
        self.conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

    def init_database_from_resource(self, res_name, reset):
        curr_folder = os.getcwd()
        os.chdir(self.psql_dumps_folder)
        # what does "-1" do as an argument to psql?
        # -1
        # --single-transaction
        # When psql executes a script with the -f option, adding this option wraps BEGIN/COMMIT around the script to execute it as a single transaction. This ensures that either all the commands complete successfully, or no changes are applied.

        db_name = res_name.split(".sql")[0]
        # Use when you want to reset the database
        if reset == True:
            try:
                self.__run_command(SQL("DROP DATABASE {};").format(Identifier(db_name)))
            except:
                pass
        
        try:
            # Create the database
            self.__run_command(SQL("CREATE DATABASE {};").format(Identifier(db_name)))
        except psycopg2.errors.DuplicateDatabase as e:
            logging.debug(timestamped(str(e)))
            # Database already existent, exit method
            # but first, restore path
            os.chdir(curr_folder)
            return

        logging.info(timestamped("Populating db... " + db_name))
        # Use the psql dump to populate the database
        subprocess.call(["psql", "--username=postgres", "--dbname=" + db_name, "--file=" + res_name + ".sql"])
        logging.info(timestamped("Done"))
        # restore path
        os.chdir(curr_folder)

    # returns a list of strings, each string represting a line that was output while running the command
    # only use the try except when silent is set to False, in order to see what actually failed
    def __run_command(self, cmd, args = (), silent = False):

        cur = self.conn.cursor()
        if silent == False:
            # mogrify returns the query that we are about to send to the dataabase as a byte array (type "bytes")
            logging.info(timestamped(cur.mogrify(cmd, args).decode("utf-8")))

        cur.execute(cmd, args)
        try:
            output = cur.fetchall()
        except psycopg2.ProgrammingError as e:
            # There may be no results to fetch from the command, so just return
            cur.close()
            self.conn.commit()
            return

        if "SELECT" in cmd and silent == False:
            logging.info(timestamped("The query returned " + str(cur.rowcount) + " entries."))

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

    # persists a list of members from all the databases to the members_file
    # a member is a tuple (ID, Username, Database, TimeSinceLastLogIn)
    def persist_members_from_all_dbs(self, members_file_root):

        self.id_member = 0
        
        # set this to True whenever you want members with the same username to be considered different members
        same_username_diff_member = False   
        
        for db_name in self.db_names:
            # initially connected to db "postgres", so can safely close connection
            self.conn.close()

            self.conn = psycopg2.connect(host="localhost", database=db_name, user="postgres", password="postgrespass12345")
            logging.info(timestamped("Connected to " + db_name + "."))

            try:
                members_output = self.__run_command(self.query_members)
            except:
                logging.critical(timestamped(self.ERR_STRING))
                exit()

            member_list = []
            if same_username_diff_member:
                username_list = []
            else:
                username_set = set()

            ref_date = "None"

            # when getting the Member.txt data, instead of fetching the real LastVisitedDue values, retrieve only
            # the time elapsed when compared to the most recent log in on that website. Only store this tuple in
            # the LastVisitedDue field of the Member objects and use it to query the Data object on the set of active
            # users.

            # Every object in the database has a "LastParse" column, so using the first date encountered as a reference
            # may be very wrong. Wait for Ben to reply to the e-mail
            # spoke to Dylan Phelps, and having worked on the project over the summer, told me that "LastParse" should be used, even if it's incosistent in some places.

            for row in members_output:

                member_ID   = row[0].strip()
                
                args = (str(member_ID),)

                posts_output = self.__run_command(self.query_members_w_posts_template, args, silent = True)

                if len(posts_output) == 0:
                    logging.info(timestamped("User " + str(member_ID) + " from database " + db_name + " has not written any posts."))
                    continue

                member_name = row[1].strip()
                if member_name == "NONE":
                    continue
                
                last_visit = row[2].strip().split() # this should now be a list containing info about the last login date and time
                                                    # the first element is the date
                                                    # the second element is the time of that day
                # if no last visit time is provided, ignore this user
                if last_visit == ["None"]:
                    continue

                last_parse = row[3].strip().split() # this should be a list of an identical format about the last parse date and time

                # if no last parsed time is provided, ignore this user
                if last_parse == ["None"]:
                    continue
                
                #-----------------last_visit-----------------#
                # obtain the time zone difference (+/- 1 day) as an int, and the time at +00 as a tuple
                (last_visit_to_add, last_visit_time) = get_00_time_from(last_visit[1])
                # obtain the date as a tuple
                last_visit_date = get_date_from(last_visit[0])
                # may have to +/- 1 day due to time zone

                # this may overflow the number of possible days in a month, but I don't think it really matters
                last_visit_date = last_visit_date[0:2] + (last_visit_date[2] + last_visit_to_add,) + last_visit_date[3:]

                for x in last_visit_time:
                    last_visit_date += (x,) # we want date to contain 6 numbers: year, month, day, hour, minute, second

                #-----------------last_parse-----------------#
                # obtain the time zone difference (+/- 1 day) as an int, and the time at +00 as a tuple
                (last_parse_to_add, last_parse_time) = get_00_time_from(last_parse[1])
                # obtain the date as a tuple
                last_parse_date = get_date_from(last_parse[0])
                # may have to +/- 1 day due to time zone

                # this may overflow the number of possible days in a month, but I don't think it really matters
                last_parse_date = last_parse_date[0:2] + (last_parse_date[2] + last_parse_to_add,) + last_parse_date[3:]

                for x in last_parse_time:
                    last_parse_date += (x,) # we want date to contain 6 numbers: year, month, day, hour, minute, second    

                if not same_username_diff_member:

                    # If the same username was found in this database, ignore the current one
                    if member_name not in username_set:
                        username_set.add(member_name)

                        # how long has this user been inactive for? (time since last log in)
                        elapsed_time = get_time_diff(last_parse_date, last_visit_date)
                        # add this member to the list of members
                        member_list += [(member_ID, member_name, db_name, elapsed_time)]
                    else:
                        logging.warning(timestamped("Ignored " + member_name + ". Already seen in this database: " + db_name))
                else:
                    username_list += [member_name]

                    # how long has this user been inactive for? (time since last log in)
                    elapsed_time = get_time_diff(last_parse_date, last_visit_date)
                    # add this member to the list of members
                    member_list += [(member_ID, member_name, db_name, elapsed_time)]

            members_file_name = members_file_root + "-" + db_name + ".txt"
            members_file_handle = open(members_file_name, "w+", encoding="utf-8")
            self.write_member_data(members_file_handle, member_list)
            members_file_handle.close()

    # returns a list of all the posts written by member
    def get_posts_from(self, member):

        member_ID = member.IdMember
        db_name =  member.Database

        # now, obtain all the posts written by this user on this website
        self.conn = psycopg2.connect(host="localhost", database=db_name, user="postgres", password="postgrespass12345")

        # AsIs is used here in order to prevent this argument from being quoted in the SQL query
        args = (AsIs(str(member_ID) + " ORDER BY \"Timestamp\" DESC"),)

        posts_output = self.__run_command(self.query_posts_template, args, silent = True)

        ret = []

        for row in posts_output:

            post_ID   = row[0].strip()
            author_ID = row[1].strip()
            content   = row[2]

            ret += [Post(IdPost=post_ID, Author=author_ID, Content=content)]

        self.conn.close()
        return ret

    def get_members_metadata(self, members):

        members_metadata = []

        for member in members:
            member_ID = member.IdMember
            db_name =  member.Database

            # now, obtain all the posts written by this user on this website
            self.conn = psycopg2.connect(host="localhost", database=db_name, user="postgres", password="postgrespass12345")

            # AsIs is used here in order to prevent this argument from being quoted in the SQL query
            args = (str(member_ID),)

            member_metadata = self.__run_command(self.query_member_metadata, args, silent = True)

            members_metadata.append(member_metadata)

        return members_metadata
            



    # writes the data about the members in the "members" list
    # the list contains tuples that represent (ID, Username, Database, TimeSinceLastLogIn)
    def write_member_data(self, g, members):

        for member in members:
            to_write = ""
            to_write += str(self.id_member) + " "
            l = len(member) - 1
            for f in member[:l]:
                # some usernames contain whitespaces, remove them (the whitespaces) or not?
                # currently removing them
                to_write += f.replace(" ", "") + " "
            f = str(member[l])
            to_write += f.replace(" ", "") + "\n"

            self.id_member += 1
            g.write(to_write)

# initialising the logging file and setting the correct working directory
def init_env():
    os.chdir("D:\\Program Files (x86)\\Courses II\\Dissertation\\res")
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger_handler = logging.FileHandler("log_psql_interface.txt", "w")
    logger_handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
    logger.addHandler(logger_handler)
    os.chdir("D:\\Program Files (x86)\\Courses II\\Dissertation\\src")

if __name__ == "__main__":
    
    init_env()

    pi = Postgres_interface()
    pi.start_server()
    
    # ONLY USE WHEN ADDING NEW DATABASES (careful not to set reset to True and wipe everything for no reason)
    pi.init_dbs(reset = False)
   
    members_file_root = os.path.join(os.getcwd(), "..\\res\\Members\\Members")
    logging.info(timestamped("Writing members data..."))
    pi.persist_members_from_all_dbs(members_file_root)
    logging.info(timestamped("Done!"))

    # TODO
    # pi.stop_server()


