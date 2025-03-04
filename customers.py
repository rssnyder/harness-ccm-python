from csv import reader
from sys import argv, exit

from costcategories import (
    CostCategory,
    Bucket,
    ViewCondition,
    ViewOperator,
)


# csv should have id and name of customer
class Customer:
    def __init__(
        self,
        id: str,
        name: str,
    ):
        self.id = id.zfill(4)
        self.name = name


if __name__ == "__main__":
    if len(argv) < 3:
        print(f"usage: {argv[0]} <csv file> <cost catagory name>")
        exit(1)

    csv_file = argv[1]
    cost_catagory_name = argv[2]

    # load in csv
    file = open(csv_file, "r")
    reader = reader(file, delimiter=",")

    # grab first row (headers) and build cost category storage
    metadata = reader.__next__()

    # storage for rows
    customers = []

    for row in reader:
        # store id, customer
        customers.append(Customer(row[0], row[1]))

    # build cost catagory buckets
    cost_targets = []

    for customer in customers:
        # a bucket represents a customer
        bucket = Bucket(customer.name)

        # add base label
        bucket.add_rule(
            {
                "viewConditions": [
                    ViewCondition(
                        "labels.value",
                        f"orgid_r{customer.id}",
                        "LABEL",
                        "label",
                        ViewOperator.NOT_NULL,
                        [],
                    ).format(),
                    ViewCondition(
                        "labels.value",
                        "tenancy",
                        "LABEL",
                        "label",
                        ViewOperator.IN,
                        ["dedicated"],
                    ).format(),
                ]
            }
        )

        # add k8s labels added by gcp
        bucket.add_rule(
            {
                "viewConditions": [
                    ViewCondition(
                        "labels.value",
                        f"k8s-label/orgid_r{customer.id}",
                        "LABEL",
                        "label",
                        ViewOperator.NOT_NULL,
                        [],
                    ).format(),
                    ViewCondition(
                        "labels.value",
                        "tenancy",
                        "LABEL",
                        "label",
                        ViewOperator.IN,
                        ["dedicated"],
                    ).format(),
                ]
            }
        )

        # add k8s namespace labels added by gcp
        bucket.add_rule(
            {
                "viewConditions": [
                    ViewCondition(
                        "labels.value",
                        f"k8s-namespace-labels/orgid_r{customer.id}",
                        "LABEL",
                        "label",
                        ViewOperator.NOT_NULL,
                        [],
                    ).format(),
                    ViewCondition(
                        "labels.value",
                        "tenancy",
                        "LABEL",
                        "label",
                        ViewOperator.IN,
                        ["dedicated"],
                    ).format(),
                ]
            }
        )

        cost_targets.append(bucket.format())

    # create cost category and update based on buckets
    cc = CostCategory(cost_catagory_name)

    if cc.update(cost_targets):
        print("update successful")
        print(cc)
