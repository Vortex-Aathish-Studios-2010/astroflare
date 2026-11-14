"""Cross-check every curated raw row against the byte-pinned original NASA CSV."""
import pathlib,json,csv,hashlib
p=pathlib.Path(__file__).resolve().parent.parent
data=json.loads((p/'public/dataset.json').read_text())
for record in data['records']:
 raw=(p/'sources'/f"{record['id']}-table.csv").read_bytes()
 assert hashlib.sha256(raw).hexdigest()==record['sha256']
 rows=[{(k or '').strip():(v or '').strip() for k,v in row.items() if isinstance(v,str)} for row in csv.DictReader(raw.decode('utf-8-sig').splitlines())]
 key='Test #' if record['id']=='PSI-25' else 'Sample Number'
 for run in record['runs']:
  row=next(row for row in rows if row.get(key)==run['id'])
  assert row==run['raw'],(record['id'],run['id'])
  outcome=run['outcome']
  if record['id']=='PSI-25':
   assert float(row['Final CO (ppm)'])==outcome['finalCO']
   assert float(row['Initial CO (ppm)'])==outcome['initialCO']
   assert row['Calibrated  initial O2 % by vol']==run['oxygenInitial']
   assert run['airflow']=='Not reported'
  else:
   assert run['direction']==row['Flow Direction']
   assert run['airflow']==(row['Air Flow (cm/s)'] if 'cm/s' in row['Air Flow (cm/s)'] else row['Air Flow (cm/s)']+' cm/s')
   assert run['oxygen']==row['Percent O2 (Note 1)' if record['id']=='PSI-99' else 'Percent O2']
   assert outcome['burnTime']==(row['Burn Time (s)'] if record['id']=='PSI-99' else row['Burn Time (s)']+' s')
   if run['id']=='2-5':assert outcome['spreadRate']==row['?-g Spread Length']=='2.1 mm/s'
   else:assert outcome['spreadRate']=='Not reported'
 print('PASS',record['id'],len(record['runs']),'curated rows; raw values, units and conditions match pinned original')
