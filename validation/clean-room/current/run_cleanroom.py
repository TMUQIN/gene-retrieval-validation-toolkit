# SPDX-License-Identifier: CC-BY-4.0
"""Run a fresh external clean-room check. PyPI downloads are setup-only."""
from __future__ import annotations
import argparse, csv, hashlib, json, os, re, shutil, subprocess, sys
from pathlib import Path

WORKER = r'''
import sys, os, json, gzip, importlib, importlib.metadata, site
from pathlib import Path
run=Path(sys.argv[1]).resolve(); phase=sys.argv[2]
snapshot=run/"snapshot"; evidence=run/"evidence"; scratch=run/"scratch"
base=Path(sys.base_prefix).resolve(); venv=Path(sys.prefix).resolve()
reads=[snapshot,venv,scratch,evidence]
writes=[scratch,evidence,snapshot/".pytest_tmp"]
devnull=os.path.normcase(os.path.realpath(os.devnull)); blocked=[]; probing=False

def inside(path,roots):
    return any(path==root or path.is_relative_to(root) for root in roots)
def permitted(path,writing=False):
    if isinstance(path,int): return True
    path=Path(os.fsdecode(path if path is not None else os.curdir)).resolve()
    if os.path.normcase(str(path))==devnull: return True
    if writing: return inside(path,writes)
    return inside(path,reads) or (path.is_relative_to(base) and "site-packages" not in path.parts)
def deny(event):
    blocked.append({"event":event,"probe":probing})
    raise PermissionError("clean-room boundary rejected "+event)
def audit(event,args):
    if event=="open":
        path,mode,flags=args
        writing=any(c in (mode or "") for c in "wax+") or bool(flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))
        if not permitted(path,writing): deny(event)
    elif event in {"os.listdir","os.scandir"}:
        if not permitted(args[0]): deny(event)
    elif event in {"os.mkdir","os.rmdir","os.remove","os.chmod","os.utime"}:
        if not permitted(args[0],True): deny(event)
    elif event in {"os.rename","os.link","os.symlink"}:
        if not permitted(args[0],True) or not permitted(args[1],True): deny(event)
    elif event.startswith("socket.") or event in {"subprocess.Popen","os.system","os.startfile","os.posix_spawn","os.exec","os.spawn"}:
        deny(event)
sys.addaudithook(audit)
records=[]
def check(name,condition,detail):
    records.append({"check":name,"status":"PASS" if condition else "FAIL","detail":detail})
    if not condition: raise AssertionError(name+": "+detail)
# Deliberate audit-event probes do not invoke network/process system calls.
probing=True
for name,operation in [("outside_read",lambda:open(run/"not_an_input.txt","rb")),("network_event",lambda:sys.audit("socket.connect",None,("192.0.2.1",9))),("subprocess_event",lambda:sys.audit("subprocess.Popen",None,[],None,None))]:
    rejected=False
    try: operation()
    except PermissionError: rejected=True
    check("audit_probe_"+name,rejected,"synthetic event rejected before operation")
probing=False
check("fresh_venv",sys.prefix!=sys.base_prefix and not site.ENABLE_USER_SITE,"venv active; user site disabled")
check("no_source_path_injection",str(snapshot/"src") not in sys.path,"src absent from sys.path")
check("no_system_site_packages",all(not Path(p).is_relative_to(base/"Lib/site-packages") for p in sys.path if p),"base global packages absent")
tests=[]
if phase=="stdlib":
    import importlib.util
    modules={}
    for name,relative in [("contracts","harmonization/contracts.py"),("reference_utils","harmonization/reference_utils.py"),("authorization","evaluation/authorization.py"),("build_manifest","evaluation/build_manifest.py")]:
        spec=importlib.util.spec_from_file_location("cleanroom_"+name,snapshot/"src/gene_retrieval"/relative)
        module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module);modules[name]=module
        check("stdlib_import_"+name,True,"imported before NumPy/pytest installation")
    check("no_scientific_packages_yet",importlib.util.find_spec("numpy") is None and importlib.util.find_spec("pytest") is None,"neither dependency installed")
    fasta=scratch/"stdlib_artificial.fa.gz"
    with gzip.open(fasta,"wt",encoding="ascii") as f: f.write(">chr1 artificial\nACGT\nACGT\n")
    check("stdlib_artificial_fasta",modules["reference_utils"].read_reference_segments(fasta,{"chr1":{3:4}})=={("chr1",3):"GTAC"},"literal sequence across lines")
    closed=False
    try: modules["authorization"].require_formal_authorization(scratch, authorization_filename="approval.txt", receipt_filename="receipt.json", environment_variable="SYNTHETIC_EVALUATION_OPT_IN", authorization_scope="SYNTHETIC_EVALUATION")
    except modules["authorization"].AuthorizationError: closed=True
    check("stdlib_authorization_fail_closed",closed,"no authorization inputs supplied")
    closed=False
    try: modules["contracts"].validate_candidate_rows([])
    except modules["contracts"].ContractError: closed=True
    check("stdlib_contract_rejects_empty",closed,"empty artificial input rejected")
    metadata={"phase":phase,"distributions":[]}
else:
    import gene_retrieval,numpy,pytest,tomllib
    installed=Path(gene_retrieval.__file__).resolve()
    check("noneditable_install",installed.is_relative_to(venv) and "site-packages" in installed.parts,"imported fresh venv installation")
    check("exact_numpy",numpy.__version__=="2.5.5",numpy.__version__)
    check("exact_pytest",pytest.__version__=="9.2.0",pytest.__version__)
    project=tomllib.loads((snapshot/"pyproject.toml").read_text(encoding="utf-8"))
    check("metadata_runtime_dependency",project["project"]["dependencies"]==["numpy==2.5.5"],"NumPy sole runtime dependency")
    class Recorder:
        def pytest_runtest_logreport(self,report):
            if report.when=="call" or (report.when in {"setup","teardown"} and report.failed): tests.append({"nodeid":report.nodeid,"outcome":report.outcome})
    result=pytest.main([str(snapshot/"tests/synthetic"),"--rootdir="+str(snapshot),"--confcutdir="+str(snapshot/"tests"),"--import-mode=importlib","--capture=sys","-p","no:cacheprovider","-q"],plugins=[Recorder()])
    check("complete_synthetic_suite",int(result)==0 and bool(tests) and all(t["outcome"]=="passed" for t in tests),str(len(tests))+" cases; no skips permitted")
    inherited=[t for t in tests if t["nodeid"].split("::")[0].split("/")[-1] in {"test_contracts.py","test_ranking.py","test_authorization.py"}]
    check("nine_original_test_functions",len(inherited)==9 and all(t["outcome"]=="passed" for t in inherited),"9 inherited tests with qualified imports")
    metadata={"phase":phase,"python":sys.version,"implementation":sys.implementation.name,"distributions":sorted([(d.metadata["Name"],d.version) for d in importlib.metadata.distributions()]),"isolated":bool(sys.flags.isolated),"bytecode_disabled":bool(sys.dont_write_bytecode),"user_site":site.ENABLE_USER_SITE}
check("no_unexpected_boundary_attempts",not any(not b["probe"] for b in blocked),"only intentional audit probes rejected")
(evidence/(phase+"_results.json")).write_text(json.dumps({"checks":records,"tests":tests,"metadata":metadata,"blocked":blocked},indent=2),encoding="utf-8")
'''

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def tsv(path,rows,columns):
    with path.open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=columns,delimiter='\t',lineterminator='\n');writer.writeheader();writer.writerows(rows)
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--work-dir',required=True,type=Path);args=parser.parse_args()
    root=Path(__file__).resolve().parents[3];run=args.work_dir.resolve()
    if not (root/'pyproject.toml').is_file(): raise ValueError('driver must run from toolkit checkout')
    if run.exists() or run.is_relative_to(root): raise ValueError('work directory must be new and outside repository')
    run.mkdir(parents=True)
    for name in ['snapshot','evidence','scratch','tmp','pip-cache']: (run/name).mkdir()
    evidence=run/'evidence'
    inputs=[root/'pyproject.toml',root/'README.md',root/'environment/requirements-minimal.txt',root/'environment/environment_metadata.md',root/'LICENSE',root/'LICENSE-CC-BY-4.0.txt',root/'LICENSES.md',Path(__file__).resolve()]
    for folder in ['src','tests','schemas','docs']: inputs.extend(p for p in (root/folder).rglob('*') if p.is_file())
    if any(p.is_symlink() or not p.resolve().is_relative_to(root) for p in inputs): raise ValueError('input symlinks forbidden')
    before={}
    for source in sorted(inputs):
        relative=source.relative_to(root).as_posix();dest=run/'snapshot'/relative;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,dest);before[relative]=sha(source)
    tsv(evidence/'VALIDATED_INPUT_SHA256.tsv',[{'relative_path':p,'sha256':h} for p,h in sorted(before.items())],['relative_path','sha256'])
    fingerprint=sha(evidence/'VALIDATED_INPUT_SHA256.tsv');worker=run/'worker.py';worker.write_text(WORKER,encoding='utf-8')
    env={k:v for k,v in os.environ.items() if k.upper() in {'SYSTEMROOT','WINDIR','COMSPEC','PATHEXT','PROCESSOR_ARCHITECTURE','NUMBER_OF_PROCESSORS'}}
    env.update({'TEMP':str(run/'tmp'),'TMP':str(run/'tmp'),'PATH':str(Path(sys.executable).parent)+os.pathsep+str(Path(os.environ['SYSTEMROOT'])/'System32'),'PYTEST_DISABLE_PLUGIN_AUTOLOAD':'1','PYTHONDONTWRITEBYTECODE':'1','PYTHONNOUSERSITE':'1','GENE_RETRIEVAL_TEST_SCRATCH':str(run/'scratch'),'PIP_CONFIG_FILE':os.devnull})
    def execute(arguments,label,cwd=run):
        command=[str(a) for a in arguments]
        command[1:1]=['-X','utf8']
        proc=subprocess.run(command,cwd=cwd,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,encoding='utf-8',errors='replace')
        text=proc.stdout
        for local_path,label_text in [(run,'[clean-room]'),(root,'[repository]'),(Path.home(),'[user-home]')]:
            for pattern in [str(local_path),local_path.as_posix()]:
                text=re.sub(re.escape(pattern),lambda _:label_text,text,flags=re.IGNORECASE)
        (evidence/(label+'.log')).write_text(text,encoding='utf-8');print(label+': exit '+str(proc.returncode),flush=True)
        if proc.returncode:
            print(text[-14000:],flush=True);raise RuntimeError(label+' failed; no PASS may be claimed')
        return text
    execute([sys.executable,'-I','-B','-m','venv','--without-pip',run/'venv'],'create_venv')
    python=run/'venv/Scripts/python.exe'
    execute([python,'-I','-B',worker,run,'stdlib'],'stdlib')
    # Work around this host's restrictive mkdtemp(mode=0700) ACL during setup only.
    setup_prefix='''import sys,tempfile,uuid
from pathlib import Path
run=Path(sys.argv[1])
def inherited_acl_temp(suffix=None,prefix=None,dir=None):
    path=run/"tmp"/((prefix or "pip-")+uuid.uuid4().hex+(suffix or ""));path.mkdir();return str(path)
tempfile.mkdtemp=inherited_acl_temp
'''
    bootstrap=run/'bootstrap.py'
    bootstrap.write_text(setup_prefix+'''wheel=next((Path(sys.base_prefix)/"Lib/ensurepip/_bundled").glob("pip-*.whl"));sys.path.insert(0,str(wheel))
from pip._internal.cli.main import main
raise SystemExit(main(["--isolated","--disable-pip-version-check","install","--no-input","--index-url","https://pypi.org/simple","--cache-dir",str(run/"pip-cache"),"pip==25.0.1","numpy==2.5.5","pytest==9.2.0","setuptools==80.9.0","wheel==0.45.1"]))
''',encoding='utf-8')
    execute([python,'-I','-B',bootstrap,run],'install_dependencies')
    installer=run/'install_package.py'
    installer.write_text(setup_prefix+'''from pip._internal.cli.main import main
raise SystemExit(main(["--isolated","--disable-pip-version-check","install","--no-input","--no-index","--no-deps","--no-build-isolation",str(run/"snapshot")]))
''',encoding='utf-8')
    execute([python,'-I','-B',installer,run],'install_package')
    execute([python,'-I','-B','-m','pip','--disable-pip-version-check','check'],'pip_check')
    execute([python,'-I','-B',worker,run,'suite'],'suite',run/'snapshot')
    execute([python,'-I','-B','-m','gene_retrieval.evaluation.build_manifest','--root',run/'scratch','--output','CLI_SHA256.tsv'],'manifest_cli')
    integrity=[]
    for relative,original in sorted(before.items()):
        after=sha(root/relative);copied=sha(run/'snapshot'/relative)
        integrity.append({'relative_path':relative,'sha256_before':original,'sha256_after':after,'snapshot_sha256_after':copied,'status':'PASS' if original==after==copied else 'FAIL'})
    tsv(evidence/'SOURCE_SHA256_BEFORE_AFTER.tsv',integrity,list(integrity[0]))
    if any(r['status']!='PASS' for r in integrity): raise RuntimeError('source integrity failed')
    records=[]
    for phase in ['stdlib','suite']:
        data=json.loads((evidence/(phase+'_results.json')).read_text(encoding='utf-8'))
        records += [{'phase':phase,**r} for r in data['checks']]
        records += [{'phase':'pytest','check':t['nodeid'],'status':'PASS' if t['outcome']=='passed' else 'FAIL','detail':t['outcome']} for t in data['tests']]
    records += [{'phase':'integrity','check':'all_validation_inputs_unchanged','status':'PASS','detail':str(len(integrity))+' checkout and copied inputs unchanged'},{'phase':'setup','check':'pip_check','status':'PASS','detail':'No broken requirements found'},{'phase':'cli','check':'manifest_explicit_root','status':'PASS','detail':'isolated module invocation succeeded'}]
    tsv(evidence/'CLEANROOM_TEST_RESULTS.tsv',records,['phase','check','status','detail'])
    import platform
    metadata=json.loads((evidence/'suite_results.json').read_text(encoding='utf-8'))['metadata'];metadata.update({'platform':platform.platform(),'machine':platform.machine(),'validated_input_manifest_sha256':fingerprint})
    (evidence/'run_summary.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8')
    print(json.dumps({'result':'PASS','input_files':len(before),'check_records':len(records),'input_fingerprint':fingerprint},indent=2),flush=True)
if __name__=='__main__': main()