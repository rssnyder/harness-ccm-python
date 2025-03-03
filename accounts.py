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
        cost_categories[category] = {}

    # process all other rows
    for row in reader:
        # for each cost category (column 3 onward), place account in bucket
        for idx, bucket in enumerate(row[2:], start=2):
            if bucket in cost_categories[metadata[idx]]:
                cost_categories[metadata[idx]][bucket].append(row[0])
            else:
                cost_categories[metadata[idx]][bucket] = [row[0]]

    # create each cost category
    for category in cost_categories:
        # build cost targets (buckets)
        cost_targets = []

        for bucket_name in cost_categories[category].keys():
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
                            cost_categories[category][bucket_name],
                        ).format()
                    ]
                }
            )

            cost_targets.append(bucket.format())

        # create cost category and update based on buckets
        cc = CostCategory(category)

        if cc.update(cost_targets):
            print("update successful")
            print(cc)
