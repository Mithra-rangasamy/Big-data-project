# Environment Discovery & Setup Report
**Project**: Multi-City Air Quality & Public Health Early-Warning System  
**Course**: 21MDS56 – Big Data Computing Laboratory  
**Institution**: Coimbatore Institute of Technology  
**Host Environment**: Windows 11 / WSL2 (Ubuntu 24.04.5 LTS x86_64)  
**Date**: October 2026  

---

## 1. Detected & Configured Software Versions

| Component | Version | Installation Directory / Binary Path | Status |
| :--- | :--- | :--- | :--- |
| **Linux Distribution** | Ubuntu 24.04.5 LTS (Noble Numbat) | Kernel: `6.18.33.2-microsoft-standard-WSL2` | Active |
| **Java** | OpenJDK 1.8.0_504 (64-Bit) | `/usr/lib/jvm/java-8-openjdk-amd64` | Verified |
| **Apache Hadoop** | 3.3.6 | `/opt/hadoop` | Verified |
| **HDFS Daemons** | NameNode, DataNode, SecondaryNameNode | Port 9000 (RPC), 9870 (Web UI) | Online (Safe mode OFF) |
| **YARN Daemons** | ResourceManager, NodeManager, JobHistory | Port 8088 (Web UI), 19888 (History) | Online |
| **Apache Pig** | 0.17.0 | `/opt/pig` | Verified (Local & MapReduce) |
| **Apache HBase** | 2.5.9 | `/opt/hbase` | Untouched (Excluded from pipeline) |
| **Apache Hive** | 4.0.1 | `/opt/hive` | Configured with Derby metastore |
| **HiveServer2** | 4.0.1 (Thrift RPC) | Port 10000 | Online |
| **MongoDB Community** | 8.0.32 | `/usr/bin/mongod` (Port 27017) | Online (Systemd service) |
| **Python** | 3.12.3 | `/home/mithra/air-quality-ews/venv` | Virtualenv active with pip 26.2.1 |

---

## 2. Ports and Service Map

| Port | Protocol / Transport | Service Name | Bound IP | Verified By |
| :--- | :--- | :--- | :--- | :--- |
| **9000** | TCP / RPC | Hadoop HDFS NameNode RPC | `127.0.0.1:9000` | `hdfs dfs -ls /` & `test_services.py` |
| **9870** | TCP / HTTP | Hadoop HDFS NameNode Web UI | `0.0.0.0:9870` | `ss -tulpn` |
| **8088** | TCP / HTTP | Hadoop YARN ResourceManager Web UI | `0.0.0.0:8088` | `ss -tulpn` |
| **19888** | TCP / HTTP | MapReduce JobHistoryServer Web UI | `0.0.0.0:19888` | `ss -tulpn` |
| **10000** | TCP / Thrift | Apache HiveServer2 | `0.0.0.0:10000` | Beeline CLI & PyHive client |
| **27017** | TCP / Mongo Wire | MongoDB Community 8.0 | `127.0.0.1:27017` | `mongosh` & PyMongo client |
| **5000** | TCP / HTTP | Flask Dashboard & REST API | `0.0.0.0:5000` | Accessible from Windows browser |

---

## 3. Configuration & Compatibility Changes Made

### A. Hive 4.0.1 & Hadoop 3.3.6 Library Conflict Resolution
1. **Guava JAR Incompatibility**:
   - *Problem*: Hive 4.0.1 ships with `guava-22.0.jar`, while Hadoop 3.3.6 requires `guava-27.0-jre.jar`. Calling Hive against Hadoop 3.3.6 triggered runtime `NoSuchMethodError: com.google.common.base.Preconditions.checkArgument`.
   - *Resolution*: Backed up `/opt/hive/lib/guava-22.0.jar` to `/opt/hive/lib/guava-22.0.jar.bak`, and copied `/opt/hadoop/share/hadoop/common/lib/guava-27.0-jre.jar` into `/opt/hive/lib/`.
2. **Duplicate SLF4J Logger Bindings**:
   - *Problem*: Classpath contained bindings in both `/opt/hive/lib/log4j-slf4j-impl-2.18.0.jar` and `/opt/hadoop/share/hadoop/common/lib/slf4j-reload4j-1.7.36.jar`.
   - *Resolution*: Archived `/opt/hive/lib/log4j-slf4j-impl-2.18.0.jar` to `.bak` to silence multiple binding warnings and enforce unified logging.
3. **Hive Configuration (`/opt/hive/conf/hive-site.xml`)**:
   - Standardized Derby embedded metastore URL: `jdbc:derby:;databaseName=/home/mithra/hive_metastore_db;create=true`.
   - Enabled `hive.server2.thrift.bind.host = 0.0.0.0` and `port = 10000`.
   - Set `hive.server2.enable.doAs = false` and `hive.server2.authentication = NONE` to allow PyHive and Beeline seamless local authentication without Kerberos.

### B. Hadoop Core Site Impersonation (`core-site.xml`)
- Backed up `/opt/hadoop/etc/hadoop/core-site.xml` to `core-site.xml.bak_pre_ews`.
- Added proxyuser parameters for user `mithra` (`hadoop.proxyuser.mithra.hosts=*`, `hadoop.proxyuser.mithra.groups=*`) ensuring HiveServer2 background execution has full authorization.

### C. MongoDB Installation
- Added official MongoDB 8.0 Community APT repository for Ubuntu Noble: `https://repo.mongodb.org/apt/ubuntu noble/mongodb-org/8.0 multiverse`.
- Installed `mongodb-org` (v8.0.32), `mongodb-mongosh` (v2.13.0), and tools.
- Enabled and started `mongod` systemd daemon. Verified status with `{ ok: 1 }` response.

### D. Python 3.12 Virtual Environment & SASL Resolution
- Installed system packages: `python3-pip`, `python3-venv`, `libsasl2-dev`, `libkrb5-dev`, `build-essential`.
- *Issue*: Legacy C-extension package `sasl` fails compilation under Python 3.12 due to the removal of `longintrepr.h` in Python 3.12 C-API.
- *Resolution*: Utilized `pure-sasl` (v0.6.2) with `thrift-sasl` (v0.4.3) and `pyhive` (v0.7.0). PyHive connects directly to HiveServer2 without requiring legacy C-bindings.
- Created dedicated venv at `~/air-quality-ews/venv`.

### E. Environment Profiles
- Created `/etc/profile.d/bigdata.sh` and updated `/home/mithra/.bashrc` to guarantee `JAVA_HOME`, `HADOOP_HOME`, `PIG_HOME`, `HIVE_HOME`, and `PATH` are available in both interactive and non-interactive subshells.

---

## 4. Verification Check
- Executed `~/air-quality-ews/venv/bin/python ~/air-quality-ews/tests/test_services.py`:
  - `[1/4] MongoDB OK`: Document inserted and queried on port 27017.
  - `[2/4] HiveServer2 OK`: Connected over Thrift port 10000, queried `default` database.
  - `[3/4] HDFS OK`: Created `/data/test_smoke`, uploaded file, read back, and removed.
  - `[4/4] Apache Pig OK`: Command execution succeeded in MapReduce/Local engine.
- Result: **ALL SERVICES OPERATIONAL AND COMPATIBLE**.
