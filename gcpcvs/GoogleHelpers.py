# -*- coding: utf-8 -*-
# 
# This file contains code which doesn't use CVS APIs, but Google APIs
# to do CVS related things

import requests, logging, re
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

   request = service.projects().get(projectId = project_id)
   try:
      response = request.execute()
      return response["projectNumber"]
   except errors.HttpError as e:
      # Unable to resolve project. No permission or project doesn't exist
      logging.error(f"Cannot use cloudresourcemanager to resolve projectId {project_id} to project number. Missing 'resourcemanager.projects.get' permissions? ")
      pass

   logging.error(f"Cannot resolve {project_id} to project number")
   return None

class VPCPeerings():
   cvs_peerings = []
   def __init__(self, project: str):
      self.update_peerings(project)

   def update_peerings(self, project: str):
      # Fetch all Peerings to CVS
      credentials, _ = default()
      service = discovery.build('compute', 'v1', credentials=credentials)

      self.cvs_peerings = []
      request = service.networks().list(project = project)
      while request is not None:
         response = request.execute()
         for network in response['items']:
            for peering in network['peerings']:
                  m = re.search(f'https://www.googleapis.com/compute/v1/projects/(.+)/global/networks/(netapp(-sds)?-tenant-vpc)$', peering['network'])
                  if m:
                     peering['vpc'] = network['name']
                     peering['tp'] = m.group(1)
                     if m.group(3):
                        peering['hardware'] = False
                     else:
                        peering['hardware'] = True
                     self.cvs_peerings.append(peering)
         request = service.networks().list_next(previous_request=request, previous_response=response)

   def get_networks(self):
      # Returns a set of all connected VPCs.
      # hardware or software
      return  {p['vpc'] for p in self.cvs_peerings}

   def get_tenant_project(self, is_hw: bool, vpc: str):
      for n in self.cvs_peerings:
         if n['vpc'] == vpc and n['hardware'] == is_hw:
            return n['tp']
      return None



      