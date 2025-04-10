"""Tests for calculate balance"""
#pylint: disable=broad-exception-caught
import datetime
from unittest import TestCase
import os.path
from os import remove
import json
import hashlib
from freezegun import freeze_time
from uc3m_money import (BALANCES_STORE_FILE,
                        AccountManager,
                        TRANSACTIONS_STORE_FILE,
                        AccountManagementException,
                        JSON_FILES_PATH)

NOMBRE_FICHERO_TEMPORAL = JSON_FILES_PATH + "swap.json"
EMPTY_TRANSACTIONS_FILE = JSON_FILES_PATH + "transactions_empty_test.json"
NO_JSON_TRANSACTIONS_FILE = JSON_FILES_PATH + "transactions_no_json_test.json"

class TestCalculateBalance(TestCase):
    """Calculate balance tests class"""
    def setUp(self):
        """ inicializo el entorno de prueba """
        if os.path.exists(BALANCES_STORE_FILE):
            remove(BALANCES_STORE_FILE)

    @staticmethod
    def read_file():
        """ this method read a Json file and return the value """
        try:
            with open(BALANCES_STORE_FILE, "r", encoding="utf-8", newline="") as file:
                data = json.load(file)
        except FileNotFoundError as ex:
            raise AccountManagementException("Wrong file or file path") from ex
        except json.JSONDecodeError as ex:
            raise AccountManagementException("JSON Decode Error - Wrong JSON Format") from ex
        return data

    @freeze_time("2025/03/26 14:00:00")
    def test_calculate_balance_1 (self):
        """path 1: all ok - entering the loop"""
        mngr = AccountManager()
        res = mngr.calculate_balance(iban="ES3559005439021242088295")
        self.assertTrue(res)
        data = self.read_file()
        data_found = False
        for balance in data:
            if (balance["IBAN"] == "ES3559005439021242088295" and
                    balance["time"] == datetime.datetime.now(datetime.timezone.utc).timestamp() and
                    balance["BALANCE"]==9268.29):
                data_found = True

        self.assertTrue(data_found)

    def test_file_wrong_iban_number(self):
        """path with wrong iban number (exception)"""
        mngr = AccountManager()

        if os.path.isfile(BALANCES_STORE_FILE):
            with open(BALANCES_STORE_FILE, "r", encoding="utf-8", newline="") as file_org:
                hash_original = hashlib.md5(str(file_org).encode()).hexdigest()
        else:
            hash_original = ""

        with self.assertRaises(AccountManagementException) as cm_obj:
            mngr.calculate_balance("ES1559005439021242088295")
        self.assertEqual("Invalid IBAN control digit",cm_obj.exception.message)

        if os.path.isfile(BALANCES_STORE_FILE):
            with open(BALANCES_STORE_FILE, "r", encoding="utf-8", newline="") as file:
                hash_new = hashlib.md5(str(file).encode()).hexdigest()
        else:
            hash_new = ""
        self.assertEqual(hash_new, hash_original)

    def test_file_not_found(self):
        """path with transactions file not found"""
        # rename the manipulated order's store
        self.rename_file(TRANSACTIONS_STORE_FILE,NOMBRE_FICHERO_TEMPORAL )
        mngr = AccountManager()
        res = False
        msg = ""
        if os.path.isfile(BALANCES_STORE_FILE):
            with open(BALANCES_STORE_FILE, "r", encoding="utf-8", newline="") as file_org:
                hash_original = hashlib.md5(str(file_org).encode()).hexdigest()
        else:
            hash_original = ""

        try:
            mngr.calculate_balance(iban="ES3559005439021242088295")
        except AccountManagementException as ex:
            if ex.message == "Wrong file  or file path":
                res = True
            else:
                msg = ex.message
        except Exception as  ex:
            msg = str(ex)

        self.rename_file(NOMBRE_FICHERO_TEMPORAL,TRANSACTIONS_STORE_FILE)
        self.assertEqual(True,res,msg)

        if os.path.isfile(BALANCES_STORE_FILE):
            with open(BALANCES_STORE_FILE, "r", encoding="utf-8", newline="") as file:
                hash_new = hashlib.md5(str(file).encode()).hexdigest()
        else:
            hash_new = ""
        self.assertEqual(hash_new, hash_original)

    def test_file_not_json(self):
        """path with transactions file without json format"""
        # rename the transactions file and setting a new empty transactions file
        self.rename_file(TRANSACTIONS_STORE_FILE,NOMBRE_FICHERO_TEMPORAL )
        self.rename_file(NO_JSON_TRANSACTIONS_FILE, TRANSACTIONS_STORE_FILE)
        mngr = AccountManager()
        res = False
        msg = ""
        if os.path.isfile(BALANCES_STORE_FILE):
            with open(BALANCES_STORE_FILE, "r", encoding="utf-8", newline="") as file_org:
                hash_original = hashlib.md5(str(file_org).encode()).hexdigest()
        else:
            hash_original = ""
        try:
            mngr.calculate_balance(iban="ES3559005439021242088295")
        except AccountManagementException as ex:
            if ex.message == "JSON Decode Error - Wrong JSON Format":
                res = True
            else:
                msg = ex.message
        except Exception as  ex:
            msg = str(ex)

        #renaming the files to the orignal state
        self.rename_file(TRANSACTIONS_STORE_FILE, NO_JSON_TRANSACTIONS_FILE)
        self.rename_file(NOMBRE_FICHERO_TEMPORAL,TRANSACTIONS_STORE_FILE)
        self.assertEqual(True,res,msg)
        if os.path.isfile(BALANCES_STORE_FILE):
            with open(BALANCES_STORE_FILE, "r", encoding="utf-8", newline="") as file:
                hash_new = hashlib.md5(str(file).encode()).hexdigest()
        else:
            hash_new = ""
        self.assertEqual(hash_new, hash_original)

    def test_file_skip_loop(self):
        """path skipping the loop (empty transactions file)"""
        mngr = AccountManager()

        if os.path.isfile(BALANCES_STORE_FILE):
            with open(BALANCES_STORE_FILE, "r", encoding="utf-8", newline="") as file_org:
                hash_original = hashlib.md5(str(file_org).encode()).hexdigest()
        else:
            hash_original = ""
        self.rename_file(TRANSACTIONS_STORE_FILE,NOMBRE_FICHERO_TEMPORAL )
        self.rename_file(EMPTY_TRANSACTIONS_FILE, TRANSACTIONS_STORE_FILE)
        msg = ""
        res = False
        try:
            mngr.calculate_balance(iban="ES3559005439021242088295")
        except AccountManagementException as ex:
            if ex.message == "IBAN not found":
                res = True
            else:
                msg = ex.message
        except Exception as ex:
            msg = str(ex)

        self.rename_file(TRANSACTIONS_STORE_FILE, EMPTY_TRANSACTIONS_FILE)
        self.rename_file(NOMBRE_FICHERO_TEMPORAL, TRANSACTIONS_STORE_FILE)
        self.assertEqual(True, res, msg)

        if os.path.isfile(BALANCES_STORE_FILE):
            with open(BALANCES_STORE_FILE, "r", encoding="utf-8", newline="") as file:
                hash_new = hashlib.md5(str(file).encode()).hexdigest()
        else:
            hash_new = ""
        self.assertEqual(hash_new, hash_original)

    def test_file_iban_not_found(self):
        """path for an IBAN not in the file"""
        mngr = AccountManager()

        if os.path.isfile(BALANCES_STORE_FILE):
            with open(BALANCES_STORE_FILE, "r", encoding="utf-8", newline="") as file_org:
                hash_original = hashlib.md5(str(file_org).encode()).hexdigest()
        else:
            hash_original = ""

        with self.assertRaises(AccountManagementException) as cm_obj:
            mngr.calculate_balance("ES9420805801101234567891")
        self.assertEqual("IBAN not found", cm_obj.exception.message)

        if os.path.isfile(BALANCES_STORE_FILE):
            with open(BALANCES_STORE_FILE, "r", encoding="utf-8", newline="") as file:
                hash_new = hashlib.md5(str(file).encode()).hexdigest()
        else:
            hash_new = ""
        self.assertEqual(hash_new, hash_original)

    def test_balance_file_not_json(self):
        """path with transactions file not in json format"""
        # rename the transactions file and setting a new empty transactions file
        self.rename_file(BALANCES_STORE_FILE,NOMBRE_FICHERO_TEMPORAL )
        self.rename_file(NO_JSON_TRANSACTIONS_FILE, BALANCES_STORE_FILE)
        mngr = AccountManager()
        res = False
        msg = ""
        if os.path.isfile(BALANCES_STORE_FILE):
            with open(BALANCES_STORE_FILE, "r", encoding="utf-8", newline="") as file_org:
                hash_original = hashlib.md5(str(file_org).encode()).hexdigest()
        else:
            hash_original = ""
        try:
            mngr.calculate_balance(iban="ES3559005439021242088295")
        except AccountManagementException as ex:
            if ex.message == "JSON Decode Error - Wrong JSON Format":
                res = True
            else:
                msg = ex.message
        except Exception as  ex:
            msg = str(ex)

        if os.path.isfile(BALANCES_STORE_FILE):
            with open(BALANCES_STORE_FILE, "r", encoding="utf-8", newline="") as file:
                hash_new = hashlib.md5(str(file).encode()).hexdigest()
        else:
            hash_new = ""
        #renaming the files to the orignal state
        self.rename_file(BALANCES_STORE_FILE, NO_JSON_TRANSACTIONS_FILE)
        self.rename_file(NOMBRE_FICHERO_TEMPORAL,BALANCES_STORE_FILE)
        self.assertEqual(True,res,msg)

        self.assertEqual(hash_new, hash_original)


    def rename_file(self, old_name, new_name):
        """renames a file (if it exists)"""
        if os.path.isfile(old_name):
            os.rename(old_name, new_name)
