from csv import reader
from sys import argv, exit
from collections import defaultdict

from common import CloudAccount, CostCategory, Bucket, ViewCondition, ViewOperator


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

    for name in buckets.keys():
        # create rules for each cloud
        bucket = Bucket(name)

        if aws_accounts := [x.identifier for x in buckets[name] if x.cloud == "aws"]:
            bucket.add_rule(
                {
                    "viewConditions": [
                        ViewCondition(
                            "awsUsageaccountid",
                            "Account",
                            "AWS",
                            "AWS",
                            ViewOperator.IN,
                            aws_accounts,
                        ).format()
                    ]
                }
            )
        if azure_accounts := [
            x.identifier for x in buckets[name] if x.cloud == "azure"
        ]:
            bucket.add_rule(
                {
                    "viewConditions": [
                        ViewCondition(
                            "azureSubscriptionGuid",
                            "Subscription id",
                            "AZURE",
                            "Azure",
                            ViewOperator.IN,
                            azure_accounts,
                        ).format()
                    ]
                }
            )
        if gcp_accounts := [x.identifier for x in buckets[name] if x.cloud == "gcp"]:
            bucket.add_rule(
                {
                    "viewConditions": [
                        ViewCondition(
                            "gcpProjectId",
                            "Project",
                            "GCP",
                            "GCP",
                            ViewOperator.IN,
                            gcp_accounts,
                        ).format()
                    ]
                }
            )

        cost_targets.append(bucket.format())

    # create cost category and update based on buckets
    cc = CostCategory(cost_catagory_name)

    if cc.update(cost_targets):
        print("update successful")
