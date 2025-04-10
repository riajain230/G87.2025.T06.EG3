"""Account manager module """
import re
import json
from datetime import datetime, timezone
from uc3m_money.account_management_exception import AccountManagementException
from uc3m_money.account_management_config import (TRANSFERS_STORE_FILE,
                                        DEPOSITS_STORE_FILE,
                                        TRANSACTIONS_STORE_FILE,
                                        BALANCES_STORE_FILE)

from uc3m_money.transfer_request import TransferRequest
from uc3m_money.account_deposit import AccountDeposit


def validate_concept(concept: str):
    """regular expression for checking the minimum and maximum length as well as
    the allowed characters and spaces restrictions
    there are other ways to check this"""
    concept_pattern = re.compile(r"^(?=^.{10,30}$)([a-zA-Z]+(\s[a-zA-Z]+)+)$")

    res = concept_pattern.fullmatch(concept)
    if not res:
        raise AccountManagementException ("Invalid concept format")


def read_transactions_file():
    """loads the content of the transactions file
    and returns a list"""
    try:
        with open(TRANSACTIONS_STORE_FILE, "r", encoding="utf-8", newline="") as file:
            input_list = json.load(file)
    except FileNotFoundError as ex:
        raise AccountManagementException("Wrong file  or file path") from ex
    except json.JSONDecodeError as ex:
        raise AccountManagementException("JSON Decode Error - Wrong JSON Format") from ex
    return input_list


def validate_transfer_date(transfer_date):
    """validates the arrival date format  using regex"""
    date_pattern = re.compile(r"^(([0-2]\d|3[0-1])\/(0\d|1[0-2])\/\d\d\d\d)$")
    result = date_pattern.fullmatch(transfer_date)
    if not result:
        raise AccountManagementException("Invalid date format")

    try:
        my_date = datetime.strptime(transfer_date, "%d/%m/%Y").date()
    except ValueError as ex:

        raise AccountManagementException("Invalid date format") from ex

    if my_date < datetime.now(timezone.utc).date():
        raise AccountManagementException("Transfer date must be today or later.")

    if my_date.year < 2025 or my_date.year > 2050:
        raise AccountManagementException("Invalid date format")
    return transfer_date

def read_json_file(file_path):
    """ This functions reads to a JSON file and gives and error if file is not found
    or it's not in json format"""
    try:
        with open(file_path, "r", encoding="utf-8", newline="") as file:
            return json.load(file)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError as ex:
        raise AccountManagementException("JSON Decode Error - Wrong JSON Format") from ex

def write_json_file(file_path, data):
    """This functions writes to a JSON file and if raises error if the file pathis wrong or
    not in JSON format"""
    try:
        with open(file_path, "w", encoding="utf-8", newline="") as file:
            json.dump(data, file, indent=2)
    except FileNotFoundError as ex:
        raise AccountManagementException("Wrong file  or file path") from ex
    except json.JSONDecodeError as ex:
        raise AccountManagementException("JSON Decode Error - Wrong JSON Format") from ex


