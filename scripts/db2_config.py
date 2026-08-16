import os
import ibm_db

DEFAULT_CONF_FILE = os.path.expanduser("~/.server/centox-dbowner.conf")

def get_db2_credentials(conf_path=None):
    """
    Parses DB2 authid and password from the specified config file.
    Defaults to ~/.server/centox-dbowner.conf or DB2_CONF_FILE environment variable.
    """
    path = conf_path or os.environ.get("DB2_CONF_FILE", DEFAULT_CONF_FILE)
    authid = None
    password = None
    
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("authid="):
                    authid = line.split("=", 1)[1].strip("\"' ")
                elif line.startswith("password="):
                    password = line.split("=", 1)[1].strip("\"' ")

    # Fallback to environment variables if not found in conf file
    authid = authid or os.environ.get("DB2_USER", "db2inst1")
    password = password or os.environ.get("DB2_PASSWORD", "Adm1Pwd1")
    
    host = os.environ.get("DB2_HOST", "localhost")
    port = os.environ.get("DB2_PORT", "50000")
    database = os.environ.get("DB2_DATABASE", "BCDEMO")
    
    return {
        "authid": authid,
        "password": password,
        "host": host,
        "port": port,
        "database": database,
    }

def get_db2_dsn(conf_path=None):
    """
    Constructs an ibm_db connection string (DSN).
    """
    creds = get_db2_credentials(conf_path)
    return (
        f"DATABASE={creds['database']};"
        f"HOSTNAME={creds['host']};"
        f"PORT={creds['port']};"
        f"PROTOCOL=TCPIP;"
        f"UID={creds['authid']};"
        f"PWD={creds['password']};"
    )

def connect_db2(conf_path=None):
    """
    Connects to the DB2 database using dynamic credentials.
    """
    dsn = get_db2_dsn(conf_path)
    return ibm_db.connect(dsn, "", "")
