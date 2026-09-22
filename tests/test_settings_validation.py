from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import pytest
from src.services.settings_validation import DATA, read_json, validate_registry, validate_file
from src.services.period_settings import CalculationContext, load_calculation_rates

BASE=CalculationContext(2026,'tokyo_23_wards',2026,'kyokai_kenpo','tokyo','2026-04')

def registry():return read_json(DATA/'period_settings.json')
def local(x):return x['resident_tax']['tokyo_23_wards']['2026']
def health(x):return x['health_insurance']['kyokai_kenpo']['tokyo']['2026-04']
def national(x):return x['national_tax']['2026']
def codes(x):return {i['code'] for i in validate_registry(x)['issues']}

def test_normal_registry_and_all_presets():
 r=validate_file(DATA/'period_settings.json',sorted(DATA.glob('rates_2026_*.json')))
 assert r['valid'] and r['record_status_counts']=={'verified':47}

@pytest.mark.parametrize('mutate,code',[
 (lambda x:local(x)['provenance'].update(sources=[]),'schema_minItems'),
 (lambda x:local(x).update(previous_income_year=2024),'resident_period_mismatch'),
 (lambda x:local(x).update(fiscal_year=2025),'resident_period_mismatch'),
 (lambda x:local(x).update(municipality_id='unknown'),'municipality_mismatch'),
 (lambda x:local(x).update(display_name='unknown'),'municipality_name_mismatch'),
 (lambda x:local(x)['values'].pop('non_taxable'),'schema_required'),
 (lambda x:local(x)['values'].update(per_capita=-1),'schema_minimum'),
 (lambda x:local(x)['values'].update(income_rate='0.1'),'schema_type'),
 (lambda x:local(x)['values'].update(forest_environment_tax=True),'schema_type'),
 (lambda x:local(x)['values'].update(income_rate=.2),'component_sum_mismatch'),
 (lambda x:local(x)['values']['income_components'][0].update(name='prefectural'),'component_duplicate'),
 (lambda x:local(x)['surtax'].update(per_capita=999999),'surtax_exceeds_total'),
 (lambda x:health(x).update(branch_id='osaka'),'insurance_identity_mismatch'),
 (lambda x:health(x).update(insurer_id='other'),'insurance_identity_mismatch'),
 (lambda x:health(x)['values'].update(health_insurance_rate=9.85),'schema_maximum'),
 (lambda x:health(x)['values'].update(care_insurance_rate=float('nan')),'non_finite_number'),
 (lambda x:health(x).update(effective_month='2026-13'),'schema_pattern'),
 (lambda x:health(x).update(effective_month='0000-04',coverage_months=['0000-04']),'invalid_month'),
 (lambda x:health(x)['provenance'].update(effective_from='2026-02-30'),'schema_format'),
 (lambda x:health(x)['provenance'].update(effective_from='2026-05-01'),'setting_outside_effective_period'),
 (lambda x:health(x)['provenance'].update(effective_to='2026-02-01'),'period_reversed'),
 (lambda x:health(x)['provenance'].update(effective_to_reason=None),'unknown_period_reason_missing'),
 (lambda x:health(x)['provenance']['sources'][0].update(checked_at='bad'),'schema_format'),
 (lambda x:health(x)['provenance']['sources'][0].update(source_url='https://example.org/source'),'official_source_not_approved'),
 (lambda x:health(x)['provenance']['sources'][0].update(authority='unapproved'),'official_source_not_approved'),
 (lambda x:national(x)['values']['salary_income_deduction'].update(table_year=2025),'setting_year_mismatch'),
 (lambda x:national(x)['values']['income_tax']['brackets'][1].update(lower=1),'table_gap_or_overlap'),
 (lambda x:x['common']['standard_monthly_remuneration']['health'][1].update(lower=1),'table_gap_or_overlap'),
 (lambda x:x['common']['rounding'].update(annual_tax_unit=0),'schema_minimum'),
 (lambda x:x.pop('child_support'),'schema_required'),
 (lambda x:x['pension']['2026-04']['values'].pop('pension_rate'),'schema_required'),
 (lambda x:x['employment_insurance']['general']['2026-04']['values'].update(worker_rate=-.1),'schema_minimum'),
 (lambda x:x['child_support']['2026-04']['values'].update(rate=2),'schema_maximum'),
])
def test_bad_records_rejected(mutate,code):
 x=registry();mutate(x);assert code in codes(x)

