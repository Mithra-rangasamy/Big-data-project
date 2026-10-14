#!/usr/bin/env python3
"""
CIT 21MDS56: Air Quality & Public Health Early-Warning System
ingestion/hdfs_utils.py
High-performance batch utilities for HDFS partitioned landing zone.
"""

import os
import subprocess
import shutil

def get_hadoop_env():
    env = os.environ.copy()
    env.setdefault("JAVA_HOME", "/usr/lib/jvm/java-8-openjdk-amd64")
    env.setdefault("HADOOP_HOME", "/opt/hadoop")
    env.setdefault("PATH", f"/opt/hadoop/bin:/opt/hadoop/sbin:{env.get('PATH', '')}")
    return env

def hdfs_mkdir(hdfs_path):
    cmd = ["hdfs", "dfs", "-mkdir", "-p", hdfs_path]
    res = subprocess.run(cmd, env=get_hadoop_env(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return res.returncode == 0

def hdfs_sync_staging_tree(local_staging_root, hdfs_dest_root):
    """
    Copies entire partitioned directory tree from local staging directly into HDFS
    in a single atomic JVM invocation.
    """
    hdfs_mkdir(hdfs_dest_root)
    shell_cmd = f"hdfs dfs -mkdir -p {hdfs_dest_root} && hdfs dfs -put -f {local_staging_root}/* {hdfs_dest_root}/"
    res = subprocess.run(
        ["bash", "-c", shell_cmd],
        env=get_hadoop_env(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    if res.returncode != 0:
        raise RuntimeError(f"HDFS batch put failed: {res.stderr}")
    return True

def hdfs_put_string(content_str, hdfs_target_file):
    parent_dir = os.path.dirname(hdfs_target_file)
    hdfs_mkdir(parent_dir)
    cmd = ["hdfs", "dfs", "-put", "-f", "-", hdfs_target_file]
    res = subprocess.run(
        cmd,
        input=content_str,
        env=get_hadoop_env(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    if res.returncode != 0:
        raise RuntimeError(f"Failed to put data to HDFS {hdfs_target_file}: {res.stderr}")
    return True

def hdfs_append_line(line_str, hdfs_target_file):
    parent_dir = os.path.dirname(hdfs_target_file)
    hdfs_mkdir(parent_dir)
    # Check if target file exists
    test_cmd = ["hdfs", "dfs", "-test", "-e", hdfs_target_file]
    exists = subprocess.run(test_cmd, env=get_hadoop_env()).returncode == 0
    if exists:
        cmd = ["hdfs", "dfs", "-appendToFile", "-", hdfs_target_file]
    else:
        cmd = ["hdfs", "dfs", "-put", "-", hdfs_target_file]
    res = subprocess.run(cmd, input=(line_str if line_str.endswith("\n") else line_str + "\n"), env=get_hadoop_env(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return res.returncode == 0

