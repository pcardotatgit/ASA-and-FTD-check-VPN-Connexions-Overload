import pandas as pd
from sqlalchemy import create_engine
from pathlib import Path

# Locate the directory containing this file and the repository root.
# Temporarily add these directories to the system path so that we can import
# local files.
here = Path(__file__).parent.absolute()
repository_root = (here / ".").resolve()
device_list=str(repository_root) + "/files/device_list.csv"

df = pd.read_csv(device_list)
engine = create_engine('sqlite:///bases/devices.db')
df.to_sql('devices', con=engine, if_exists='replace')   #with this one you can truncat an existing database