#!/usr/bin/env bash
export JAVA_HOME="/usr/lib/jvm/java-8-openjdk-amd64"
export HADOOP_HOME="/opt/hadoop"
export PATH="/opt/hive/bin:/opt/hadoop/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

cd /home/mithra/air-quality-ews
beeline -u "jdbc:hive2://localhost:10000/default" -n mithra -f hive/queries.hql > docs/hive_queries_output.txt 2>&1
echo "Queries finished with exit code $?"
