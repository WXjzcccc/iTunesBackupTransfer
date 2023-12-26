from helper.DBHelper import DBHelper
from helper.FileHelper import FileHelper

class Parser:
    def __init__(self,path: str,target_path: str):
        self.db = DBHelper(path)
        self.file = FileHelper(path,target_path)

    def get_file_list(self) -> list:
        lst = self.db.select('select fileID,domain,relativePath,flags from Files')
        return lst

    def copy_all(self) -> None:
        for row in self.get_file_list():
            file_id = row[0]
            domain = row[1]
            path = row[2]
            flags = row[3]
            self.file.create_file(file_id, domain, path, flags)