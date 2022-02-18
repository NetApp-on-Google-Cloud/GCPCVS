#!/usr/bin/env python3
# 

import GCPCVS
import logging
import typer
import json
from tabulate import tabulate

app = typer.Typer(no_args_is_help=True)
volume_app = typer.Typer(no_args_is_help=True)
app.add_typer(volume_app, name="volume")
snapshot_app = typer.Typer(no_args_is_help=True)
app.add_typer(snapshot_app, name="snapshot")
activedirectory_app = typer.Typer(no_args_is_help=True)
app.add_typer(activedirectory_app, name="activedirectory")
backup_app = typer.Typer(no_args_is_help=True)
app.add_typer(backup_app, name="backup")
replication_app = typer.Typer(no_args_is_help=True)
app.add_typer(replication_app, name="replication")
kms_app = typer.Typer(no_args_is_help=True)
app.add_typer(kms_app, name="kms")

cvs: GCPCVS

def print_results(entries: list, fields: list, style: str = "text"):
    if style == "text":
        table = []
        for i in entries:
            table.append([i[k] for k in fields])
        print(tabulate(table, headers=fields))
    if style == "json":
        print(json.dumps(entries, indent=4))
    return 

@volume_app.command()
def list(format: str = typer.Option("text", help="Specify output format: text/json")):
    result = cvs._API_getAll("-", "Volumes")
    if result.status_code != 200:
        logging.error(f"HTTP code: {result.status_code} {result.reason.decode('utf-8')} for url: {result.url}")
        return

    print_results(result.json(), ['volumeId', 'name', 'region', 'lifeCycleState', 'quotaInBytes', 'protocolTypes', 'serviceLevel', 'network'], format)
    return

@snapshot_app.command()
def list(format: str = typer.Option("text", help="Specify output format: text/json")):
    result = cvs._API_getAll("-", "Snapshots")
    if result.status_code != 200:
        logging.error(f"HTTP code: {result.status_code} {result.reason.decode('utf-8')} for url: {result.url}")
        return

    print_results(result.json(), ['ownerId', 'name', 'region', 'usedBytes'], format)
    return

@activedirectory_app.command()
def list(format: str = typer.Option("text", help="Specify output format: text/json")):
    result = cvs._API_getAll("-", "Storage/ActiveDirectory")
    if result.status_code != 200:
        logging.error(f"HTTP code: {result.status_code} {result.reason.decode('utf-8')} for url: {result.url}")
        return

    print_results(result.json(), ['UUID', 'domain', 'netBIOS', 'region', 'DNS', 'username'], format)
    return

@kms_app.command()
def list(format: str = typer.Option("text", help="Specify output format: text/json")):
    result = cvs._API_getAll("-", "Storage/KmsConfig")
    if result.status_code != 200:
        logging.error(f"HTTP code: {result.status_code} {result.reason.decode('utf-8')} for url: {result.url}")
        return

    print_results(result.json(), ['uuid', 'keyRingLocation', 'keyRing', 'keyName', 'region', 'network'], format)
    return
    
if __name__ == "__main__":
    import sys
    from os import getenv

    logging.basicConfig(level=logging.ERROR)
    credentials = getenv('SERVICE_ACCOUNT_CREDENTIAL', None)
    if credentials == None:
        logging.error('Missing service account credentials. Please set SERVICE_ACCOUNT_CREDENTIAL.')
        sys.exit(2)

    cvs = GCPCVS.GCPCVS(credentials)
    app()
