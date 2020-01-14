class Data:

    def __init__(self): 
        self.members = [] # members will consist of a list of member objects
        self.posts = [] # posts will consist of a list of Post objects

    # adds a new member object to the list of members of this data_fetcher object
    def add_member(self, member):
        self.members += [member]

    # adds a new member object to the list of posts
    def add_post(self, post):
        self.posts += [post]

    # returns total number of members
    def get_user_count(self):
        return len(self.members)

    # returns total number of members
    def get_post_count(self):
        return len(self.posts)

    # returns a list of Member objects that correspond to active users
    def get_active_users(self):
        ret = []

        for m in self.members:

            if m.is_active():
                ret += [m]

        return ret

    # returns the Member object corresponding to the member with ID = ID
    def get_user_by_id(self, ID):
        for m in self.members:
            if m.IdMember == ID:
                return m

    # returns a list of Post objects that were written by Author with ID
    def get_posts_written_by(self, ID):

        ret = []

        for p in self.posts:
            if p.Author == ID:
                ret += [p]

        return ret
