from os import getenv
from enum import Enum

from requests import get, put, post, exceptions


class CloudAccount:
    def __init__(
        self,
        cloud: str,
        identifier: str,
        bucket: str,
    ):
        cloud_fmt = cloud.lower()
        if cloud_fmt not in ["aws", "azure", "gcp"]:
            raise Exception(f"Unknown cloud {cloud}")

        self.cloud = cloud_fmt
        self.identifier = identifier
        self.bucket = bucket


class ViewOperator(Enum):
    IN = "IN"
    NOT_IN = "NOT_IN"
    NULL = "NULL"
    NOT_NULL = "NOT_NULL"
    LIKE = "LIKE"


class ViewCondition:
    def __init__(
        self,
        fieldId: str,
        fieldName: str,
        identifier: str,
        identifierName: str,
        viewOperator: ViewOperator,
        values: list,
    ):
        self.fieldId = fieldId
        self.fieldName = fieldName
        self.identifier = identifier
        self.identifierName = identifierName
        self.viewOperator = viewOperator
        self.values = values

    def format(self):
        return {
            "type": "VIEW_ID_CONDITION",
            "viewField": {
                "fieldId": self.fieldId,
                "fieldName": self.fieldName,
                "identifier": self.identifier,
                "identifierName": self.identifierName,
            },
            "viewOperator": self.viewOperator.value,
            "values": self.values,
        }


class Bucket:
    def __init__(
        self,
        name: str,
    ):
        self.name = name
        self.rules = []

    def add_rule(self, rule):
        self.rules.append(rule)

    def format(self):
        return {"name": self.name, "rules": self.rules}


class CostCategory:
    def __init__(
        self,
        name: str,
        uuid: str = "",
    ):
        self.name = name

        # if existing cc get its id
        if not uuid:
            if all_cc := [
                x.get("uuid")
                for x in CostCategory.get_all()
                if x.get("name") == self.name
            ]:
                self.uuid = all_cc.pop()
            else:
                self.uuid = None

    def __repr__(self):
        return f"Cost Category: {self.name} ({self.uuid})"

    def payload(self, cost_targets: list = []):
        return {
            "accountId": getenv("HARNESS_ACCOUNT_ID"),
            "name": self.name,
            "uuid": self.uuid,
            "costTargets": cost_targets,
            "unallocatedCost": {
                "strategy": "DISPLAY_NAME",
                "label": "Unattributed",
                "sharingStrategy": None,
                "splits": None,
            },
            "sharedCosts": [],
        }

    def update(self, cost_targets: list = []) -> bool:
        # given a list of cost targets update an existing cost catagory

        if not self.uuid:
            return self.create(cost_targets)
        else:
            resp = put(
                "https://app.harness.io/gateway/ccm/api/business-mapping",
                params={
                    "accountIdentifier": getenv("HARNESS_ACCOUNT_ID"),
                },
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": getenv("HARNESS_PLATFORM_API_KEY"),
                },
                json=self.payload(cost_targets),
            )

            resp.raise_for_status()

            return resp.json()

    def create(self, cost_targets=[]):
        # given a list of cost targets create a cost catagory

        resp = post(
            "https://app.harness.io/gateway/ccm/api/business-mapping",
            params={
                "accountIdentifier": getenv("HARNESS_ACCOUNT_ID"),
            },
            headers={
                "Content-Type": "application/json",
                "x-api-key": getenv("HARNESS_PLATFORM_API_KEY"),
            },
            json=self.payload(cost_targets),
        )

        resp.raise_for_status()

        return resp.json()

    def get_all() -> list:
        # get all the cost catagories in an account

        resp = get(
            "https://app.harness.io/ccm/api/business-mapping",
            params={
                "accountIdentifier": getenv("HARNESS_ACCOUNT_ID"),
            },
            headers={
                "Content-Type": "application/json",
                "x-api-key": getenv("HARNESS_PLATFORM_API_KEY"),
            },
        )

        resp.raise_for_status()

        return resp.json().get("resource", {}).get("businessMappings", [])
