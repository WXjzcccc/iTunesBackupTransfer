from helper.DBHelper import DBHelper
from helper.FileHelper import FileHelper
import os

class Parser:
    def __init__(self):
        self.db = None
        self.file = None

    def setDB(self,db: str):
        self.db = DBHelper(db)

    def setFile(self,db: str,file: str):
        self.file = FileHelper(db,file)

    def get_childs(self,dir: str) -> list:
        lst = self.get_file_list()
        retval = []
        for row in lst:
            if row[1].startswith(dir):
                retval.append(row)
        return retval

    def get_file_list(self) -> list:
        lst = self.db.select('select fileID,domain,relativePath,flags from Files')
        retval = []
        for row in lst:
            file_id = row[0]
            domain = row[1]
            path = row[2]
            flags = row[3]
            domain = domain.replace('Domain','')
            if domain.__contains__('-'):
                domain = domain.replace('-','/',1)
            true_path = domain + '/' + path
            retval.append((file_id,true_path,flags))
        return retval
    
    def get_file_list1(self) -> list:
        lst = self.db.select('select fileID,domain,relativePath,flags from Files')
        return lst

    def get_roots(self) -> list:
        lst = self.db.select('select distinct(domain) from Files')
        retval = set()
        for row in lst:
            domain = row[0]
            domain = domain.replace('Domain','')
            if domain.__contains__('-'):
                domain = domain.replace('-','/',1)
            retval.add(domain.split('/')[0])
        return sorted(retval)

    def copy_all(self) -> None:
        for row in self.get_file_list1():
            file_id = row[0]
            domain = row[1]
            path = row[2]
            flags = row[3]
            self.file.create_file(file_id, domain, path, flags)

    def copy_selected(self,values: tuple,path: str,keepOriginPath: bool =False) -> None:
        dir = ''
        if len(values) == 1:
            dir = values[0]
        elif len(values) == 3:
            dir = values[1]
        if dir.endswith('/'):
            dir = dir[:-1]
        rows = self.get_childs(dir)
        if not keepOriginPath:
            for row in rows:
                tmp = row[1]
                tmp = tmp.replace(os.path.dirname(dir)+'/','')
                if tmp.startswith('/'):
                    tmp = tmp[1:]
                self.file.create_file2(row[0],tmp,row[2],path)
        else:
            for row in rows:
                self.file.create_file2(row[0],row[1],row[2],path)