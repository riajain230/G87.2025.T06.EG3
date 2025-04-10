"""Deposit into account test cases """
import csv
import json
import os.path
import hashlib
from unittest import TestCase
from os import remove
from freezegun import freeze_time
from uc3m_money import (JSON_FILES_PATH,
                        DEPOSITS_STORE_FILE,
                        AccountManager,
                        JSON_FILES_DEPOSITS,
                        AccountManagementException)

class TestDepositIntoAccountTests(TestCase):
    """Test class for deposit method"""
    def setUp(self):
        """ inicializo el entorno de prueba """
        if os.path.exists(DEPOSITS_STORE_FILE):
            remove(DEPOSITS_STORE_FILE)

    @staticmethod
    def read_file():
        """ this method read a Json file and return the value """
        try:
            with open(DEPOSITS_STORE_FILE, "r", encoding="utf-8", newline="") as file:
                data = json.load(file)
        except FileNotFoundError as ex:
            raise AccountManagementException("Wrong file or file path") from ex
        except json.JSONDecodeError as ex:
            raise AccountManagementException("JSON Decode Error - Wrong JSON Format") from ex
        return data

    @freeze_time("2025/03/26 14:00:00")
    #pylint: disable=too-many-locals
    def test_parametrized_cases(self):
        """Parametrized cases read from testingCases_RF2.csv
        time is set to 01/07/2024 since it is the chosen for the valid case"""
        my_cases = JSON_FILES_PATH + "test_cases_2025_method2.csv"
        with open(my_cases, newline='', encoding='utf-8') as csvfile:
            param_test_cases = csv.DictReader(csvfile, delimiter=',')
            mngr = AccountManager()
            for row in param_test_cases:
                # VALID INVALID;ID TEST;FILE;EXPECTED RESULT
                test_id = row['ID_TEST']
                valid = row["VALID_INVALID"]
                result = row["RESULT"]
                test_file = JSON_FILES_DEPOSITS + row["FILE"]
                if valid == "VALID":
                    with self.subTest(test_id + valid):
                        # removes all the deposits to be sure that the method works
                        self.setUp()
                        valor = mngr.deposit_into_account(test_file)
                        self.assertEqual(result, valor)
                        # Check if this deposit has been stored

                        my_data = self.read_file()
                        found = False
                        for k in my_data:
                            if k["deposit_signature"] == valor:
                                found = True
                        # if found is False , this assert fails
                        self.assertTrue(found)
                else:
                    with self.subTest(test_id + valid):
                        # read the file to compare file content before and after method call
                        if os.path.isfile(DEPOSITS_STORE_FILE):
                            with open(DEPOSITS_STORE_FILE, "r",
                                      encoding="utf-8", newline="") as file_org:
                                hash_original = hashlib.md5(str(file_org).encode()).hexdigest()
                        else:
                            hash_original = ""

                        with self.assertRaises(AccountManagementException) as c_m:
                            valor = mngr.deposit_into_account(test_file)
                        self.assertEqual(c_m.exception.message, result)
                        if os.path.isfile(DEPOSITS_STORE_FILE):
                            with open(DEPOSITS_STORE_FILE, "r",
                                      encoding="utf-8", newline="") as file:
                                hash_new = hashlib.md5(str(file).encode()).hexdigest()
                        else:
                            hash_new = ""
                        self.assertEqual(hash_new, hash_original)
