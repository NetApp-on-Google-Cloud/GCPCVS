# GCPCVS

A Python module for Cloud Volume Service on GCP using API.

API documentation: https://cloudvolumesgcp-api.netapp.com/swagger.json

## Documentation


1. Create CVS service account with roles/netappcloudvolumes.admin. See https://cloud.google.com/architecture/partners/netapp-cloud-volumes/api?hl=en_US#creating_your_service_account_and_private_key

Example:
```bash
project=$(gcloud config get-value project)

gcloud iam service-accounts create cvs-api-admin \
--description "Admin SA for CVS API access" \
--display-name "cloudvolumes-admin-sa"

gcloud projects add-iam-policy-binding $project \
--member="serviceAccount:cvs-api-admin@$project.iam.gserviceaccount.com" \
--role="roles/netappcloudvolumes.admin"
```

2. Decide with authentication method to use:
   1. JSON key file
    Create JSON key to use.
    
        Example:
        ```bash
        gcloud iam service-accounts keys create cvs-api-admin.json \
        --iam-account cvs-api-admin@$project.iam.gserviceaccount.com
        ```
   2. Service Account Impersonation
    Allow your run-user (Google IAM principal running the code) to impersonate the CVS service-account.

        Example:
        ```bash
        gcloud iam service-accounts add-iam-policy-binding cvs-api-admin@$project.iam.gserviceaccount.com \
        --member=user:<your_google_user> \
        --role=roles/iam.serviceAccountTokenCreator
        ```
    If your "run-user" is your "gcloud" user, make sure you setup your [Application Default Credentials (ADC)](https://google.aip.dev/auth/4110). Depending on the environment you run on, ADC can be set differently. If you run on a system you usually use to run gcloud commands, the most likely way to do it is to run "gcloud auth application-default login".

3. Installation

It is recommended to install the package in a python virtual environment (see https://realpython.com/python-virtual-environments-a-primer/).

```bash
git clone https://github.com/NetApp-on-Google-Cloud/GCPCVS.git
cd GCPCVS
python3 -m venv venv
source venv/bin/activate
pip3 install .
# use pip3 install -e . if you want to do modifications to the code
```
4. Run sample code

```bash
# This is just a pretty printer used in the output below. Use is not required.
pip3 install -U tabulate
```

```python
import gcpcvs
from tabulate import tabulate

project = "my-gcp-project"
# if using keyfile
cvs = gcpcvs.gcpcvs("/home/user/cvs-api-admin.json")

# or, if using service account impersonation
cvs = gcpcvs.gcpcvs("cvs-api-admin@my-gcp-project.iam.gserviceaccount.com")

# Lets list volumes
vols = cvs.getVolumesByRegion("-")

table = [[v['name'], v['region'], v['network'], int(v['usedBytes']/1024**2)] for v in vols]
print(tabulate(table))
``` 
For more available methods, see source code in gcpcvs.py.

## Upgrading

Currently the module isn't available via PyPi. Use the GitHub repository.

If you installed an older version via in process described above, use the following procedure for upgrade:

```bash
cd GCPCVS
git pull origin
pip3 install -U .
```

## gcloud-like CVS tool

The cvs.py script emulates gcloud-like behaviour (read-only). It's more a proof of concept. Set SERVICE_ACCOUNT_CREDENTIAL to your absolute key file path or service account name. Make sure you did setup your ADC properly (see above).

```bash
pip3 install -U typer tabulate
export SERVICE_ACCOUNT_CREDENTIAL=cvs-api-admin@my-gcp-project.iam.gserviceaccount.com
alias gcloud-cvs="python3 $PWD/cvs.py"
gcloud-cvs volume list
# or output JSON
gcloud-cvs volume list --format json
``` 

## Troubleshooting

Want more details of what is going on? Configure logging in your code:

```python
import logging
logging.basicConfig(level=logging.INFO)
```

It will give you infos on all method calls, and for some API calls it will log error codes. Please note that some error codes are handled internally (e.g. waiting for the API to take more calls).

Please note: The code will pass through exceptions to the using code, if they cannot be handled internally. You error handling needs to catch these exceptions or error out.

## Getting help

This code is unsupported. Use at your own risk. The source is currently the documentation.

Code should run on Python3.7+.
Code is tested, developed and used on Python3.10 on MacOS.
