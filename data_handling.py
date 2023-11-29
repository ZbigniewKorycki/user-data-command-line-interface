import re
import xmltodict
import xml.etree.ElementTree as ET
from typing import List
import csv
import json
from scripts import logging_setup

logger = logging_setup.setup_logging(__name__)


class TelephoneHandler:
    FORMATTING_PATTERN = r"\s|\+48|\(48\)|^00"

    @classmethod
    def format_number(cls, number: str) -> str:
        return re.sub(cls.FORMATTING_PATTERN, "", number)

    @staticmethod
    def is_phone_present(number) -> bool:
        return False if (number == "") or (number is None) or (number == []) else True


class EmailHandler:
    VALIDATION_PATTERN = r"(^[^@]+@[^@\.]+\.[a-z\d]{1,4}$)"

    @classmethod
    def is_email_valid(cls, email) -> bool:
        try:
            validation = re.match(cls.VALIDATION_PATTERN, email, re.IGNORECASE)
        except TypeError:
            logger.debug("TypeError in email validation")
            return False
        else:
            return True if validation else False


class DataConverter:

    @staticmethod
    def extract_file_extension_from_path(path_to_file: str) -> str:
        return path_to_file.rsplit(".", 1)[1]

    @staticmethod
    def if_user_has_children(user: dict):
        return False if (user["children"] == "") or (user["children"] is None) or (user["children"] == []) else True

    @staticmethod
    def get_children_info_from_csv(user: dict):
        if not DataConverter.if_user_has_children(user):
            return None
        children = [
            child.strip() for child in user["children"].split(",")
        ]
        children_info = [
            {
                "name": child.split("(")[0].strip(),
                "age": int(child.split("(")[1].replace(")", "").strip()),
            }
            for child in children]
        return children_info

    @staticmethod
    def get_children_info_from_xml(user: dict):
        logger.info(f"{user}")
        if not DataConverter.if_user_has_children(user):
            return None
        try:
            children_info = user["children"].get("child")
        except AttributeError:
            return user["children"]
        else:
            return children_info


    @staticmethod
    def get_children_info_from_json(user: dict):
        if not DataConverter.if_user_has_children(user):
            return None
        return user["children"].get("child")


    @staticmethod
    def parse_xml_to_dict(path_to_xml: str) -> dict:
        tree = ET.parse(path_to_xml)
        root = tree.getroot()
        return xmltodict.parse(ET.tostring(root))

    @staticmethod
    def read_csv_file(path_to_csv: str):
        with open(path_to_csv, newline="") as csvfile:
            return csv.DictReader(csvfile, delimiter=";")

    @staticmethod
    def read_json_file(path_to_json: str):
        with open(path_to_json) as file:
            data = json.load(file)
        return data

    @staticmethod
    def format_user_from_xml(user: dict) -> dict:
        if not TelephoneHandler.is_phone_present(user.get("telephone_number")) or not EmailHandler.is_email_valid(
                user.get("email")):
            return None
        user["telephone_number"] = TelephoneHandler.format_number(user["telephone_number"])
        user["children"] = DataConverter.get_children_info_from_xml(user)
        return user

    @staticmethod
    def format_user_from_csv(user: dict) -> dict:
        if not TelephoneHandler.is_phone_present(user.get("telephone_number")) or EmailHandler.is_email_valid(
                user.get("email")):
            return None
        user["telephone_number"] = TelephoneHandler.format_number(user["telephone_number"])
        user["children"] = DataConverter.get_children_info_from_csv(user)
        return user

    @staticmethod
    def format_user_from_json(user: dict) -> dict:
        if not TelephoneHandler.is_phone_present(user.get("telephone_number")) or not EmailHandler.is_email_valid(
                user.get("email")):
            return None
        user["telephone_number"] = TelephoneHandler.format_number(user["telephone_number"])
        user["children"] = DataConverter.get_children_info_from_json(user)
        return user

    @staticmethod
    def filter_valid_users_from_xml(data: List[dict]) -> List[dict]:
        return [DataConverter.format_user_from_xml(user) for user in data if
                DataConverter.format_user_from_xml(user)]

    @staticmethod
    def filter_valid_users_from_csv(data: List[dict]) -> List[dict]:
        return [DataConverter.format_user_from_csv(user) for user in data if
                DataConverter.format_user_from_csv(user)]

    @staticmethod
    def filter_valid_users_from_json(data: List[dict]) -> List[dict]:
        return [DataConverter.format_user_from_json(user) for user in data if
                DataConverter.format_user_from_json(user)]
