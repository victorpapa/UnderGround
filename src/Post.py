class Post:

    # TODO write getters and setters and re-factor code

    def __init__(self, IdPost = 0, Author = 0, Thread = 0, TimeStamp = "", Content = "", 
                AuthorNumPosts = 0, AuthorReputation = 0, LastParse = "", parsed = False, 
                Site = 0, CitedPost = [], AuthorName = '', Likes = 0):
        
        # TODO comment the fields that are not used by the program
        # TODO see if the CitedPost or AuthorName could be used somewhere (don't think so at this point)
        self.IdPost = IdPost # integer
        self.Author = Author # integer
        self.Thread = Thread # integer
        self.TimeStamp = TimeStamp # timestamp with time zone
        self.Content = Content # string
        self.AuthorNumPosts = AuthorNumPosts # integer
        self.AuthorReputation = AuthorReputation # integer
        self.LastParse = LastParse # timestamp with time zone
        self.parsed = parsed # boolean
        self.Site = Site # integer
        self.CitedPost = CitedPost # bigint[] 
        self.AuthorName = AuthorName # characterD
        self.Likes = Likes # integer
