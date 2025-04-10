"""Transfer Request test cases"""
import csv
import json
import os.path
import hashlib
from unittest import TestCase
from os import remove
from freezegun import freeze_time
from uc3m_money import (JSON_FILES_PATH,
                        TRANSFERS_STORE_FILE,
                        AccountManager,
                        TransferRequest,
                        AccountManagementException)

class TestTransferRequestTest(TestCase):
    """Class for testing deliver_product"""

    def setUp(self):
        """ inicializo el entorno de prueba """
        if os.path.exists(TRANSFERS_STORE_FILE):
            remove(TRANSFERS_STORE_FILE)


    @staticmethod
    def read_file():
        """ this method read a Json file and return the value """
        my_file= TRANSFERS_STORE_FILE
        try:
            with open(my_file, "r", encoding="utf-8", newline="") as file:
                data = json.load(file)
        except FileNotFoundError as ex:
            raise AccountManagementException("Wrong file or file path") from ex
        except json.JSONDecodeError as ex:
            raise AccountManagementException("JSON Decode Error - Wrong JSON Format") from ex
        return data

    #pylint: disable=too-many-locals
    @freeze_time("2024/12/31 13:00:00")
    def test_parametrized_cases_tests(self):
        """Parametrized cases read from testingCases_RF1.csv"""
        my_cases = JSON_FILES_PATH + "test_cases_2025_method1.csv"
        with open(my_cases, newline='', encoding='utf-8') as csvfile:
            param_test_cases = csv.DictReader(csvfile, delimiter=';')
            mngr = AccountManager()
            for row in param_test_cases:
                test_id = row['ID_TEST']
                iban_from = row["From_iban"]
                #From_iban;to_iban;concept;type;date;amount;RESULT
                iban_to = row["to_iban"]
                transfer_type = row["type"]
                transfer_amount = row["amount"]
                try:
                    number_amount = float(transfer_amount)
                except ValueError:
                    number_amount = row["amount"]
                result = row["RESULT"]
                valid = row["VALID"]
                transfer_date = row["date"]
                transfer_concept = row["concept"]

                if valid == "VALID":
                    with self.subTest(test_id + valid):
                        valor = mngr.transfer_request(from_iban=iban_from,
                                                      to_iban=iban_to,
                                                      transfer_type=transfer_type,
                                                      amount=number_amount,
                                                      date=transfer_date,
                                                      concept=transfer_concept)
                        self.assertEqual(result, valor)
                        # Check if this DNI is store in storeRequest.json
                        my_data = self.read_file()
                        my_request = TransferRequest(from_iban=iban_from,
                                                     to_iban=iban_to,
                                                     transfer_concept=transfer_concept,
                                                     transfer_date=transfer_date,
                                                     transfer_amount=number_amount,
                                                     transfer_type=transfer_type)
                        found = False
                        for k in my_data:
                            if k["transfer_code"] == valor:
                                found = True
                                # this assert give me more information
                                # about the differences than assertEqual
                                self.assertDictEqual(k, my_request.to_json())
                        # if found is False , this assert fails
                        self.assertTrue(found)
                else:
                    with self.subTest(test_id + valid):

                        # we calculater the files signature bejore calling the tested method
                        if os.path.isfile(TRANSFERS_STORE_FILE):
                            with open(TRANSFERS_STORE_FILE, "r",
                                      encoding="utf-8", newline="") as file_org:
                                hash_original = hashlib.md5(str(file_org).encode()).hexdigest()
                        else:
                            hash_original = ""
                        with self.assertRaises(AccountManagementException) as c_m:
                            valor = mngr.transfer_request(from_iban=iban_from,
                                                          to_iban=iban_to,
                                                          transfer_type=transfer_type,
                                                          amount=number_amount,
                                                          date=transfer_date,
                                                          concept=transfer_concept)
                        self.assertEqual(c_m.exception.message, result)

                        # now we check that the signature of the file is the same
                        # (the file didn't change)
                        if os.path.isfile(TRANSFERS_STORE_FILE):
                            with open(TRANSFERS_STORE_FILE, "r",
                                      encoding="utf-8", newline="") as file:
                                hash_new = hashlib.md5(str(file).encode()).hexdigest()
                        else:
                            hash_new = ""
                        self.assertEqual(hash_new, hash_original)

    @freeze_time("2025/03/22 13:00:00")
    def test_duplicated_transfer_test(self):
        """tets methdo for duplicated transfer"""
        iban_from = "ES6211110783482828975098"
        # From_iban;to_iban;concept;type;date;amount;RESULT
        iban_to = "ES8658342044541216872704"
        transfer_type = "ORDINARY"
        transfer_amount = 10.0
        transfer_date = "22/03/2025"
        transfer_concept = "Testing duplicated transfers"
        mngr  = AccountManager()
        mngr.transfer_request(from_iban=iban_from,
                              to_iban=iban_to,
                              transfer_type=transfer_type,
                              amount=transfer_amount,
                              date=transfer_date,
                              concept=transfer_concept)

        if os.path.isfile(TRANSFERS_STORE_FILE):
            with open(TRANSFERS_STORE_FILE, "r", encoding="utf-8", newline="") as file_org:
                hash_original = hashlib.md5(str(file_org).encode()).hexdigest()
        else:
            hash_original = ""
        with self.assertRaises(AccountManagementException) as c_m:
            mngr.transfer_request(from_iban=iban_from,
                                  to_iban=iban_to,
                                  transfer_type=transfer_type,
                                  amount=transfer_amount,
                                  date=transfer_date,
                                  concept=transfer_concept)
        self.assertEqual(c_m.exception.message, "Duplicated transfer in transfer list")

        # now we check that the signature of the file is the same
        # (the file didn't change)
        if os.path.isfile(TRANSFERS_STORE_FILE):
            with open(TRANSFERS_STORE_FILE, "r", encoding="utf-8", newline="") as file:
                hash_new = hashlib.md5(str(file).encode()).hexdigest()
        else:
            hash_new = ""
        self.assertEqual(hash_new, hash_original)

    @freeze_time("2025/03/22 13:00:00")
    def test_transfer_for_today(self):
        """test for a transfer today (using freezetime)"""
        iban_from = "ES6211110783482828975098"
        # From_iban;to_iban;concept;type;date;amount;RESULT
        iban_to = "ES8658342044541216872704"
        transfer_type = "ORDINARY"
        transfer_amount = 10.0
        transfer_date = "22/03/2025"
        transfer_concept = "Testing duplicated transfers"
        mngr  = AccountManager()
        res = mngr.transfer_request(from_iban=iban_from,
                                    to_iban=iban_to,
                                    transfer_type=transfer_type,
                                    amount=transfer_amount,
                                    date=transfer_date,
                                    concept=transfer_concept)
        self.assertEqual("c5477f9dcde7275021eab0bd58bb8175",res)
        my_data = self.read_file()
        my_request = TransferRequest(from_iban=iban_from,
                                     to_iban=iban_to,
                                     transfer_concept=transfer_concept,
                                     transfer_date=transfer_date,
                                     transfer_amount=transfer_amount,
                                     transfer_type=transfer_type)
        found = False
        for k in my_data:
            if k["transfer_code"] == res:
                found = True
                # this assert give me more information
                # about the differences than assertEqual
                self.assertDictEqual(k, my_request.to_json())
        # if found is False , this assert fails
        self.assertTrue(found)

        @freeze_time("2025/03/22 13:00:00")
        def test_transfer_for_tomorrow(self):
            iban_from = "ES6211110783482828975098"
            # From_iban;to_iban;concept;type;date;amount;RESULT
            iban_to = "ES8658342044541216872704"
            transfer_type = "ORDINARY"
            transfer_amount = 10.0
            transfer_date = "23/03/2025"
            transfer_concept = "Testing duplicated transfers"
            mngr = AccountManager()
            res = mngr.transfer_request(from_iban=iban_from,
                                        to_iban=iban_to,
                                        transfer_type=transfer_type,
                                        amount=transfer_amount,
                                        date=transfer_date,
                                        concept=transfer_concept)
            self.assertEqual("b04ac19f692944771fc66c97b1072757", res)
            my_data = self.read_file()
            my_request = TransferRequest(from_iban=iban_from,
                                         to_iban=iban_to,
                                         transfer_concept=transfer_concept,
                                         transfer_date=transfer_date,
                                         transfer_amount=transfer_amount,
                                         transfer_type=transfer_type)
            found = False
            for k in my_data:
                if k["transfer_code"] == res:
                    found = True
                    # this assert give me more information
                    # about the differences than assertEqual
                    self.assertDictEqual(k, my_request.to_json())
            # if found is False , this assert fails
            self.assertTrue(found)

    @freeze_time("2025/03/26 13:00:00")
    def test_transfer_yesterday_test(self):
        """test for a transfer with yesterday date"""
        iban_from = "ES6211110783482828975098"
        # From_iban;to_iban;concept;type;date;amount;RESULT
        iban_to = "ES8658342044541216872704"
        transfer_type = "ORDINARY"
        transfer_amount = 10.0
        transfer_date = "25/03/2025"
        transfer_concept = "Testing yesterday"
        mngr  = AccountManager()
        if os.path.isfile(TRANSFERS_STORE_FILE):
            with open(TRANSFERS_STORE_FILE, "r", encoding="utf-8", newline="") as file_org:
                hash_original = hashlib.md5(str(file_org).encode()).hexdigest()
        else:
            hash_original = ""
        with self.assertRaises(AccountManagementException) as c_m:
            mngr.transfer_request(from_iban=iban_from,
                                  to_iban=iban_to,
                                  transfer_type=transfer_type,
                                  amount=transfer_amount,
                                  date=transfer_date,
                                  concept=transfer_concept)
        self.assertEqual(c_m.exception.message, "Transfer date must be today or later.")

        # now we check that the signature of the file is the same
        # (the file didn't change)
        if os.path.isfile(TRANSFERS_STORE_FILE):
            with open(TRANSFERS_STORE_FILE, "r", encoding="utf-8", newline="") as file:
                hash_new = hashlib.md5(str(file).encode()).hexdigest()
        else:
            hash_new = ""
        self.assertEqual(hash_new, hash_original)
