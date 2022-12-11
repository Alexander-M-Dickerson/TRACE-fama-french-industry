import pandas as pd
import numpy as np
from dateutil.relativedelta import *
from pandas.tseries.offsets import *
import datetime as datetime
import pandasql as ps

# =============================================================================
# Read in TRACE processed data from WRDS Bond Module
# =============================================================================
# Read in all data from TRACE Bond Returns Module
df = pd.read_csv('milbyvewfkxzypnm.csv.gz', compression = "gzip" )
df.columns = map(str.lower, df.columns)
df.rename(columns={'issue_id':'issueid' }, inplace=True)
df['date'] = pd.to_datetime(df['date'], format = "%Y%m%d")

# Ensures dates are at the very last day of month t
df['date'] = df['date'] + pd.offsets.MonthEnd(0)

df.set_index(['date','issueid'], inplace = True)
df = df.sort_index(level = ["issueid","date"])
df = df.reset_index()

df = df[['date', 'issueid']].dropna()

# Load the Mergent FISD data for the sic codes #
FISDx = pd.read_csv('FISD_2022.gz')
FISDx.columns = FISDx.columns.str.lower()
FISDx = FISDx[['issue_id','complete_cusip','sic_code','industry_code']]
FISDx.columns = ['issueid','complete_cusip','sic_code','industry_code']
df = df.merge(FISDx, how = "left", left_on = ['issueid'], right_on = ['issueid'])
# =============================================================================
df = df.set_index(['date','issueid'])

# Note: there seem to be many cases where the sic codes are missing #
# =============================================================================
ffi30 = pd.read_csv('ind30.csv')
ffi17 = pd.read_csv('ind17.csv')

# Use SQL within Pandas / Python to merge #
# May take up to ~5mins to run each time.

# Fama French 30
sqlcode ='''
SELECT a.issueid, a.date, b.ind_num
FROM df AS a
LEFT JOIN 
ffi30 AS b
ON a.sic_code BETWEEN b.sic_low AND b.sic_high;
'''

dfi30 = ps.sqldf(sqlcode,locals())
dfi30['date'] = pd.to_datetime( dfi30['date'])
dfi30.rename(columns={'ind_num':'ind_num_30'}, inplace=True)

# Fama French 17
sqlcode ='''
SELECT a.issueid, a.date, b.ind_num
FROM df AS a
LEFT JOIN 
ffi17 AS b
ON a.sic_code BETWEEN b.sic_low AND b.sic_high;
'''

dfi17 = ps.sqldf(sqlcode,locals())
dfi17['date'] = pd.to_datetime( dfi17['date'])
dfi17.rename(columns={'ind_num':'ind_num_17'}, inplace=True)

dfIndustryExport = dfi30.merge(dfi17, how = "inner", left_on = ['issueid','date'],
                               right_on = ['issueid','date'])

dfIndustryExport.isnull().sum()
dfIndustryExport.to_csv('TRACE_fama_french_industry.gz', compression = "gzip")
# =============================================================================
