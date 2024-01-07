#I reccomend disabling full path lengths in Windows

#Dependencies: pycryptodome and biplist

import argparse
import getpass
import os
import pprint
import random
import shutil
import sqlite3
import string
import struct
import tempfile
from binascii import hexlify

import Crypto.Cipher.AES # pip install pycryptodome If you have issues refer to https://pycryptodome.readthedocs.io/en/latest/src/faq.html#why-do-i-get-the-error-no-module-named-crypto-on-windows
import biplist #pip install biplist
import hashlib
from .aes_keywrap import aes_unwrap_key
from pathlib import Path

#CLASSES AND FUNCTIONS
CLASSKEY_TAGS = [b"CLAS",b"WRAP",b"WPKY", b"KTYP", b"PBKY"]
KEYBAG_TYPES = ["System", "Backup", "Escrow", "OTA (icloud)"] #Different Keybag structures which exist. Ours is a Backup
KEY_TYPES = ["AES", "Curve25519"]
PROTECTION_CLASSES={
    1:"NSFileProtectionComplete",
    2:"NSFileProtectionCompleteUnlessOpen",
    3:"NSFileProtectionCompleteUntilFirstUserAuthentication",
    4:"NSFileProtectionNone",
    5:"NSFileProtectionRecovery?",
    6: "kSecAttrAccessibleWhenUnlocked",
    7: "kSecAttrAccessibleAfterFirstUnlock",
    8: "kSecAttrAccessibleAlways",
    9: "kSecAttrAccessibleWhenUnlockedThisDeviceOnly",
    10: "kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly",
    11: "kSecAttrAccessibleAlwaysThisDeviceOnly"
}
WRAP_DEVICE = 1
WRAP_PASSCODE = 2

class Keybag(object):
    def __init__(self, data):
        self.type = None
        self.uuid = None
        self.wrap = None
        self.deviceKey = None
        self.attrs = {}
        self.classKeys = {}
        self.KeyBagKeys = None 
        self.parseBinaryBlob(data)

    def parseBinaryBlob(self, data): #This breaks the tags up into a structure.
        currentClassKey = None

        for tag, data in loopTLVBlocks(data):
            if len(data) == 4:
                data = struct.unpack(">L", data)[0]
            if tag == b"TYPE":
                self.type = data
                if self.type > 3:
                    print("FAIL: keybag type > 3 : %d" % self.type)
            elif tag == b"UUID" and self.uuid is None:
                self.uuid = data
            elif tag == b"WRAP" and self.wrap is None:
                self.wrap = data
            elif tag == b"UUID":
                if currentClassKey:
                    self.classKeys[currentClassKey[b"CLAS"]] = currentClassKey
                currentClassKey = {b"UUID": data}
            elif tag in CLASSKEY_TAGS:
                currentClassKey[tag] = data
            else:
                self.attrs[tag] = data
        if currentClassKey:
            self.classKeys[currentClassKey[b"CLAS"]] = currentClassKey

    def unlockWithPasscode(self, passcode):
        passcode1 = hashlib.pbkdf2_hmac('sha256', passcode,
                                        self.attrs[b"DPSL"],
                                        self.attrs[b"DPIC"], 32)
        passcode_key = hashlib.pbkdf2_hmac('sha1', passcode1,
                                            self.attrs[b"SALT"],
                                            self.attrs[b"ITER"], 32)
        print('== Passcode key')
        print(hexlify(passcode_key).decode("utf-8")) 

        for classkey in self.classKeys.values():
            k = classkey[b"WPKY"]
            if classkey[b"WRAP"] & WRAP_PASSCODE:
                k = aes_unwrap_key(passcode_key, classkey[b"WPKY"])
                if not k:
                    return False
                classkey[b"KEY"] = k
        return True

    def unwrapKeyForClass(self, protection_class, persistent_key):
        ck = self.classKeys[protection_class][b"KEY"]
        if len(persistent_key) != 0x28:
            raise Exception("Invalid key length")
        return aes_unwrap_key(ck, persistent_key) 
        

def loopTLVBlocks(blob):
    i = 0
    while i + 8 <= len(blob):
        tag = blob[i:i+4]
        length = struct.unpack(">L",blob[i+4:i+8])[0]
        data = blob[i+8:i+8+length]
        yield (tag,data)
        i += 8 + length

def removePadding(data, blocksize=16):
    n = int(data[-1])  # RFC 1423: last byte contains number of padding bytes.
    if n > blocksize or n > len(data):
        raise Exception('Invalid CBC padding')
    return data[:-n]

ZEROIV = b"\x00"*16
def AESdecryptCBC(data, key, iv=ZEROIV, padding=False): 
    if len(data) % 16:
        print("AESdecryptCBC: data length not /16, truncating")
        data = data[0:(len(data)/16) * 16]
    data = Crypto.Cipher.AES.new(key, Crypto.Cipher.AES.MODE_CBC, iv).decrypt(data)
    if padding:
        return removePadding(16, data)
    return data

def decrypt_manifest_db(keybag,password,manifest_key,db_path):
    """
    @keybag:        Manifest.plist中的Keybag
    @password:      iTunes备份密码
    @manifest_key:  数据库wrapKey
    @db_path:       数据库路径
    @return:        解密后的数据库
    """
    keybag1 = Keybag(keybag)

    ## Unlock keybag with password
    passwordcorrect = False
    keybag1.unlockWithPasscode(password.encode('utf8'))

    #Decrypt manifest.db
    manifestKey = manifest_key[4:] #The key is everything after the first 4 bytes
    db = open(db_path, 'rb') #Opens Manifest.db as readable binary object
    encrypted_db = db.read()
    manifest_class = struct.unpack('<l', manifest_key[:4])[0] #Gets manifest protection class
    key = keybag1.unwrapKeyForClass(manifest_class, manifestKey) #Unwrapped key to the manifest.db
    decrypted_data = AESdecryptCBC(encrypted_db, key) #Decrypts the manifest.db
    if decrypted_data[:6] == b'SQLite':
        return decrypted_data
    return b''