class AccountManager:
    """Class for providing the methods for managing the orders"""
    def __init__(self):
        pass

    @staticmethod
    def validate_iban(input_iban: str):
        """
    Calcula el dígito de control de un IBAN español.

    Args:
        input_iban (str): El IBAN sin los dos últimos dígitos (dígito de control).

    Returns:
        str: El dígito de control calculado.
        """
        iban_pattern = re.compile(r"^ES[0-9]{22}")
        iban_match = iban_pattern.fullmatch(input_iban)
        if not iban_match:
            raise AccountManagementException("Invalid IBAN format")
        iban = input_iban
        original_code = iban[2:4]
        #replacing the control
        iban = iban[:2] + "00" + iban[4:]
        iban = iban[4:] + iban[:4]


        # Convertir el IBAN en una cadena numérica, reemplazando letras por números
        iban = (iban.replace('A', '10').replace('B', '11').
                replace('C', '12').replace('D', '13').replace('E', '14').
                replace('F', '15'))
        iban = (iban.replace('G', '16').replace('H', '17').
                replace('I', '18').replace('J', '19').replace('K', '20').
                replace('L', '21'))
        iban = (iban.replace('M', '22').replace('N', '23').
                replace('O', '24').replace('P', '25').replace('Q', '26').
                replace('R', '27'))
        iban = (iban.replace('S', '28').replace('T', '29').replace('U', '30').
                replace('V', '31').replace('W', '32').replace('X', '33'))
        iban = iban.replace('Y', '34').replace('Z', '35')

        # Mover los cuatro primeros caracteres al final

        # Convertir la cadena en un número entero
        int_iban = int(iban)

        # Calcular el módulo 97
        modulo = int_iban % 97

        # Calcular el dígito de control (97 menos el módulo)
        checked_digits = 98 - modulo

        if int(original_code) != checked_digits:
            #print(checked_digits)
            raise AccountManagementException("Invalid IBAN control digit")

        return input_iban

    #pylint: disable=too-many-arguments
    def transfer_request(self, from_iban: str,
                         to_iban: str,
                         concept: str,
                         transfer_type: str,
                         date: str,
                         amount: float)->str:
        """first method: receives transfer info and
        stores it into a file"""
        self.validate_iban(from_iban)
        self.validate_iban(to_iban)
        validate_concept(concept)
        transfer_type_pattern = re.compile(r"(ORDINARY|INMEDIATE|URGENT)")
        result = transfer_type_pattern.fullmatch(transfer_type)
        if not result:
            raise AccountManagementException("Invalid transfer type")
        validate_transfer_date(date)

        try:
            float_amount  = float(amount)
        except ValueError as exc:
            raise AccountManagementException("Invalid transfer amount") from exc

        n_str = str(float_amount)
        if '.' in n_str:
            decimals = len(n_str.split('.')[1])
            if decimals > 2:
                raise AccountManagementException("Invalid transfer amount")

        if float_amount < 10 or float_amount > 10000:
            raise AccountManagementException("Invalid transfer amount")

        my_request = TransferRequest(from_iban=from_iban,
                                     to_iban=to_iban,
                                     transfer_concept=concept,
                                     transfer_type=transfer_type,
                                     transfer_date=date,
                                     transfer_amount=amount)

        transfer_list = read_json_file(TRANSFERS_STORE_FILE)

        for transfer_index in transfer_list:
            if (transfer_index["from_iban"] == my_request.from_iban and
                    transfer_index["to_iban"] == my_request.to_iban and
                    transfer_index["transfer_date"] == my_request.transfer_date and
                    transfer_index["transfer_amount"] == my_request.transfer_amount and
                    transfer_index["transfer_concept"] == my_request.transfer_concept and
                    transfer_index["transfer_type"] == my_request.transfer_type):
                raise AccountManagementException("Duplicated transfer in transfer list")

        transfer_list.append(my_request.to_json())

        write_json_file(TRANSFERS_STORE_FILE, transfer_list)

        return my_request.transfer_code

    def deposit_into_account(self, input_file:str)->str:
        """manages the deposits received for accounts"""
        try:
            with open(input_file, "r", encoding="utf-8", newline="") as file:
                input_data = json.load(file)
        except FileNotFoundError as ex:
            raise AccountManagementException("Error: file input not found") from ex
        except json.JSONDecodeError as ex:
            raise AccountManagementException("JSON Decode Error - Wrong JSON Format") from ex

        # comprobar valores del fichero
        try:
            deposit_iban = input_data["IBAN"]
            deposit_amount = input_data["AMOUNT"]
        except KeyError as e:
            raise AccountManagementException("Error - Invalid Key in JSON") from e


        deposit_iban = self.validate_iban(deposit_iban)
        amount_pattern = re.compile(r"^EUR [0-9]{4}\.[0-9]{2}")
        result = amount_pattern.fullmatch(deposit_amount)
        if not result:
            raise AccountManagementException("Error - Invalid deposit amount")

        deposit_amount_float = float(deposit_amount[4:])
        if deposit_amount_float == 0:
            raise AccountManagementException("Error - Deposit must be greater than 0")

        deposit_obj = AccountDeposit(to_iban=deposit_iban, deposit_amount=deposit_amount_float)

        ## using new functions
        deposit_log = read_json_file(DEPOSITS_STORE_FILE)
        deposit_log.append(deposit_obj.to_json())
        write_json_file(DEPOSITS_STORE_FILE, deposit_log)

        return deposit_obj.deposit_signature

    def calculate_balance(self, iban:str):
        """ Calculates the balance for a given iban from the transcations sheet"""
        iban = self.validate_iban(iban)
        loaded_transactions = read_transactions_file()
        iban_found = False
        total_balance = 0
        for transaction in loaded_transactions:
            #print(transaction["IBAN"] + " - " + iban)
            if transaction["IBAN"] == iban:
                total_balance += float(transaction["amount"])
                iban_found = True
        if not iban_found:
            raise AccountManagementException("IBAN not found")

        last_balance = {"IBAN": iban,
                        "time": datetime.timestamp(datetime.now(timezone.utc)),
                        "BALANCE": total_balance}
        ## using the new functions
        balance_list = read_json_file(BALANCES_STORE_FILE)
        balance_list.append(last_balance)
        write_json_file(BALANCES_STORE_FILE, balance_list)
        return True
