import os
import shutil
import biplist
from kurtbrose.decryptor_CLI import decrypt_file

class FileHelper:
    def __init__(self,path: str,target_path: str):
        # 备份文件的根目录，即包含Info.plist、Manifest.db的那个目录
        self.backup_dir = path
        # 解析后文件存放的根目录
        self.target_dir = target_path.replace('\\','/').replace('//','/')
        if self.target_dir[-1] != '/':
            self.target_dir += '/'

    def get_file_list(self,file_id: str,domain: str,file_path: str, flag: int) -> list:
        """
        @file_id:       文件ID
        @domain:        包目录
        @file_path:     文件路径
        @flag:          文件标记，1表示文件，2表示目录
        return:         文件列表
        """
        domain = domain.replace('Domain','')
        if domain.__contains__('-'):
            domain = domain.replace('-','/')
        true_path = domain + '/' + file_path
        print(true_path)

    def create_file(self,file_id: str,domain: str,file_path: str, flag: int) -> None:
        """
        @file_id:       文件ID
        @domain:        包目录
        @file_path:     文件路径
        @flag:          文件标记，1表示文件，2表示目录
        """
        domain = domain.replace('Domain','')
        if domain.__contains__('-'):
            domain = domain.replace('-','/',1)
        true_path = self.target_dir + domain + '/' + file_path
        if flag == 2:
            # 创建的是目录
            if file_path == '':
                os.makedirs(self.target_dir + domain,exist_ok=True)
            else:
                os.makedirs(true_path,exist_ok=True)
        elif flag == 1:
            # 复制对应的文件
            dictory = os.path.dirname(true_path)
            if not os.path.exists(dictory):
                os.makedirs(dictory,exist_ok=True)
            # fileID的前两位被iTunes作为索引目录，因此需要拼接
            source = self.backup_dir + "/" + file_id[:2] + "/" + file_id
            shutil.copy2(source,true_path)

    def create_file2(self,file_id: str,file_path: str, flag: int, target_path: str) -> None:
        """
        @file_id:       文件ID
        @file_path:     文件路径
        @flag:          文件标记，1表示文件，2表示目录
        """
        true_path = target_path + '/' + file_path
        if flag == 2:
            # 创建的是目录
                os.makedirs(true_path,exist_ok=True)
        elif flag == 1:
            # 复制对应的文件
            dictory = os.path.dirname(true_path)
            if not os.path.exists(dictory):
                os.makedirs(dictory,exist_ok=True)
            # fileID的前两位被iTunes作为索引目录，因此需要拼接
            source = self.backup_dir + "/" + file_id[:2] + "/" + file_id
            shutil.copy2(source,true_path)

    def create_file3(self,file_id: str,domain: str,file_path: str, flag: int,bplist,keybag) -> None:
        """
        @file_id:       文件ID
        @domain:        包目录
        @file_path:     文件路径
        @flag:          文件标记，1表示文件，2表示目录
        """
        domain = domain.replace('Domain','')
        if domain.__contains__('-'):
            domain = domain.replace('-','/',1)
        true_path = self.target_dir + domain + '/' + file_path
        if flag == 2:
            # 创建的是目录
            if file_path == '':
                os.makedirs(self.target_dir + domain,exist_ok=True)
            else:
                os.makedirs(true_path,exist_ok=True)
        elif flag == 1:
            # 复制对应的文件
            dictory = os.path.dirname(true_path)
            if not os.path.exists(dictory):
                os.makedirs(dictory,exist_ok=True)
            # fileID的前两位被iTunes作为索引目录，因此需要拼接
            source = self.backup_dir + "/" + file_id[:2] + "/" + file_id
            source_size = os.path.getsize(source)
            with open(source,'rb') as source:
                source_data = source.read()
            with open(true_path,'wb') as target:
                target.write(decrypt_file(keybag,bplist,source_data,source_size))

    def create_file4(self,file_id: str,file_path: str, flag: int, target_path: str,bplist,  keybag) -> None:
        """
        @file_id:       文件ID
        @file_path:     文件路径
        @flag:          文件标记，1表示文件，2表示目录
        @bplsit:        数据库中的plist数据
        """
        true_path = target_path + '/' + file_path
        if flag == 2:
            # 创建的是目录
                os.makedirs(true_path,exist_ok=True)
        elif flag == 1:
            # 复制对应的文件
            dictory = os.path.dirname(true_path)
            if not os.path.exists(dictory):
                os.makedirs(dictory,exist_ok=True)
            # fileID的前两位被iTunes作为索引目录，因此需要拼接
            source = self.backup_dir + "/" + file_id[:2] + "/" + file_id
            source_size = os.path.getsize(source)
            with open(source,'rb') as source:
                source_data = source.read()
            with open(true_path,'wb') as target:
                target.write(decrypt_file(keybag,bplist,source_data,source_size))