def decrypt_file(keybag,bplist,data):
    """
    @keybag:        Manifest.plist中的Keybag
    @password:      iTunes备份密码
    @bplist:        数据库中对应文件的plist数据
    @data:          需要解密的文件数据
    @return:        解密后的文件数据
    """
    plist = biplist.readPlistFromString(bplist)
    file_data = plist['$objects'][plist['$top']['root'].integer]
    size = file_data['Size']
    protection_class = file_data['ProtectionClass']
    encryption_key = plist['$objects'][file_data['EncryptionKey'].integer]['NS.data'][4:]
    key = keybag.unwrapKeyForClass(protection_class, encryption_key)
    decrypted_data = AESdecryptCBC(data, key)[:size]
    return decrypted_data


# #Command Line Arguments
# parser = argparse.ArgumentParser(description='Decrypt iPhone backups')
# parser.add_argument('InputPath', type=str, help='Path to the Manifest.plist file')
# parser.add_argument('OutputPath', type=str, help='Path to save the decrypted backup')
# parser.add_argument('Password', type=str, help='Password for the iPhone backup (not neccessarily the iPhone password)')
# args = parser.parse_args()
# manifest_file = args.InputPath
# output_path = args.OutputPath
# passcode = args.Password

# #Validate backup location input
# validated = False
# while validated == False:
#     if os.path.exists(manifest_file):
#         validated = True
#     else:
#         print("That isn't a valid path. Please try again")
#         validated = False
#         manifest_file = input("Please enter the path to the manifest file: ")
# if "Manifest.plist" in manifest_file:
# 	pass
# else:
#     manifest_file = manifest_file + "\Manifest.plist"
#     if os.path.exists(manifest_file):
#         pass
#     else:
#         manifest_file = manifest_file + "Manifest.plist"
# backup_path = manifest_file[:-14]
# manifest_db = backup_path + "Manifest.db"

# #Validate output path input
# validated = False
# while validated == False:
#     if os.path.exists(output_path):
#         validated = True
#     else:
#         creation = input("This directory does not exist. Would you like to create it? (Y/N): ")
#         if creation == "Y":
#             os.makedirs(output_path)
#             validated = True
#         else:
#             print("Okay, let's try again")
#             validated = False
#             output_path = input("Please enter the location you want to save the backup: ")

# #Encode password input
# password = passcode.encode('utf-8')

#Open the manifest.plist and dump keybag
# infile = open(manifest_file, 'rb')
# manifest_plist = biplist.readPlist(infile)
# keybag = Keybag(manifest_plist['BackupKeyBag'])

# ## Unlock keybag with password
# passwordcorrect = False
# keybag.unlockWithPasscode(password)

# #Decrypt manifest.db
# manifest_key = manifest_plist['ManifestKey'][4:] #The key is everything after the first 4 bytes
# db = open(manifest_db, 'rb') #Opens Manifest.db as readable binary object
# encrypted_db = db.read()
# manifest_class = struct.unpack('<l', manifest_plist['ManifestKey'][:4])[0] #Gets manifest protection class
# key = keybag.unwrapKeyForClass(manifest_class, manifest_key) #Unwrapped key to the manifest.db
# decrypted_data = AESdecryptCBC(encrypted_db, key) #Decrypts the manifest.db

# #This will write out the manifest.db
# db_filename = output_path + "\db.sqlite3"
# db_file = open(db_filename, 'wb')
# db_file.write(decrypted_data)
# db_file.close()
# conn = sqlite3.connect(db_filename)
# c = conn.cursor()
# c.execute("""
#     SELECT fileID, domain, relativePath, file
# 	FROM Files
# 	WHERE flags=1
# 	ORDER BY domain, relativePath""")
# results = c.fetchall()
# for item in results:
#     fileID, domain, relativePath, file_bplist = item
#     if ':' in relativePath: #APFS allows colons in filenames but NTFS does not, so this replaces the colon with !-.
#         relativePath = relativePath.replace(':','!-')
#     plist = biplist.readPlistFromString(file_bplist)
#     file_data = plist['$objects'][plist['$top']['root'].integer]
#     size = file_data['Size']
#     protection_class = file_data['ProtectionClass']
#     encryption_key = plist['$objects'][file_data['EncryptionKey'].integer]['NS.data'][4:]
#     backup_filename = os.path.join(backup_path, fileID[:2], fileID)
#     infile = open(backup_filename, 'rb')
#     data = infile.read()
#     key = keybag.unwrapKeyForClass(protection_class, encryption_key)
#     decrypted_data = AESdecryptCBC(data, key)[:size]
#     output_filename = os.path.join(output_path, "Decrypted", relativePath)
#     if not os.path.exists(os.path.dirname(output_filename)):
#         try:
#             os.makedirs(os.path.dirname(output_filename))
#         except OSError as exc:
#             if exc.errno != errno.EEXIST:
#                 raise
#     outfile = open(output_filename, 'wb')
#     outfile.write(decrypted_data)
#     outfile.close()
#     infile.close()
