import argparse
from myparser.Parser import Parser

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='iTunesBackupTransfer')
    parser.add_argument('backup_path', help='iTunes备份目录')
    parser.add_argument('target_path', help='备份解析目录')
    args = parser.parse_args()
    backup_path = args.backup_path
    target_path = args.target_path
    parser = Parser()
    parser.setDB(backup_path)
    parser.setFile(backup_path, target_path)
    parser.copy_all()