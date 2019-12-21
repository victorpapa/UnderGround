class Data_fetcher:

    def __init__(self): 
        self.members = [] # members will consist of a list of member objects

    # adds a new member object to the list of members of this data_fetcher object
    def add_member(self, member):
        self.members += [member]

    # returns total number of members
    def get_user_count(self):
        return len(self.members)

    # returns a dictionary mapping user IDs to a pair consisting of
    # the time elapsed since last log in, and 
    # the age of the user account, 
    # both represented by tuples (days, hours, minutes, seconds)
    def get_active_users(self):
        ret = {}

        for m in self.members:
            active = m.get_last_active_dist()
            age = m.get_age()

            if m.is_active():
                ret[m.IdMember] = (active, age)

        return ret
