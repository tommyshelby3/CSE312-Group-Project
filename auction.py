import database as db

class Auction:
    def __init__(self, title, description, price, imagepath):
        self.title = title
        self.description = description
        self.price = price
        self.imagepath = imagepath
        self.update_datebase()
        
        
    def update_datebase (self):
        db.create_auction_item(self.title, self.description, self.price, self.imagepath)