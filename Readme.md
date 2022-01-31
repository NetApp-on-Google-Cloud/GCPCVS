# GCPCVS

A Python module for Cloud Volume Service on GCP using API.

API documentation: https://cloudvolumesgcp-api.netapp.com/swagger.json

## Documentation

1. Create CVS service account with roles/netappcloudvolumes.admin. See https://cloud.google.com/architecture/partners/netapp-cloud-volumes/api?hl=en_US#creating_your_service_account_and_private_key

Example:
```bash
project=$(gcloud config get-value project)

gcloud iam service-accounts create cvs-api-admin --description "Admin SA for CVS API access" --display-name "cloudvolumes-admin-sa"

gcloud projects add-iam-policy-binding $project --member="serviceAccount:cvs-api-admin@$project.iam.gserviceaccount.com" --role='roles/netappcloudvolumes.admin'
```

2. Decide with authentication method to use:
   1. JSON key file
    Create JSON key to use.
    
        Example:
        ```bash
        gcloud iam service-accounts keys create cvs-api-admin.json --iam-account cvs-api-admin@$project.iam.gserviceaccount.com
        ```
   2. Service Account Impersonation
    Allow your run-user (Google IAM principal running the code) to impersonate the CVS service-account.

        Example:
        ```bash
        gcloud iam service-accounts add-iam-policy-binding cvs-api-user@cv-product-management.iam.gserviceaccount.com --member=user:<your_google_user> --role=roles/iam.serviceAccountTokenCreator
        ```

3. Installation
```bash
mkdir GCPCVS && cd GCPCVS
git clone <this repo>
pip3 install -r requirements
cd ..
```
4. Run sample code
```python
import GCVCVS
from tabulate import tabulate

project = "my-gcp-project"
# if using keyfile
cvs = GCPCVS.GCPCVS("/home/user/cvs-api-admin.json")

# or, if using service account impersonation
cvs = GCPCVS.GCPCVS("cvs-api-admin@my-gcp-project.iam.gserviceaccount.com")

# Lets list volumes
vols = cvs.getVolumesByRegion("-")

table = [[v['name'], v['region'], v['network'], int(v['usedBytes']/1024**2)] for v in vols]
print(tabulate(table))
``` 
For more available methods, see source code in GCPCVS.py.

## gcloud-like CVS tool

the cvs.py script emulates gcloud-like behaviour (read-only). It's more a proof of concept. Set SERVICE_ACCOUNT_CREDENTIAL to your absolute key file path or service account name.

```bash
export SERVICE_ACCOUNT_CREDENTIAL=cvs-api-admin@my-gcp-project.iam.gserviceaccount.com
alias gcloud-cvs="python3 -m GCPCVS.cvs"
gcloud-cvs volume list
``` 

## Getting help

This code is unsupported. Use at your own risk. The source is currently the documentation.

Code should run on Python3.6+.
Code is tested, developed and used on Python3.9 on MacOS.
