#!/usr/bin/python3

import app
import datetime

from classes import *
from github import Github
from flask_mongoengine import MongoEngine

def getVendorNameFromRepo(repo):
    v = "error"
    n = "error"

    if len(repo) == 0:
        return v, n

    if len(repo.split('_')) < 2:
        # lge-kernel-mako
        if len(repo.split('-')) >= 3:
            v = repo.split('-')[0]
            n = repo.split('-')[2]
    elif len(repo.split('_')) == 4:
        # android_kernel_samsung_manta
        v = repo.split('_')[2]
        n = repo.split('_')[3]

    return v, n

def getKernelTableFromGithub(app):
    print("Updating kernel list from github...this may take a long time...")

    u = app.config['GITHUBUSER']
    p = app.config['GITHUBTOKEN']
    g = Github(u, p)

    org = g.get_organization('LineageOS')

    for repo in org.get_repos():
        if "android_kernel_" in repo.name or "-kernel-" in repo.name:
            print(repo.name)
            if Kernel.objects(repo_name=repo.name).count() == 0:
                addKernel(repo.name, repo.updated_at)
            else:
                Kernel.objects(repo_name=repo.name).update(last_github_update=repo.updated_at)

    print("Done!")
    return

def addKernel(reponame, last_update=datetime.datetime.now()):
    v, n = getVendorNameFromRepo(reponame)
    if v is not "error" and n is not "error":
        Kernel(repo_name=reponame, last_github_update=last_update, vendor=v, device=n).save()
        for c in CVE.objects():
            Patches(cve=c.id, kernel=Kernel.objects.get(repo_name=reponame).id, status=Status.objects.get(text=Status.objects(short_id=1).first()['text']).id).save()

def nukeCVE(cve):
    if CVE.objects(cve_name=cve):
        cve_id = CVE.objects(cve_name=cve).first()['id']
        Patches.objects(cve=cve_id).delete()
        Links.objects(cve_id=cve_id).delete()
        CVE.objects(id=cve_id).delete()

def getProgress(kernel):
    patched = Patches.objects(kernel=kernel, status=Status.objects.get(text=Status.objects(short_id=2).first()['text']).id).count()
    dna = Patches.objects(kernel=kernel, status=Status.objects.get(text=Status.objects(short_id=3).first()['text']).id).count()
    progress = 100 * (patched + dna) / CVE.objects().count()
    return progress
