# -*- coding: utf-8 -*-

import requests, logging
from googleapiclient import discovery, errors
from google.auth import default
from typing import Optional

def getGoogleProjectNumber(project_id: str) -> Optional[str]:
   """Lookup Project Number for gives ProjectID
   
   Args:
      project_id (str): Google Project ID
      
   Returns:
      str: Google Project Number
   
   When running inside a Google VM, App, Function etc, it will use VM Metadata to
   resolve projectID to projectNumber, else it will use
   https://cloud.google.com/resource-manager/reference/rest/v1/projects/get,
   which requires resourcemanager.projects.get permissions.
   """

   # First try to fetch from Google VM Metadata
   try:
      metadata_project_ID = requests.get("http://metadata.google.internal/computeMetadata/v1/project/project-id", headers={'Metadata-Flavor': 'Google'}).text
      metadata_project_number = requests.get("http://metadata.google.internal/computeMetadata/v1/project/numeric-project-id", headers={'Metadata-Flavor': 'Google'}).text

      if project_id == metadata_project_ID:
         return metadata_project_number
   except:
      pass

   # No metadata available, lets use resource manager
   credentials, _ = default()

   service = discovery.build('cloudresourcemanager', 'v1', credentials=credentials)

   request = service.projects().get(projectId=project_id)
   try:
      response = request.execute()
      return response["projectNumber"]
   except errors.HttpError as e:
      # Unable to resolve project. No permission or project doesn't exist
      logging.error(f"Cannot use cloudresourcemanager to resolve projectId {project_id} to project number. Missing 'resourcemanager.projects.get' permissions? ")
      pass

   logging.error(f"Cannot resolve {project_id} to project number")
   return None
