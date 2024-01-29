from csv import reader
from sys import argv, exit
from collections import defaultdict

from common import CloudAccount, CostCategory


if __name__ == "__main__":
    if len(argv) < 3:
        print(f"usage: {argv[0]} <csv file> <cost catagory name>")
        exit(1)

    csv_file = argv[1]
    cost_catagory_name = argv[2]

    file = open(csv_file, "r")
    reader = reader(file, delimiter=",")

    # load all rows
    accounts = []
    buckets = defaultdict(list)

    for column in reader:
        account = CloudAccount(column[0].lower(), column[1], column[2])

        accounts.append(account)
        buckets[account.bucket].append(account)

    # build cost catagory buckets
    cost_targets = []

    for bucket in buckets.keys():
        # create rules for each cloud
        rules = []

        if aws_accounts := [x.identifier for x in buckets[bucket] if x.cloud == "aws"]:
            rules.append(
                {
                    "viewConditions": [
                        {
                            "type": "VIEW_ID_CONDITION",
                            "viewField": {
                                "fieldId": "awsUsageaccountid",
                                "fieldName": "Account",
                                "identifier": "AWS",
                                "identifierName": "AWS",
                            },
                            "viewOperator": "IN",
                            "values": aws_accounts,
                        }
                    ]
                }
            )
        if azure_accounts := [
            x.identifier for x in buckets[bucket] if x.cloud == "azure"
        ]:
            rules.append(
                {
                    "viewConditions": [
                        {
                            "type": "VIEW_ID_CONDITION",
                            "viewField": {
                                "fieldId": "awsUsageaccountid",
                                "fieldName": "Account",
                                "identifier": "AZURE",
                                "identifierName": "Azure",
                            },
                            "viewOperator": "IN",
                            "values": azure_accounts,
                        }
                    ]
                }
            )
        if gcp_accounts := [x.identifier for x in buckets[bucket] if x.cloud == "gcp"]:
            rules.append(
                {
                    "viewConditions": [
                        {
                            "type": "VIEW_ID_CONDITION",
                            "viewField": {
                                "fieldId": "awsUsageaccountid",
                                "fieldName": "Account",
                                "identifier": "GCP",
                                "identifierName": "GCP",
                            },
                            "viewOperator": "IN",
                            "values": gcp_accounts,
                        }
                    ]
                }
            )

        cost_targets.append(
            {
                "name": bucket,
                "rules": rules,
            }
        )

    # create cost category and update based on buckets
    cc = CostCategory(cost_catagory_name)

    if cc.update_cost_category(cost_targets):
        print("update successful")
