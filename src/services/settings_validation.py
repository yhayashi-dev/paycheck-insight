"""Offline admission gate. Structural validity is not proof of legal correctness."""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import date
import json
import math
from pathlib import Path
from urllib.parse import urlsplit
from jsonschema import Draft202012Validator, FormatChecker

DATA = Path(__file__).resolve().parents[2] / 'data'
DEPTHS = {'national_tax':1, 'resident_tax':2, 'health_insurance':3,
          'pension':1, 'employment_insurance':2, 'child_support':1}


def read_json(path):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError(f'duplicate_key: {key}')
            result[key] = value
        return result
    def constant(value):
        raise ValueError(f'non_finite_number: {value}')
    return json.loads(Path(path).read_text(encoding='utf-8'), object_pairs_hook=pairs,
                      parse_constant=constant)


def records(registry):
    yield 'common', (), registry['common']
    def walk(value, depth, keys):
        if not depth:
            yield keys, value
        else:
            for key, child in value.items():
                yield from walk(child, depth-1, keys+(key,))
    for section, depth in DEPTHS.items():
        for keys, record in walk(registry[section], depth, ()):
            yield section, keys, record


def validate_registry(registry, *, policy=None):
    policy = read_json(DATA/'settings_admission_policy.json') if policy is None else policy
    issues = []
    def error(code, path, message):
        issues.append({'code':code, 'path':path, 'message':message})
    for municipality, identity in policy['municipalities'].items():
        code=identity.get('municipality_code')
        if code is None:
            if not identity.get('code_reason'):error('municipality_code_reason_missing',municipality,'null code requires reason')
        elif not isinstance(code,str) or len(code)!=6 or not code.isascii() or not code.isdigit():
            error('municipality_code_format',municipality,'six digits required, leading zeros retained')
        elif (11-sum(int(c)*w for c,w in zip(code[:5],[6,5,4,3,2]))%11)%10!=int(code[5]):
            error('municipality_code_checksum',municipality,'invalid check digit')
    assigned=[v['municipality_code'] for v in policy['municipalities'].values() if v.get('municipality_code') is not None]
    if len(assigned)!=len(set(assigned)):error('municipality_code_duplicate','/policy','duplicate national code')
    schema = read_json(DATA/'period_settings.schema.json')
    for e in Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(registry):
        error('schema_'+e.validator, '/'+ '/'.join(map(str,e.absolute_path)), e.message)
    def finite(value, path=''):
        if isinstance(value,float) and not math.isfinite(value):error('non_finite_number',path,'finite number required')
        elif isinstance(value,dict):
            for k,v in value.items():finite(v,path+'/'+k)
        elif isinstance(value,list):
            for i,v in enumerate(value):finite(v,path+'/'+str(i))
    finite(registry)
    if issues:
        return {'valid':False,'admissible':False,'issues':issues,'record_status_counts':{}}
    seen_intervals = {}
    statuses = Counter()
    def table(rows, path, contiguous=False):
        previous=0
        for i,row in enumerate(rows):
            upper=row['upper']
            if previous is None or (upper is not None and upper <= previous) or (upper is None and i!=len(rows)-1):
                error('table_order',path,'bounds must increase, open end only last')
            if contiguous and row['lower']!=previous:error('table_gap_or_overlap',path,'lower must equal preceding upper')
            previous=upper
        if rows[-1]['upper'] is not None:error('table_open_end_missing',path,'last upper must be null')
    for section,keys,r in records(registry):
        path='/'+ '/'.join((section,)+keys)
        statuses[r['status']]+=1
        if r['status']!='verified':error('setting_not_verified',path,r['status'])
        p=r['provenance']; start=date.fromisoformat(p['effective_from'])
        end=date.fromisoformat(p['effective_to']) if p['effective_to'] else None
        if end and end<start:error('period_reversed',path,'end before start')
        if end is None and not p['effective_to_reason']:error('unknown_period_reason_missing',path,'unknown end requires reason')
        for source in p['sources']:
            u=urlsplit(source['source_url'])
            try: port=u.port
            except ValueError: port=-1
            if u.scheme!='https' or u.username or u.password or port not in (None,443) or u.hostname not in policy['authorities'].get(source['authority'],[]):
                error('official_source_not_approved',path,source['source_url'])
            if date.fromisoformat(source['checked_at'])>date.today():error('checked_at_in_future',path,source['checked_at'])
            if not source['applicable_period'].strip():error('source_period_missing',path,'applicable period required')
        # Legal dates can overlap between annual snapshots. Reject conflicting values;
        # identical snapshots may coexist only with disjoint explicitly accepted months.
        group=(section,)+keys[:-1]
        if section!='common':
            for old_start,old_end,old,old_path in seen_intervals.get(group,[]):
                overlap=start <= (old_end or date.max) and old_start <= (end or date.max)
                comparable=lambda v: {k:v[k] for k in v if k not in ('note','verification','provisional')}
                if overlap and comparable(r['values'])!=comparable(old['values']):
                    error('dangerous_period_overlap',path,old_path)
                if set(r.get('coverage_months',[])) & set(old.get('coverage_months',[])):
                    error('duplicate_coverage_month',path,old_path)
            seen_intervals.setdefault(group,[]).append((start,end,r,path))
        if section=='national_tax':
            y=r['income_year']
            if keys[0]!=str(y) or r['values']['salary_income_deduction']['table_year']!=y:error('setting_year_mismatch',path,'income year/key/table mismatch')
            if y not in policy['supported_salary_income_years']:error('unsupported_salary_algorithm',path,str(y))
            if not date(y,1,1)<=start<=date(y,12,31):error('national_effective_year_mismatch',path,'effective start must be within income year for v1')
            for rows in [r['values']['salary_income_deduction']['brackets'],r['values']['income_tax']['basic_deduction_brackets']]:table(rows,path)
            table(r['values']['income_tax']['brackets'],path,True)
        elif section=='resident_tax':
            municipality,year=keys;v=r['values'];fy=r['fiscal_year']
            exemption_keys = ('income_levy_exemption', 'per_capita_levy_exemption',
                              'forest_environment_tax_exemption')
            if registry['schema_version'] == 2 or any(k in v for k in exemption_keys):
                for key in exemption_keys:
                    if key not in v:
                        error('exemption_missing', path+'/'+key, 'independent exemption required')
                    else:
                        known_sources = {s['source_url'] for s in r['provenance']['sources']}
                        if not set(v[key]['source_urls']).issubset(known_sources):
                            error('exemption_source_missing', path+'/'+key, 'source must have record provenance')
            if municipality not in policy['municipalities']:error('municipality_unknown',path,municipality)
            elif r['display_name']!=policy['municipalities'][municipality]['display_name']:error('municipality_name_mismatch',path,r['display_name'])
            if r['municipality_id']!=municipality or v['municipality_class']!=municipality or set(v['non_taxable'])!={municipality}:error('municipality_mismatch',path,'ID/class/non-taxable mismatch')
            if str(fy)!=year or r['previous_income_year']!=fy-1:error('resident_period_mismatch',path,'fiscal/previous year mismatch')
            if v['salary_income_year']!=r['previous_income_year']:error('salary_income_year_mismatch',path,'previous salary table mismatch')
            if v['salary_income_year'] not in policy['supported_salary_income_years']:error('unsupported_salary_algorithm',path,str(v['salary_income_year']))
            if start!=date(fy,4,1) or end!=date(fy+1,3,31):error('resident_effective_period_mismatch',path,'v1 requires complete declared fiscal period')
            components=v['income_components']
            if {c['name'] for c in components}!={'municipal','prefectural'}:error('component_duplicate',path,'both tax components required')
            for field,total in [('income_rate',v['income_rate']),('adjustment_rate',v['adjustment_deduction']['rate'])]:
                if not math.isclose(sum(c[field] for c in components),total,abs_tol=1e-12):error('component_sum_mismatch',path,field)
            if r['surtax']['income_rate']>v['income_rate'] or r['surtax']['per_capita']>v['per_capita']:error('surtax_exceeds_total',path,'surtax is already included')
        elif section=='health_insurance':
            insurer,branch,_=keys
            if insurer not in policy['insurers'] or branch not in policy['insurers'].get(insurer,{}).get('branches',[]):error('insurance_branch_unknown',path,branch)
            if r['insurer_id']!=insurer or r['branch_id']!=branch:error('insurance_identity_mismatch',path,'key vs ID')
        elif section=='employment_insurance' and keys[0] not in policy['business_types']:error('business_type_unknown',path,keys[0])
        if 'effective_month' in r:
            if keys[-1]!=r['effective_month']:error('setting_month_mismatch',path,'key vs month')
            if r['effective_month'] not in r['coverage_months']:error('coverage_missing',path,'snapshot month missing')
            for month in r['coverage_months']:
                try:d=date.fromisoformat(month+'-01')
                except ValueError:
                    error('invalid_month',path,month);continue
                if d<start or (end and d>end):error('setting_outside_effective_period',path,month)
                if any(d<date.fromisoformat(s) for s in r.get('component_effective_from',{}).values()):error('component_not_effective',path,month)
            if section=='child_support' and r['values']['effective_from']!=p['effective_from']:error('component_period_mismatch',path,'support effective date')
    for insurer,branches in registry['health_insurance'].items():
        for branch,months in branches.items():
            for month in months:
                for section,entries in [('pension',registry['pension']),('child_support',registry['child_support']),('employment_insurance/general',registry['employment_insurance'].get('general',{}))]:
                    if month not in entries:error('monthly_dependency_missing',f'/health_insurance/{insurer}/{branch}/{month}',section)
    common=registry['common']
    if common['metadata']['age']!=common['assumptions']['age'] or common['metadata']['dependents']!=common['assumptions']['dependents'] or common['metadata']['bonus']!=common['assumptions']['bonus_included']:
        error('common_assumption_mismatch','/common','metadata and supported assumptions differ')
    for name,rows in registry['common']['standard_monthly_remuneration'].items():
        table(rows,'/common/'+name,True)
        if any(b['standard']<=a['standard'] for a,b in zip(rows,rows[1:])):error('standard_order','/common/'+name,'standards must increase')
    return {'valid':not issues,'admissible':not issues,'issues':issues,'record_status_counts':dict(statuses)}


