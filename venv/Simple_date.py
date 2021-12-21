class SimpleDate:

    def __init__(self, year, month, date):
        try:
            self.year = int(year)
            self.month = int(month)
            self.date = int(date)
        except Exception  as e:
            print("Could not create date object")

    def print(self):
        print(str(self.year) + '.' + str(self.month) + '.' + str(self.date))