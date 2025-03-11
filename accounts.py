##########################################################################################
# create harness cost categories from csv definition
# input:
#   csv (comma delineated) where the first column are aws account ids
#   the second column can be anything (account alias for example)
#   and the rest of the columns are for each cost category you want to create
#
#   category names are derived from the first row:
#   Account ID,Account Alias,Business Area,Department,Account Owner,Account Environment
#
# usage:
#   python accounts.py "AWS Cost Categories.csv"

# authentication:
#   environment variables:
#     HARNESS_URL: url for your harness instances, usually `app.harness.io` or `app3.harness.io`
#     HARNESS_ACCOUNT_ID: account id
#     HARNESS_PLATFORM_API_KEY: api token with access to create/edit cost categories
##########################################################################################

from csv import reader
from sys import argv, exit

from costcategories import (
    CostCategory,
    Bucket,
    SharedBucket,
    ViewCondition,
    ViewOperator,
)


if __name__ == "__main__":
    if len(argv) < 2:
        print(f"usage: {argv[0]} <csv file>")
        exit(1)

    csv_file = argv[1]

    # load in the file
    file = open(csv_file, "r")
    reader = reader(file, delimiter=",")

    # grab first row (headers) and build cost category storage
    metadata = reader.__next__()

    cost_categories = {}
    # cost categories are defined after column 2
    for category in metadata[2:]:
        cost_categories[category] = {"buckets": {}, "shared": {}}

    # process all other rows
    for row in reader:
        account_id = row[0]

        # for each cost category (column 3 onward), place account in bucket
        for idx, bucket in enumerate(row[2:], start=2):
            # catch shared buckets
            if bucket.startswith("shared_"):
                name = bucket.split("_")[2]
                type = bucket.split("_")[1]

                # add account to shared bucket
                if name in cost_categories[metadata[idx]]["shared"]:
                    cost_categories[metadata[idx]]["shared"][name]["accounts"].append(
                        account_id
                    )
                else:
                    cost_categories[metadata[idx]]["shared"][name] = {
                        "accounts": [account_id],
                        "type": type,
                    }

            # regular buckets
            else:
                if bucket in cost_categories[metadata[idx]]["buckets"]:
                    cost_categories[metadata[idx]]["buckets"][bucket].append(account_id)
                else:
                    cost_categories[metadata[idx]]["buckets"][bucket] = [account_id]

    # create each cost category
    for category in cost_categories:
        # build cost targets (buckets)
        cost_targets = []

        for bucket_name in cost_categories[category]["buckets"].keys():
            bucket = Bucket(bucket_name)

            bucket.add_rule(
                {
                    "viewConditions": [
                        ViewCondition(
                            "awsUsageaccountid",
                            "Account",
                            "AWS",
                            "AWS",
                            ViewOperator.IN,
                            cost_categories[category]["buckets"][bucket_name],
                        ).format()
                    ]
                }
            )

            cost_targets.append(bucket.format())

        shared_buckets = []

        for bucket_name in cost_categories[category]["shared"].keys():
            bucket = SharedBucket(
                bucket_name, cost_categories[category]["shared"][bucket_name]["type"]
            )

            bucket.add_rule(
                {
                    "viewConditions": [
                        ViewCondition(
                            "awsUsageaccountid",
                            "Account",
                            "AWS",
                            "AWS",
                            ViewOperator.IN,
                            cost_categories[category]["shared"][bucket_name][
                                "accounts"
                            ],
                        ).format()
                    ]
                }
            )

            shared_buckets.append(bucket.format())

        # create cost category and update based on buckets
        cc = CostCategory(category)

        if cc.update(cost_targets, shared_buckets):
            print("update successful")
            print(cc)
