class Member:

    def __init__(self, IdMember = 0, Site = 0, Username = "anonymous", 
                Avatar = '', RegistrationDate = "", Age = 0, Signature = "", Location = '', 
                localT = "", TimeSpent = 0, LastVisitDue = "", TotalPosts = 0, Reputation = 0, 
                Prestige = 0, Homepage = '', LastParse = "", parsed = False, URL = "",
                LastPostDate = "", FirstPostDate = "", Database = "postgres"):

        self.IdMember         = IdMember  # integer   
        self.Site             = Site  # integer     
        self.Username         = Username # string       
        self.Avatar           = Avatar # character varying (512)
        self.RegistrationDate = RegistrationDate # timestamp with time zone
        self.Age              = Age # integer
        self.Signature        = Signature # string
        self.Location         = Location # character varying (255)
        self.localT           = localT # timestamp with time zone
        self.TimeSpent        = TimeSpent  # numeric(20, 10)
        self.LastVisitDue     = LastVisitDue # timestamp with time zone
        self.TotalPosts       = TotalPosts # integer
        self.Reputation       = Reputation # integer
        self.Prestige         = Prestige # integer
        self.Homepage         = Homepage # character varying (512)
        self.LastParse        = LastParse # timestamp with time zone
        self.parsed           = parsed # boolean
        self.URL              = URL # string
        self.LastPostDate     = LastPostDate # timestamp with time zone
        self.FirstPostDate    = FirstPostDate # timestamp with time zone
        self.Database         = Database # I introduced this field to remember the origin of the user as the name of the db

    # returns a tuple (days, hours, minutes, seconds) representing the elapsed time 
    # since the user last logged in
    def get_last_active_dist(self):
        return (0, 0, 0, 0) # TODO

    def is_active(self):
        return True # TODO should involve self.get_active_time()

    # returns the age of this account as (days, hours, minutes, seconds)
    def get_age(self):
        return (0, 0, 0, 0)