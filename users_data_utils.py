import re
import xmltodict
import xml.etree.ElementTree as ET
from typing import List, Optional, Union
import csv
import json
import pandas as pd


class UsersDataExtractor:
    def __init__(self, path_to_file):
        self.path_to_file = path_to_file
        self.file_extension = self.extract_file_extension()

    def extract_file_extension(self) -> Optional[str]:
        try:
            file_extension = self.path_to_file.rsplit(".", 1)[1]
        except IndexError:
            print(f"File extension not recognized in: {self.path_to_file}")
            return None
        else:
            return file_extension

    def extract_data(self) -> Optional[List[dict]]:
        if self.file_extension.lower() == "xml":
            return self.parse_xml()
        elif self.file_extension.lower() == "csv":
            return self.read_csv()
        elif self.file_extension.lower() == "json":
            return self.read_json()
        else:
            print(f"Given file extension ({self.file_extension}) is not supported.")
            return None

    def parse_xml(self) -> List[dict]:
        tree = ET.parse(self.path_to_file)
        root = tree.getroot()
        return xmltodict.parse(ET.tostring(root))["users"]["user"]

    def read_json(self) -> List[dict]:
        with open(self.path_to_file) as file:
            data = json.load(file)
        return data

    def read_csv(self) -> List[dict]:
        with open(self.path_to_file, newline="") as csvfile:
            reader = csv.DictReader(csvfile, delimiter=";")
            data = list(reader)
        return data


class UsersDataFormatter:
    TELEPHONE_FORMATTING_PATTERN = r"\s|\+48|\(48\)|^00"
    EMAIL_VALIDATION_PATTERN = r"(^[^@]+@[^@\.]+\.[a-z\d]{1,4}$)"

    @staticmethod
    def filter_valid_data(data: Optional[List[dict]]) -> Optional[List[dict]]:
        return [user for user in data if user is not None]

    @classmethod
    def format_telephone_number(cls, number: str) -> str:
        return re.sub(cls.TELEPHONE_FORMATTING_PATTERN, "", number)

    @staticmethod
    def is_data_present_in_user(key: str, user: dict) -> bool:
        return True if key in user and user[key] not in ["", None, []] else False

    @classmethod
    def is_email_address_valid(cls, email: Union[str, dict]) -> bool:
        try:
            validation = re.match(cls.EMAIL_VALIDATION_PATTERN, email, re.IGNORECASE)
        except TypeError:
            return False
        else:
            return True if validation else False

    @classmethod
    def get_info_on_user_children(cls, user: dict) -> Optional[List[dict]]:
        if not cls.is_data_present_in_user("children", user):
            return None
        children_data = user.get("children")
        # Check if children from users data type xml
        if isinstance(children_data, dict):
            if isinstance(children_data.get("child"), dict):
                return [children_data["child"]]
            elif isinstance(children_data.get("child"), list):
                return [child for child in children_data["child"]]
            else:
                return None
        # Check if children from users data type json
        elif isinstance(children_data, list):
            return list(children_data)
        # Else children from users data type csv
        children = [child.strip() for child in children_data.split(",")]
        return [
            {
                "name": child.split("(")[0].strip(),
                "age": child.split("(")[1].replace(")", "").strip(),
            }
            for child in children]

    @staticmethod
    def convert_children_age_to_int(children_data: List[dict]) -> Optional[List[dict]]:
        if children_data is not None:
            for child in children_data:
                try:
                    child["age"] = int(child["age"])
                except (ValueError, KeyError):
                    pass
        return children_data

    @classmethod
    def format_user_data(cls, user: dict) -> Optional[dict]:
        if not cls.is_data_present_in_user(
                "telephone_number", user
        ) or not cls.is_email_address_valid(user.get("email")):
            return None
        user["telephone_number"] = cls.format_telephone_number(user["telephone_number"])
        user["children"] = cls.get_info_on_user_children(user)
        user["children"] = cls.convert_children_age_to_int(user["children"])
        return user

    @classmethod
    def process_data(cls, data: List[dict]) -> Optional[List[dict]]:
        try:
            formatted_data = [cls.format_user_data(user) for user in data]
            validated_data = cls.filter_valid_data(formatted_data)
        except Exception as e:
            print(f"Encounter error processing data: {e}")
            return None
        return validated_data


class UsersDataProcessor:
    def __init__(self, path_to_file: str):
        self.data_extractor = UsersDataExtractor(path_to_file)
        self.data_formatter = UsersDataFormatter()

    def process_users_data(self) -> Optional[List[dict]]:
        try:
            data = self.data_extractor.extract_data()
        except TypeError:
            print(
                f"Encounter error extracting data from path:{self.data_extractor.path_to_file}, check if file is correct.")
            return None
        else:
            try:
                formatted_data = self.data_formatter.process_data(data)
            except TypeError:
                print(
                    f"Encounter error processing data from path: {self.data_extractor.path_to_file}, check if file is correct.")
                return None
            else:
                return formatted_data


class UsersDataMerger:

    def __init__(self, files_paths: List[str]):
        self.files_paths = files_paths
        self.df_merged_users_data = None

    def files_exist(self) -> bool:
        return bool(self.files_paths)

    def merge_users_data(self) -> List[dict]:
        merged_data = []
        for file_path in self.files_paths:
            try:
                users_data = UsersDataProcessor(file_path)
                processed_data = users_data.process_users_data()
                if processed_data:
                    merged_data.extend(processed_data)
            except Exception as e:
                print(f"Encounter error processing file {file_path}: {e}")
        return merged_data

    def create_dataframe_from_merged_data(self):
        return pd.DataFrame(self.merge_users_data())

    def process_merged_users_data(self):
        try:
            if self.files_exist():
                self.df_merged_users_data = self.create_dataframe_from_merged_data()
                if not self.df_merged_users_data.empty:
                    self.df_merged_users_data = self.df_merged_users_data.sort_values(by="created_at", ascending=False)
                    self.df_merged_users_data.drop_duplicates(subset=["telephone_number"], keep='first', inplace=True)
                    self.df_merged_users_data.drop_duplicates(subset=["email"], keep='first', inplace=True)
        except Exception as e:
            print(f"Error processing merged data: {e}")
