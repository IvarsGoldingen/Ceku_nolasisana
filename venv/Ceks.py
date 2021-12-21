class Ceks:
    
    
    def __init__(self, ceka_nr, sasijas_nr, veikals, pvn_nr, summa, datums, file_name):
        self.ceka_nr = ceka_nr
        self.sasijas_nr = sasijas_nr
        self.veikals = veikals
        self.pvn_nr = pvn_nr
        self.summa = summa
        self.datums = datums
        self.file_name = file_name
        
    
    def print(self):
        print("Čeka dati:\n"
              "Veikals: %s\n"
              "Čeka nr.: %s\n"
              "Šasijas nr.: %s\n"
              "PVN nr.: %s\n"
              "Summa: %s\n"
              "Datums: %s\n"% 
              (self.veikals, 
               self.ceka_nr,
               self.sasijas_nr,
               self.pvn_nr,
               self.summa,
               self.datums))