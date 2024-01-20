from helper.DBHelper import DBHelper
from helper.FileHelper import FileHelper
import os
import biplist
from kurtbrose.decryptor_CLI import decrypt_manifest_db,Keybag
import time

class Parser:
    def __init__(self):
        self.db = None
        self.file = None
        self.keybag = None
        self.manifest_key = None
        self.password = None

    def setDB(self,db: str):
        self.db = DBHelper(db)

    def setFile(self,db: str,file: str):
        self.file = FileHelper(db,file)

    def check_encryption(self,path)  -> bool:
        # 检测是否是加密备份
        with open(f'{path}/Manifest.plist','rb') as plist:
            manifest_plist = biplist.readPlist(plist)
            try:
                self.keybag = manifest_plist['BackupKeyBag']
                self.manifest_key = manifest_plist['ManifestKey']
            except KeyError:
                return False
            return True

    def decrypt_db(self,backup_path :str,password :str) -> str:
        """
        @backup_path:   备份路径
        @password:      备份密码
        @return:        返回解密后的数据库路径
        """
        data = decrypt_manifest_db(self.keybag,password,self.manifest_key,backup_path+'/Manifest.db')
        self.password = password
        salt = str(time.time())[:10]
        os.makedirs(f'./tmp',exist_ok=True)
        if data != b'':
            with open(f'./tmp/Manifest{salt}.db','wb') as f:
                f.write(data)
            return os.path.abspath(f'./tmp/Manifest{salt}.db')
        return ''


    def get_childs(self,dir: str) -> list:
        lst = self.get_file_list()
        retval = []
        for row in lst:
            if row[1].startswith(dir):
                retval.append(row)
        return retval

    def get_file_list(self) -> list:
        lst = self.db.select("select fileID,domain,replace(relativePath,':','-') path,flags,file from Files order by domain,path")
        retval = []
        for row in lst:
            file_id = row[0]
            domain = row[1]
            path = row[2]
            flags = row[3]
            bplist = row[4]
            domain = domain.replace('Domain','')
            if domain.__contains__('-'):
                domain = domain.replace('-','/',1)
            true_path = domain + '/' + path
            retval.append((file_id,true_path,flags,bplist))
        return retval
    
    def get_file_list1(self) -> list:
        lst = self.db.select("select fileID,domain,replace(relativePath,':','-') path,flags,file from Files order by domain,path")
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

    def copy_all(self,flag) -> None:
        """
        @flag:      判断是否加密
        """
        keybag = Keybag(self.keybag)
        keybag.unlockWithPasscode(self.password.encode('utf8'))
        for row in self.get_file_list1():
            file_id = row[0]
            domain = row[1]
            path = row[2]
            flags = row[3]
            bplist = row[4]
            if flag:
                self.file.create_file3(file_id, domain, path,flags,bplist,keybag)
            else:
                self.file.create_file(file_id, domain, path, flags)

    def copy_selected(self,values: tuple,path: str,flag: bool,keepOriginPath: bool =False) -> None:
        """
        @flag:      判断是否加密
        """
        dir = ''
        if len(values) == 1:
            dir = values[0]
        elif len(values) == 3:
            dir = values[1]
        if dir.endswith('/'):
            dir = dir[:-1]
        rows = self.get_childs(dir)
        keybag = Keybag(self.keybag)
        keybag.unlockWithPasscode(self.password.encode('utf8'))
        if not keepOriginPath:
            for row in rows:
                tmp = row[1]
                # tmp = tmp.replace(os.path.dirname(dir)+'/','')
                if tmp.startswith('/'):
                    tmp = tmp[1:]
                print('2'+tmp)
                if flag:
                    self.file.create_file4(row[0],tmp,row[2],path,row[3],keybag)
                else:
                    self.file.create_file2(row[0],tmp,row[2],path)
        else:
            for row in rows:
                pass
                if flag:
                    self.file.create_file4(row[0],tmp,row[2],path,row[3],keybag)
                else:
                    self.file.create_file2(row[0],tmp,row[2],path)