def require_valid(registry):
    result=validate_registry(registry)
    if not result['admissible']:
        raise ValueError('; '.join(i['code']+': '+i['path'] for i in result['issues']))


def validate_file(path, presets=()):
    try:
        registry=read_json(path);result=validate_registry(registry)
        if result['valid']:
            for preset in presets:
                c=read_json(preset)['calculation_context']
                refs=[('national_tax',c['income_year']),('resident_tax',c['municipality_id'],c['fiscal_year']),('health_insurance',c['insurer_id'],c['branch_id'],c['effective_month']),('pension',c['effective_month']),('employment_insurance',c['business_type'],c['effective_month']),('child_support',c['effective_month'])]
                for ref in refs:
                    try:
                        node=registry
                        for k in ref:node=node[str(k)]
                    except KeyError:result['issues'].append({'code':'preset_reference_missing','path':str(preset),'message':str(ref)})
        result['valid']=result['admissible']=not result['issues']
        return result
    except (ValueError, OSError, KeyError, TypeError) as e:
        return {'valid':False,'admissible':False,'issues':[{'code':str(e).split(':')[0] if isinstance(e,ValueError) else 'input_error','path':str(path),'message':str(e)}]}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--settings',type=Path,default=DATA/'period_settings.json')
    parser.add_argument('--preset',action='append',type=Path)
    args=parser.parse_args()
    result=validate_file(args.settings,args.preset if args.preset is not None else sorted(DATA.glob('rates_2026_*.json')))
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0 if result['admissible'] else 1

if __name__=='__main__':raise SystemExit(main())
