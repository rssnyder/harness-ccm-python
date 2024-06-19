# harness-ccm-python

all examples are for python >= 3.8

all code uses the following for configuration:

- `HARNESS_URL`: url for your harness instances, usually `app.harness.io` or `app3.harness.io`
- `HARNESS_ACCOUNT_ID`: account id
- `HARNESS_PLATFORM_API_KEY`: api token

## costcategories

helper classes for dealing with cost categories

## perspectives

helper classes for dealing with perspectives

## example_accounts_csv.py

example python for taking a csv of cloud accounts and "buckets" they are in and creating a cost category from this information

input:
```
aws,000000000001,bucket1
aws,000000000002,bucket2
aws,000000000003,bucket3
azure,0000-000-000-0001,bucket1
azure,0000-000-000-0002,bucket2
azure,0000-000-000-0003,bucket3
gcp,proj-0001,bucket1
gcp,proj-0002,bucket2
gcp,proj-0003,bucket3
```

output:

a cost category with three buckets [`bucket1`, `bucket2`, `bucket3`] with an aws, azure, and gcp account in each 

## example_per_bucket.py

create a perspective for every bucket in a cost category

```
python example_per_bucket.py "A Folder" "A Cost Category"
```

if the folder dosnt exist, it will be created