@pytest.mark.parametrize('status',['candidate','needs_review','rejected'])
def test_non_verified_never_enters_calculation(status,tmp_path):
 x=registry();health(x)['status']=status;p=tmp_path/'settings.json';p.write_text(json.dumps(x))
 with pytest.raises(ValueError,match='setting_not_verified'):load_calculation_rates(BASE,settings_file=p)
 assert health(x)['status']==status

@pytest.mark.parametrize('kind',['municipality','branch','business'])
def test_unknown_registered_identity(kind):
 x=registry()
 if kind=='municipality':x['resident_tax']['unknown']=x['resident_tax'].pop('tokyo_23_wards')
 elif kind=='branch':x['health_insurance']['kyokai_kenpo']['unknown']=x['health_insurance']['kyokai_kenpo'].pop('tokyo')
 else:x['employment_insurance']['unknown']=x['employment_insurance'].pop('general')
 assert {'municipality_unknown','insurance_branch_unknown','business_type_unknown'} & codes(x)

@pytest.mark.parametrize('changed',[True,False])
def test_overlap_detection(changed):
 x=registry();r=deepcopy(health(x));r['effective_month']='2026-05'
 r['coverage_months']=['2026-04','2026-05']
 if changed:r['values']['health_insurance_rate']=.12
 x['health_insurance']['kyokai_kenpo']['tokyo']['2026-05']=r
 assert 'duplicate_coverage_month' in codes(x)
 if changed:assert 'dangerous_period_overlap' in codes(x)

def test_identical_legal_period_disjoint_snapshots_allowed():
 x=registry();r=deepcopy(health(x));r.update(effective_month='2026-05',coverage_months=['2026-05'])
 x['health_insurance']['kyokai_kenpo']['tokyo']['2026-05']=r
 for entries in [x['pension'],x['child_support'],x['employment_insurance']['general']]:
  entries['2026-05']=deepcopy(entries['2026-04'])
  entries['2026-05'].update(effective_month='2026-05',coverage_months=['2026-05'])
 assert validate_registry(x)['valid']

@pytest.mark.parametrize('text,code',[
 ('{"x":1,"x":2}','duplicate_key'),
 ('{"nested":{"x":1,"x":2}}','duplicate_key'),
 ('{"x":NaN}','non_finite_number'),
 ('{"x":Infinity}','non_finite_number'),
])
def test_duplicate_json_keys_and_constants(text,code,tmp_path):
 p=tmp_path/'bad.json';p.write_text(text)
 assert validate_file(p)['issues'][0]['code']==code

def test_broken_preset_reference(tmp_path):
 p=tmp_path/'preset.json';x=read_json(DATA/'rates_2026_tokyo.json');x['calculation_context']['branch_id']='unknown';p.write_text(json.dumps(x))
 assert validate_file(DATA/'period_settings.json',[p])['issues'][0]['code']=='preset_reference_missing'

def test_cli_and_exit_code(tmp_path):
 root=DATA.parent
 ok=subprocess.run([sys.executable,'-m','src.services.settings_validation'],cwd=root,capture_output=True,text=True)
 assert ok.returncode==0 and json.loads(ok.stdout)['valid']
 p=tmp_path/'bad.json';p.write_text('{"x":1,"x":2}')
 bad=subprocess.run([sys.executable,'-m','src.services.settings_validation','--settings',str(p)],cwd=root,capture_output=True,text=True)
 assert bad.returncode==1 and not json.loads(bad.stdout)['valid']


def test_missing_monthly_dependency():
    x=registry();r=deepcopy(health(x));r.update(effective_month='2026-05',coverage_months=['2026-05'])
    x['health_insurance']['kyokai_kenpo']['tokyo']['2026-05']=r
    assert 'monthly_dependency_missing' in codes(x)

@pytest.mark.parametrize('code,expected',[('123','municipality_code_format'),('141004','municipality_code_checksum')])
def test_future_municipality_codes(code,expected):
    p=read_json(DATA/'settings_admission_policy.json');p['municipalities']['yokohama_city']['municipality_code']=code
    assert expected in {i['code'] for i in validate_registry(registry(),policy=p)['issues']}
