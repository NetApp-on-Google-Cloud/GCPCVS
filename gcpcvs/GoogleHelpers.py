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

def get_host_project(service_project: str) -> str:
   """Lookup host project ID for gives ProjectID
   
   Args:
      service_project (str): Google Service Project ID
      
   Returns: Host Project ID
   """
   credentials, project = default()

   service = discovery.build('compute', 'v1', credentials = credentials)

   request = service.projects().getXpnHost(project = service_project)
   response = request.execute()

   if 'name' in response:
      return response['name']
   else:
      return None

def get_gcp_regions() -> list[str]:
   """Returns list of all GCP regions
   
   Returns:
      list(str): List of GCP regions
   
   """   
   credentials, project = default()
   service = discovery.build('compute', 'v1', credentials = credentials)

   request = service.regions().list(project = project)
   gcp_regions = []
   while request is not None:
      response = request.execute()

      for region in response['items']:
         gcp_regions.append(region['name'])

      request = service.regions().list_next(previous_request=request, previous_response=response)
   return gcp_regions

class VPCPeerings():
   cvs_peerings = []
   def __init__(self, project: str):
      """
      Args:
         project (str): Google project_id
      """
      self.cvs_peerings = []
      self.update_peerings(project)
      # If project is a service project, get CVS peerings for host project also
      host_project = get_host_project(project)
      if host_project:
         self.update_peerings(host_project)

   def update_peerings(self, project: str):
      # Fetch all Peerings to CVS
      credentials, _ = default()
      service = discovery.build('compute', 'v1', credentials=credentials)

      request = service.networks().list(project = project)
      while request is not None:
         response = request.execute()
         if 'items' in response:
            # Iterate over all VPCs found
            for network in response['items']:
               # Does the VPC have an peerings?
               if 'peerings' in network:
                  for peering in network['peerings']:
                        m = re.search(f'https://www.googleapis.com/compute/v1/projects/(.+)/global/networks/(netapp(-sds)?-tenant-vpc)$', peering['network'])
                        if m:
                           peering['vpc'] = network['name']
                           peering['tp'] = m.group(1)
                           if m.group(3):
                              peering['hardware'] = False
                           else:
                              peering['hardware'] = True
                           peering['project'] = project
                           self.cvs_peerings.append(peering)
         request = service.networks().list_next(previous_request=request, previous_response=response)

   def get_networks(self, is_hw: bool) -> set:
      """
      Get list of peered VPCs for service type

      Args:
         is_hw (bool): True for CVS-Performance, False for CVS
      """
      # Returns a set of all connected VPCs.
      # hardware or software
      r = set()
      for p in self.cvs_peerings:
         if p['hardware'] == is_hw:
            r.add(p['vpc'])
      return r

   def get_tenant_project(self, is_hw: bool, vpc: str) -> str:
      # Returns tenant project for given VPC and service type
      for n in self.cvs_peerings:
         if n['vpc'] == vpc and n['hardware'] == is_hw:
            return n['tp']
      return None

   def is_active(self, is_hw: bool, vpc: str) -> bool:
      # Checks if peering in active
      for n in self.cvs_peerings:
         if n['vpc'] == vpc and n['hardware'] == is_hw:
            return n['state'] == 'ACTIVE'
      return None




      