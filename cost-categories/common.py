from os import getenv

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


class CostCategory:
    def __init__(
        self,
        name: str,
        uuid: str = "",
    ):
        self.name = name

        if not uuid:
            if all_cc := [
                x.get("uuid")
                for x in CostCategory.get_all_cost_categories()
                if x.get("name") == self.name
            ]:
                self.uuid = all_cc.pop()
            else:
                self.uuid = None

    def __repr__(self):
        return f"Cost Category: {self.name} ({self.uuid})"

    def update_cost_category(self, cost_targets=[]) -> bool:
        # given a list of cost targets update an existing cost catagory

        payload = {
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
            "dataSources": ["AWS", "AZURE", "GCP"],
        }

        resp = put(
            "https://app.harness.io/gateway/ccm/api/business-mapping",
            params={
                "accountIdentifier": getenv("HARNESS_ACCOUNT_ID"),
            },
            headers={
                "Content-Type": "application/json",
                "x-api-key": getenv("HARNESS_PLATFORM_API_KEY"),
            },
            json=payload,
        )

        try:
            resp.raise_for_status()
        except exceptions.HTTPError as e:
            # attempt to create the cost category
            if resp.status_code == 500:
                del payload["uuid"]

                resp = post(
                    "https://app.harness.io/gateway/ccm/api/business-mapping",
                    params={
                        "accountIdentifier": getenv("HARNESS_ACCOUNT_ID"),
                    },
                    headers={
                        "Content-Type": "application/json",
                        "x-api-key": getenv("HARNESS_PLATFORM_API_KEY"),
                    },
                    json=payload,
                )

                try:
                    resp.raise_for_status()
                except exceptions.HTTPError:
                    pass

            raise (e)

        return True

    def get_all_cost_categories() -> list:
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
