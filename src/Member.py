from Utils import is_longer_than

class Member:

    # TODO write getters and setters and re-factor code
    # TODO make all the methods that need to be private private

    def __init__(self, GlobalId = 0, IdMember = 0, Site = 0, Username = "", 
                Avatar = '', RegistrationDate = "", Age = 0, Signature = "", Location = '', 
                localT = "", TimeSpent = 0, LastVisitDue = "", TotalPosts = 0, Reputation = 0, 
                Prestige = 0, Homepage = '', LastParse = "", parsed = False, URL = "",
                LastPostDate = "", FirstPostDate = "", Database = "postgres"):

        # TODO comment the fields that are not used by the program
        self.GlobalId         = GlobalId # integer
        self.IdMember         = IdMember  # integer   
        # self.Site             = Site  # integer     
        self.Username         = Username # string       
        self.Avatar           = Avatar # character varying (512)
        self.RegistrationDate = RegistrationDate # timestamp with time zone
        self.Age              = Age # integer
        self.Signature        = Signature # string
        self.Location         = Location # character varying (255)
        self.localT           = localT # timestamp with time zone
        # TODO what is the time spent measured in?  
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
        self.Database         = Database # I introduced this field to remember the origin of the member as the name of the db
        self.Manual_Posts     = [] # for testing purposes

    def is_active(self):
        if is_longer_than(self.LastVisitDue, 30):
            return False
    
        return True

    def get_age(self):
        return self.Age