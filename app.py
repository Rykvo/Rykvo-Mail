#!/usr/bin/env python3
import base64,hashlib,hmac,html,json,os,re,secrets,ssl,time,threading
from email.header import Header
from http import cookies
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib import request,parse
HOST,PORT="127.0.0.1",8090; ADMIN_PATH="/gly"; USER=os.getenv("MAILPANEL_USER","admin"); PASSWORD=os.getenv("MAILPANEL_PASSWORD","admin123"); STALWART_USER=os.getenv("STALWART_USER","admin"); STALWART_PASSWORD=os.getenv("STALWART_PASSWORD","admin123")
SECRET=os.getenv("MAILPANEL_SECRET","mailpanel-local-secret").encode(); STATE="/var/lib/mailpanel/state.json"; IP=os.getenv("MAILPANEL_PUBLIC_IP","35.212.159.98"); JMAP="http://127.0.0.1:8080/jmap"
JOBS={};JOBS_LOCK=threading.Lock();LOGIN_ATTEMPTS={};LOGIN_LOCK=threading.Lock()
CSS=""":root{--navy:#0b1220;--navy2:#111c31;--primary:#356df3;--primary2:#2558d9;--cyan:#22c7e8;--bg:#f3f6fb;--card:#fff;--text:#14213d;--muted:#6b7a90;--line:#e4eaf3;--danger:#e5484d;--success:#14a673;--warning:#e8a317;--shadow:0 12px 35px rgba(25,45,85,.08)}*{box-sizing:border-box}html{min-height:100%}body{margin:0;min-height:100vh;background:linear-gradient(145deg,#f7f9fd 0,#eef3fa 100%);color:var(--text);font-family:Inter,-apple-system,BlinkMacSystemFont,'Segoe UI','Microsoft YaHei',sans-serif;-webkit-font-smoothing:antialiased}a{color:var(--primary);text-decoration:none}.side{position:fixed;z-index:20;inset:0 auto 0 0;width:244px;background:linear-gradient(180deg,var(--navy) 0%,#101b30 100%);color:#fff;padding:26px 18px;border-right:1px solid rgba(255,255,255,.06)}.brand{display:flex;align-items:center;gap:12px;font-size:20px;font-weight:800;letter-spacing:.2px;padding:2px 10px 28px}.brand svg{width:36px;height:36px;filter:drop-shadow(0 6px 12px rgba(34,199,232,.22))}.nav{display:flex;flex-direction:column;gap:7px}.nav a{position:relative;display:flex;align-items:center;color:#aebbd0;padding:13px 15px;border-radius:11px;font-weight:600;transition:.18s ease}.nav a:hover{background:rgba(255,255,255,.07);color:#fff;transform:translateX(2px)}.nav a.on{background:linear-gradient(100deg,var(--primary),#477ef7);color:#fff;box-shadow:0 8px 20px rgba(53,109,243,.28)}.nav a:last-child{margin-top:18px;color:#94a3b8}.main{margin-left:244px;padding:38px 42px;min-height:100vh}.top{display:flex;justify-content:space-between;align-items:center;margin:0 auto 24px;max-width:1380px}.top h1{margin:0;font-size:30px;letter-spacing:-.5px}.card{max-width:1380px;margin:0 auto 20px;background:rgba(255,255,255,.94);border:1px solid rgba(220,228,240,.95);border-radius:18px;padding:25px;box-shadow:var(--shadow)}.narrow{max-width:820px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:18px}.full{grid-column:1/-1}h2,h3{letter-spacing:-.3px}label{display:block;font-size:13px;font-weight:750;margin-bottom:8px;color:#34435a}input,select,textarea{width:100%;padding:12px 14px;border:1px solid #ccd6e5;border-radius:10px;background:#fbfcfe;color:var(--text);font:inherit;outline:none;transition:.18s}input[type=checkbox]{width:16px;height:16px;padding:0;accent-color:var(--primary)}input:focus,select:focus,textarea:focus{border-color:var(--primary);background:#fff;box-shadow:0 0 0 4px rgba(53,109,243,.1)}textarea{min-height:160px;resize:vertical}.btn,button{display:inline-flex;align-items:center;justify-content:center;border:0;border-radius:10px;background:linear-gradient(135deg,var(--primary),var(--primary2));color:#fff;padding:11px 18px;font-weight:750;cursor:pointer;box-shadow:0 5px 14px rgba(53,109,243,.18);transition:.16s ease}.btn:hover,button:hover{transform:translateY(-1px);filter:brightness(1.04)}button:disabled{opacity:.55;cursor:not-allowed;transform:none}.red{background:linear-gradient(135deg,#ef5358,#d9363e)!important}.gray{background:#64748b!important}.green{background:linear-gradient(135deg,#19b77f,#0b9466)!important}.small{padding:8px 12px;font-size:13px}.actions{display:flex;gap:9px;align-items:center;flex-wrap:wrap}.listbar{display:flex;align-items:center;justify-content:space-between;gap:14px;margin-bottom:18px;flex-wrap:wrap}.list-search{max-width:340px;background:#f8fafc}.pager{display:flex;align-items:center;justify-content:center;gap:12px;width:100%;margin:6px 0 16px;color:var(--muted);font-size:13px}.msg{max-width:1380px;margin:0 auto 18px;padding:13px 16px;border-radius:11px;border:1px solid transparent}.ok{background:#e8fbf3;color:#087452;border-color:#c5f1df}.err{background:#fff0f0;color:#a5242a;border-color:#ffd2d4}.warn{background:#fff7e5;color:#915e00;border-color:#ffe5ab}.muted{font-size:13px;color:var(--muted)}.badge{display:inline-flex;align-items:center;padding:5px 10px;border-radius:999px;font-size:12px;font-weight:700}table{width:100%;border-collapse:separate;border-spacing:0}th,td{padding:15px 12px;border-bottom:1px solid var(--line);text-align:left;vertical-align:middle}th{font-size:12px;text-transform:none;letter-spacing:.25px;color:#78869a;background:#f8fafc}th:first-child{border-radius:10px 0 0 10px}th:last-child{border-radius:0 10px 10px 0}tr:last-child td{border-bottom:0}.dns{font:13px 'Cascadia Code',Consolas,monospace;word-break:break-all}.login-wrap{width:min(440px,calc(100% - 28px));margin:8vh auto}.login-brand{display:flex;align-items:center;justify-content:center;gap:13px;margin-bottom:20px}.login-brand svg{width:52px;height:52px;filter:drop-shadow(0 10px 18px rgba(53,109,243,.25))}.login-brand div{display:flex;flex-direction:column}.login-brand b{font-size:22px}.login-brand span{font-size:12px;color:var(--muted);margin-top:2px}.login{max-width:none;margin:0;padding:34px}.login h1{text-align:left;margin:0 0 26px;font-size:24px}.login button{width:100%;min-height:46px}.settings-radio{display:none}.settings-tabs{display:flex;gap:8px;max-width:820px;margin:0 auto 18px;padding:6px;background:#e8edf5;border-radius:13px}.settings-tabs .tab-label{flex:1;margin:0;padding:11px;text-align:center;border-radius:9px;color:#64748b;cursor:pointer}.settings-panel{display:none}#tab-account:checked~.settings-tabs label[for=tab-account],#tab-panel:checked~.settings-tabs label[for=tab-panel],#tab-cleanup:checked~.settings-tabs label[for=tab-cleanup],#tab-mail:checked~.settings-tabs label[for=tab-mail]{background:#fff;color:var(--primary);box-shadow:0 4px 14px rgba(25,45,85,.1)}#tab-account:checked~#set-account,#tab-panel:checked~#set-panel,#tab-cleanup:checked~#set-cleanup,#tab-mail:checked~#set-mail{display:block}.settings-divider{height:1px;background:var(--line);margin:28px 0}.settings-row{display:flex;justify-content:space-between;align-items:center;padding:14px 0;border-bottom:1px solid var(--line);margin-bottom:16px}.step{display:flex;gap:10px;max-width:1380px;margin:0 auto 18px}.step span{flex:1;background:#e7ecf4;color:#64748b;padding:10px;text-align:center;border-radius:10px}.step .on{background:linear-gradient(135deg,var(--primary),#4f82f8);color:#fff}.modal{display:none;position:fixed;z-index:100;inset:0;background:rgba(7,15,29,.68);padding:5vh 18px;overflow:auto;backdrop-filter:blur(7px)}.modal.open{display:block;animation:fade .15s ease}.modalbox{max-width:900px;margin:auto;background:#fff;border-radius:20px;padding:27px;box-shadow:0 30px 90px rgba(0,0,0,.28);animation:rise .2s ease}.modalbox.narrow{max-width:720px}#web-confirm .modalbox{max-width:420px;padding:22px}#web-confirm .modalhead{margin-bottom:12px;padding-bottom:10px}#web-confirm .confirm-text{margin:15px 0 20px;color:#475569}#web-confirm .actions{justify-content:flex-end}.modalhead{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;padding-bottom:14px;border-bottom:1px solid var(--line)}.modalhead h2{margin:0}.x{background:#eef2f7!important;color:#334155!important;box-shadow:none!important;padding:8px 12px!important}@keyframes fade{from{opacity:0}}@keyframes rise{from{opacity:0;transform:translateY(10px) scale(.985)}}@media(max-width:820px){.side{position:static;width:auto;padding:14px}.brand{padding:4px 8px 14px}.nav{flex-direction:row;overflow:auto}.nav a{white-space:nowrap}.nav a:last-child{margin:0}.main{margin:0;padding:22px 14px}.grid{grid-template-columns:1fr}.full{grid-column:1}.card{padding:18px;overflow-x:auto}.top h1{font-size:25px}.modal{padding:16px 10px}.modalbox{padding:19px}}
/* Rykvo Text visual system */
:root{--primary:#0d9488;--primary2:#14b8a6;--bg:#f5f7fb;--text:#172033;--muted:#718096;--line:#e5eaf1;--shadow:0 8px 30px rgba(15,23,42,.06)}
body{background:#f5f7fb;color:var(--text)}
.side{width:220px;background:rgba(255,255,255,.98);color:var(--text);padding:24px 16px;border-right:1px solid var(--line);box-shadow:4px 0 18px rgba(15,23,42,.025)}
.brand{color:#162033;padding:2px 10px 26px;font-size:19px}.brand svg{width:34px;height:34px;filter:none}
.nav{gap:6px}.nav a{display:flex;align-items:center;gap:11px;color:#64748b;padding:12px 14px;border:1px solid transparent;border-radius:11px;font-weight:650;transform:none}
.nav a:hover{background:#f6faf9;color:#0f766e;transform:none}.nav a.on{background:linear-gradient(135deg,rgba(20,184,166,.14),rgba(6,182,212,.07));border-color:rgba(13,148,136,.12);color:#087f78;box-shadow:none}.nav a:last-child{color:#94a3b8}
.nav-ico{width:20px;text-align:center;font-size:16px}.main{margin-left:220px;padding:30px 36px}.top{max-width:1240px;margin:0 0 20px}.top h1{font-size:28px}
.card{max-width:1240px;margin:0 0 18px;background:#fff;border:1px solid var(--line);border-radius:16px;padding:24px;box-shadow:var(--shadow)}
.msg{max-width:1240px;margin:0 0 16px}.list-search{background:#fff}.step{max-width:1240px;margin-left:0}.settings-tabs{margin-left:0}
input,select,textarea{border-color:#d7deea;background:#fff}input:focus,select:focus,textarea:focus{border-color:#2bb8ad;box-shadow:0 0 0 3px rgba(20,184,166,.11)}
.btn,button{background:linear-gradient(135deg,var(--primary2),var(--primary));box-shadow:0 5px 14px rgba(13,148,136,.17)}.btn:hover,button:hover{box-shadow:0 7px 18px rgba(13,148,136,.21)}
.red{background:linear-gradient(135deg,#f45b61,#e33b43)!important}.green{background:linear-gradient(135deg,#18b98b,#07966e)!important}
th{background:#f8fafc}.settings-tabs{background:#e9eef4}.modal{background:rgba(15,23,42,.48);backdrop-filter:blur(4px)}.modalbox{border-radius:18px;box-shadow:0 28px 80px rgba(15,23,42,.24)}#web-confirm.open{display:flex;align-items:center;justify-content:center;padding:18px}#web-confirm .modalbox{margin:0;width:min(440px,calc(100vw - 36px));max-width:none!important;padding:28px!important}#web-confirm .confirm-head{padding:0 0 15px!important;margin:0 0 16px!important}#web-confirm .confirm-text{font-size:15px;line-height:1.7;margin:0 0 24px!important;white-space:normal}#web-confirm .actions{gap:10px}
.login-wrap{min-height:100vh;margin:0 auto!important;display:flex;flex-direction:column;justify-content:center}.login-brand svg{filter:none}.login{border-radius:18px}.login h1{text-align:center!important}.toast{position:fixed!important;z-index:9999!important;left:50%!important;top:50%!important;transform:translate(-50%,-50%)!important;width:max-content!important;max-width:420px!important;margin:0!important;padding:12px 18px!important;box-shadow:0 14px 40px rgba(15,23,42,.2)!important;text-align:center!important;animation:toastIn .18s ease}@keyframes toastIn{from{opacity:0;transform:translate(-50%,-46%)}}
/* unified controls and spacing */
.top,.card,.msg,.step{width:100%}.card{padding:24px}.listbar{min-height:46px;margin-bottom:18px}.listbar>.actions,.listbar>div.actions{gap:10px}.listbar button.small{min-height:40px;padding:0 16px;font-size:14px}.listbar button{height:40px}.listbar+.pager{margin:-4px 0 14px}.listbar .gray{background:linear-gradient(135deg,var(--primary2),var(--primary))!important;box-shadow:0 5px 14px rgba(13,148,136,.17)!important}
input,select{height:44px;padding:0 14px;border-radius:10px}textarea{height:auto;padding:13px 14px;border-radius:10px}
.btn,button{min-height:40px;padding:0 16px;border-radius:9px;font-size:14px;font-weight:700;line-height:1;white-space:nowrap}.small{min-height:36px;padding:0 13px;font-size:13px}.x{min-height:36px!important;padding:0 13px!important}
.actions{gap:9px}.actions form{margin:0}.list-search{height:44px}.domain-filter{height:44px}
table{table-layout:auto}th{height:52px;padding:12px 14px}td{height:58px;padding:12px 14px}.badge{min-height:28px;padding:5px 11px}
.modalhead{min-height:48px}.modalhead h2{font-size:22px}.modalbox .actions:last-child{align-items:center}
.settings-tabs{min-height:48px}.settings-tabs .tab-label{display:flex;align-items:center;justify-content:center}.bulk-progress{display:none;margin-top:18px;padding:16px;background:#f6faf9;border:1px solid #d8eee9;border-radius:12px}.progress-track{height:12px;background:#dfe8e7;border-radius:999px;overflow:hidden}.progress-fill{height:100%;width:0;background:linear-gradient(90deg,var(--primary2),var(--primary));transition:width .25s}.progress-label{display:flex;justify-content:space-between;margin-top:9px;font-size:13px;color:var(--muted)}@media(max-width:820px){.side{width:auto}.main{margin-left:0;padding:21px 13px}}
"""
ICON="""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><defs><linearGradient id="g" x1="8" y1="5" x2="56" y2="59" gradientUnits="userSpaceOnUse"><stop stop-color="#477ef7"/><stop offset="1" stop-color="#20c7e7"/></linearGradient></defs><rect x="3" y="3" width="58" height="58" rx="17" fill="url(#g)"/><path d="M17 21h30a4 4 0 0 1 4 4v18a4 4 0 0 1-4 4H17a4 4 0 0 1-4-4V25a4 4 0 0 1 4-4Z" fill="none" stroke="white" stroke-width="4"/><path d="m15 25 17 13 17-13" fill="none" stroke="white" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/><path d="M23 17h11c5 0 8 3 8 7" fill="none" stroke="white" stroke-width="4" stroke-linecap="round"/></svg>"""
def e(v):return html.escape(str(v or ""),quote=True)
def friendly_error(x):
 t=str(x)
 if t.startswith('密码至少') or t.startswith('用户名格式') or t.startswith('两次输入') or t.startswith('管理员账号'):return t
 if 'Password is too weak' in t:return '密码过于简单或属于常用密码。请使用至少 12 位，并组合不常见单词、数字和符号。'
 if 'primaryKeyViolation' in t:return '该用户名或域名已经存在。'
 if 'objectIsLinked' in t:return '该项目仍被其他数据使用，请先删除关联用户后再操作。'
 return '操作没有完成，请检查填写内容后重试。'
def password_secret(p):
 salt=os.urandom(16);raw=hashlib.sha512(p.encode()+salt).digest()+salt
 return '{SSHA512}'+base64.b64encode(raw).decode()
def seal(v):
 nonce=os.urandom(16);key=hashlib.sha256(SECRET+b':mail-passwords').digest();raw=v.encode();out=bytes(c^hmac.new(key,nonce+(i//32).to_bytes(4,'big'),hashlib.sha256).digest()[i%32] for i,c in enumerate(raw));return base64.urlsafe_b64encode(nonce+out).decode()
def unseal(v):
 try:
  z=base64.urlsafe_b64decode(v);nonce,raw=z[:16],z[16:];key=hashlib.sha256(SECRET+b':mail-passwords').digest();return bytes(c^hmac.new(key,nonce+(i//32).to_bytes(4,'big'),hashlib.sha256).digest()[i%32] for i,c in enumerate(raw)).decode()
 except:return ''
def state():
 try:
  with open(STATE,encoding="utf8") as f:s=json.load(f)
  s.setdefault("domains",{});return s
 except:return {"domains":{},"retention_days":30}
def save(s):
 os.makedirs(os.path.dirname(STATE),exist_ok=True)
 with open(STATE,"w",encoding="utf8") as f:json.dump(s,f,ensure_ascii=False,indent=2)
 os.chmod(STATE,0o600)
def admin_creds():
 s=state();return s.get("admin_user",USER),s.get("admin_password",PASSWORD)
def token():
 p=f"{int(time.time())+86400}:{secrets.token_hex(8)}".encode();return base64.urlsafe_b64encode(p+b"."+hmac.new(SECRET,p,hashlib.sha256).hexdigest().encode()).decode()
def valid(v):
 try:
  p,s=base64.urlsafe_b64decode(v).rsplit(b".",1);return hmac.compare_digest(s,hmac.new(SECRET,p,hashlib.sha256).hexdigest().encode()) and int(p.split(b":")[0])>time.time()
 except:return False
def csrf(v):return hmac.new(SECRET,("csrf:"+v).encode(),hashlib.sha256).hexdigest()
def call(calls):
 body={"using":["urn:ietf:params:jmap:core","urn:stalwart:jmap"],"methodCalls":calls};auth=base64.b64encode(f"{STALWART_USER}:{STALWART_PASSWORD}".encode()).decode()
 req=request.Request(JMAP,data=json.dumps(body).encode(),headers={"Content-Type":"application/json","Authorization":"Basic "+auth})
 with request.urlopen(req,timeout=35) as r:o=json.loads(r.read())
 bad=[x for x in o.get("methodResponses",[]) if x[0]=="error" or (x[0].endswith("/set") and (x[1].get("notCreated") or x[1].get("notUpdated") or x[1].get("notDestroyed")))]
 if bad:raise RuntimeError(json.dumps(bad,ensure_ascii=False))
 return o
def call_raw(calls):
 body={"using":["urn:ietf:params:jmap:core","urn:stalwart:jmap"],"methodCalls":calls};auth=base64.b64encode(f"{STALWART_USER}:{STALWART_PASSWORD}".encode()).decode()
 req=request.Request(JMAP,data=json.dumps(body).encode(),headers={"Content-Type":"application/json","Authorization":"Basic "+auth})
 with request.urlopen(req,timeout=35) as r:return json.loads(r.read())
def sync_sender_name(email_addr,display_name):
 """同步 JMAP 发件身份名称；SMTP 客户端读取该身份时会显示此名称。"""
 try:
  body={"using":["urn:ietf:params:jmap:core","urn:ietf:params:jmap:mail","urn:ietf:params:jmap:submission"],"methodCalls":[["Identity/query",{},"q"]]}
  login=f"{email_addr}%{STALWART_USER}";auth=base64.b64encode(f"{login}:{STALWART_PASSWORD}".encode()).decode()
  def ucall(method_calls):
   body["methodCalls"]=method_calls;req=request.Request(JMAP,data=json.dumps(body).encode(),headers={"Content-Type":"application/json","Authorization":"Basic "+auth})
   with request.urlopen(req,timeout=35) as r:return json.loads(r.read())
  q=resp(ucall([["Identity/query",{},"q"]]),"Identity/query");ids=q.get("ids",[])
  if ids:ucall([["Identity/set",{"update":{str(ids[0]):{"name":display_name}}},"s"]])
  else:ucall([["Identity/set",{"create":{"new":{"name":display_name,"email":email_addr,"replyTo":[],"bcc":[],"textSignature":"","htmlSignature":""}}},"s"]])
 except Exception:pass
def rebuild_sender_name_script(restart=True):
 """Rebuild the trusted SMTP Sieve map so every authenticated sender gets its saved display name."""
 try:
  ds={str(x.get('id')):x.get('name','') for x in domains()};st=state();names=st.get('display_names',{})
  lines=['require ["variables", "editheader"];']
  for u in users():
   uid=str(u.get('id'));addr=f"{u.get('name')}@{ds.get(str(u.get('domainId')),'')}";name=str(names.get(uid,u.get('name',''))).strip()
   if not name or '@' not in addr:continue
   qaddr=addr.replace('\\','\\\\').replace('"','\\"');qfrom=f"{Header(name,'utf-8').encode()} <{addr}>".replace('\\','\\\\').replace('"','\\"')
   lines+= [f'if string :is "${{env.authenticated_as}}" "{qaddr}" {{', '  deleteheader "From";', f'  addheader "From" "{qfrom}";', '}']
  contents='\n'.join(lines);typ='x:SieveSystemScript';q=resp(call([[typ+'/query',{},'q']]),typ+'/query');ids=q.get('ids',[])
  objs=resp(call([[typ+'/get',{'ids':ids},'g']]),typ+'/get').get('list',[]);old=next((x for x in objs if x.get('name')=='rykvo-sender-name'),None)
  if old:call([[typ+'/set',{'update':{str(old['id']):{'contents':contents,'isActive':True}}},'s']])
  else:call([[typ+'/set',{'create':{'new':{'name':'rykvo-sender-name','description':'Rykvo sender display names','isActive':True,'contents':contents}}},'s']])
  call([['x:MtaStageData/set',{'update':{'singleton':{'script':{'match':{'0':{'if':'!is_empty(authenticated_as)','then':"'rykvo-sender-name'"}},'else':'false'}}}},'s']])
  if restart:
   def notify_reload():
    try:
     with open('/var/lib/mailpanel/reload-stalwart','w') as f:f.write(str(time.time()))
    except Exception as ex:print('sender-name reload:',ex,flush=True)
   threading.Timer(.8,notify_reload).start()
 except Exception as ex:print('sender-name sync:',ex,flush=True)
def resp(o,n):
 for x in o.get("methodResponses",[]):
  if x[0]==n:return x[1]
 return {}
def domains():
 o=call([["x:Domain/query",{},"q"],["x:Domain/get",{"#ids":{"resultOf":"q","name":"x:Domain/query","path":"/ids"}},"g"]]);return [x for x in resp(o,"x:Domain/get").get("list",[]) if x.get('name')!='mailpanel-placeholder.example.com']
def domain(i):
 a=resp(call([["x:Domain/get",{"ids":[i]},"g"]]),"x:Domain/get").get("list",[]);return a[0] if a else None
def add_domain(n):
 x={"name":n,"aliases":{},"certificateManagement":{"@type":"Manual"},"dkimManagement":{"@type":"Automatic"},"dnsManagement":{"@type":"Manual"},"subAddressing":{"@type":"Enabled"}}
 did=resp(call([["x:Domain/set",{"create":{"new":x}},"s"]]),"x:Domain/set")["created"]["new"]["id"]
 try:
  sys=resp(call([["x:SystemSettings/get",{"ids":["singleton"]},"g"]]),"x:SystemSettings/get").get('list',[{}])[0]
  old=sys.get('defaultDomainId');old_obj=domain(old) if old else None
  if old_obj and old_obj.get('name')=='mailpanel-placeholder.example.com':
   call([["x:SystemSettings/set",{"update":{"singleton":{"defaultDomainId":did,"defaultHostname":"mail."+n}}},"s"]]);call([["x:Domain/set",{"destroy":[old]},"d"]])
 except Exception:pass
 return did
def delete_domain_cascade(i):
 d=domain(i)
 if not d:return
 linked=[str(x.get('id')) for x in users() if str(x.get('domainId'))==str(i)]
 if linked:
  destroy_accounts(linked)
  st=state();dn=st.setdefault('display_names',{});vault=st.setdefault('password_vault',{})
  [dn.pop(x,None) for x in linked];[vault.pop(x,None) for x in linked];save(st)
  schedule_purge()
 sys=resp(call([["x:SystemSettings/get",{"ids":["singleton"]},"g"]]),"x:SystemSettings/get").get('list',[{}])[0]
 if sys.get('defaultDomainId')==i:
  others=domains();other=next((x for x in others if str(x.get('id'))!=str(i)),None)
  if not other:
   raw=call([["x:Domain/query",{},"q"],["x:Domain/get",{"#ids":{"resultOf":"q","name":"x:Domain/query","path":"/ids"}},"g"]]);internal=next((x for x in resp(raw,"x:Domain/get").get('list',[]) if x.get('name')=='mailpanel-placeholder.example.com'),None)
   if internal:oid=internal['id']
   else:
    x={"name":"mailpanel-placeholder.example.com","aliases":{},"certificateManagement":{"@type":"Manual"},"dkimManagement":{"@type":"Manual"},"dnsManagement":{"@type":"Manual"},"subAddressing":{"@type":"Enabled"}}
    oid=resp(call([["x:Domain/set",{"create":{"internal":x}},"c"]]),"x:Domain/set")["created"]["internal"]["id"]
  else:oid=other['id']
  call([["x:SystemSettings/set",{"update":{"singleton":{"defaultDomainId":oid,"defaultHostname":"mail.mailpanel-placeholder.example.com"}}},"s"]])
 o=call([["x:DkimSignature/query",{},"q"],["x:DkimSignature/get",{"#ids":{"resultOf":"q","name":"x:DkimSignature/query","path":"/ids"}},"g"]]);ids=[x['id'] for x in resp(o,"x:DkimSignature/get").get('list',[]) if str(x.get('domainId'))==str(i)]
 if ids:call([["x:DkimSignature/set",{"destroy":ids},"d"]])
 call([["x:Domain/set",{"destroy":[i]},"x"]])
def users():
 ids=[];pos=0
 while True:
  q=resp(call([["x:Account/query",{"position":pos,"limit":200},"q"]]),"x:Account/query");part=q.get('ids',[]);ids.extend(part)
  if not part or len(part)<200:break
  pos+=len(part)
 out=[]
 for n in range(0,len(ids),50):out.extend(resp(call([["x:Account/get",{"ids":ids[n:n+50]},"g"]]),"x:Account/get").get("list",[]))
 return [x for x in out if x.get("@type")=="User" and (x.get("roles")or{}).get("@type")!="Admin"]
def user_obj(n,d,p,q,display=""):
 return {"@type":"User","aliases":{},"credentials":{"0":{"@type":"Password","secret":password_secret(p)}},"domainId":d,"encryptionAtRest":{"@type":"Disabled"},"memberGroupIds":{},"name":n,"description":display or n,"permissions":{"@type":"Inherit"},"quotas":{"maxDiskQuota":int(q)*1048576},"roles":{"@type":"User"}}
def add_user(n,d,p,q,display=""):
 x=user_obj(n,d,p,q,display)
 return resp(call([["x:Account/set",{"create":{"new":x}},"s"]]),"x:Account/set")["created"]["new"]["id"]
def update_user(i,p,q,display=""):
 x={"quotas":{"maxDiskQuota":int(q)*1048576},"description":display}
 if p:x["credentials"]={"0":{"@type":"Password","secret":password_secret(p)}}
 call([["x:Account/set",{"update":{i:x}},"s"]])
def schedule_purge(delay=60):
 due=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime(time.time()+delay));creates={}
 for n,t in enumerate(("purgeAccounts","purgeData","purgeBlob")):creates[str(n)]={"@type":"StoreMaintenance","maintenanceType":t,"status":{"@type":"Pending","due":due}}
 call([["x:Task/set",{"create":creates},"p"]])
def destroy_accounts(ids):
 ids=[str(x) for x in ids];done=[];failed=[]
 def run(part):
  if not part:return
  try:
   r=resp(call([["x:Account/set",{"destroy":part},"s"]]),"x:Account/set")
   done.extend(str(x) for x in r.get("destroyed",[]))
  except Exception:
   if len(part)==1:failed.extend(part)
   else:
    m=len(part)//2;run(part[:m]);run(part[m:])
 for n in range(0,len(ids),25):run(ids[n:n+25])
 return done,failed
def delete_worker(jid,ids):
 done=[];failed=[];processed=0
 for n in range(0,len(ids),25):
  part=[str(x) for x in ids[n:n+25]]
  try:
   x=resp(call_raw([["x:Account/set",{"destroy":part},"s"]]),"x:Account/set")
   destroyed=[str(i) for i in x.get('destroyed',[])];nd=x.get('notDestroyed',{})
   # 已不存在的账号也视为删除完成，避免旧查询结果拖慢任务。
   gone=[str(i) for i,v in nd.items() if v.get('type')=='notFound']
   retry=[str(i) for i in part if str(i) not in destroyed and str(i) not in gone]
   done.extend(destroyed+gone)
   for uid in retry:
    ok=False
    for attempt in range(2):
     d,f=destroy_accounts([uid])
     if d:done.extend(d);ok=True;break
     time.sleep(.15)
    if not ok:failed.append(uid)
  except Exception:
   failed.extend(part)
  processed+=len(part)
  with JOBS_LOCK:JOBS[jid].update(done=processed,deleted=len(done),failed=len(failed))
 if done:
  try:schedule_purge()
  except:pass
 st=state();dn=st.setdefault('display_names',{});vault=st.setdefault('password_vault',{})
 for uid in done:dn.pop(str(uid),None);vault.pop(str(uid),None)
 save(st)
 with JOBS_LOCK:JOBS[jid].update(finished=True,done=len(ids),deleted=len(done),failed=len(failed))
 rebuild_sender_name_script()
def bulk_worker(jid,domain_id,raw):
 lines=[(n,x.strip()) for n,x in enumerate(raw.splitlines(),1) if x.strip()];valid=[];errors=[]
 for no,line in lines:
  x=[z.strip() for z in line.split('----')]
  try:
   if len(x)!=4 or not all(x):raise ValueError('格式错误')
   mailbox=x[1].split('@')[0].lower()
   if not re.fullmatch(r'[a-z0-9][a-z0-9._+-]{0,63}',mailbox):raise ValueError('邮箱账号错误')
   valid.append((no,x[0],mailbox,x[2],int(x[3])))
  except Exception as ex:errors.append(f'第{no}行：{ex}')
 total=len(lines);done=len(errors);made=0
 with JOBS_LOCK:JOBS[jid].update(total=total,done=done,made=0,errors=errors[:20])
 for off in range(0,len(valid),25):
  chunk=valid[off:off+25];creates={f'u{k}':user_obj(v[2],domain_id,v[3],v[4],v[1]) for k,v in enumerate(chunk)}
  try:
   created=resp(call([["x:Account/set",{"create":creates},"b"]]),"x:Account/set").get('created',{});st=state();names=st.setdefault('display_names',{});vault=st.setdefault('password_vault',{})
   for k,v in enumerate(chunk):
    obj=created.get(f'u{k}')
    if obj:
     uid=str(obj['id']);names[uid]=v[1];vault[uid]=seal(v[3]);made+=1
    else:errors.append(f'第{v[0]}行：创建失败')
   save(st)
  except Exception as ex:errors.append('批次失败：'+friendly_error(ex))
  done+=len(chunk)
  with JOBS_LOCK:JOBS[jid].update(done=min(done,total),made=made,errors=errors[:20])
 with JOBS_LOCK:JOBS[jid].update(done=total,made=made,finished=True,errors=errors[:20])
 rebuild_sender_name_script()
def doh(n,t):
 req=request.Request("https://cloudflare-dns.com/dns-query?"+parse.urlencode({"name":n,"type":t}),headers={"Accept":"application/dns-json"})
 with request.urlopen(req,timeout=12,context=ssl.create_default_context()) as r:o=json.loads(r.read())
 return [str(a.get("data","")).strip('"') for a in o.get("Answer",[])]
def checks(n,z):
 h="mail."+n;out=[]
 def ck(label,fn,vals):out.append((label,fn(vals),", ".join(vals) or "未解析"))
 try:v=doh(h,"A");ck("A 记录",lambda x:IP in x,v)
 except:out.append(("A 记录",False,"查询失败"))
 try:v=doh(n,"MX");ck("MX 记录",lambda x:any(y.lower().rstrip('.').endswith(h) for y in x),v)
 except:out.append(("MX 记录",False,"查询失败"))
 try:v=doh(n,"TXT");ck("SPF 记录",lambda x:any("v=spf1" in y.lower() for y in x),v)
 except:out.append(("SPF 记录",False,"查询失败"))
 try:v=doh("_dmarc."+n,"TXT");ck("DMARC 记录",lambda x:any("v=dmarc1" in y.lower() for y in x),v)
 except:out.append(("DMARC 记录",False,"查询失败"))
 for sel in sorted(set(re.findall(r"(?im)^([a-z0-9_-]+)\._domainkey.*?TXT",z)))[:4]:
  try:v=doh(f"{sel}._domainkey.{n}","TXT");ck("DKIM "+sel,lambda x:any("p=" in y for y in x),v)
  except:out.append(("DKIM "+sel,False,"查询失败"))
 return out
def request_mail_certificate(d):
 o=call([["x:AcmeProvider/query",{},"q"],["x:AcmeProvider/get",{"#ids":{"resultOf":"q","name":"x:AcmeProvider/query","path":"/ids"}},"g"]]);providers=resp(o,"x:AcmeProvider/get").get('list',[])
 if providers:aid=providers[0]['id']
 else:
  obj={'challengeType':'TlsAlpn01','contact':{'postmaster@'+d['name']:True},'renewBefore':'R23','maxRetries':10,'reuseKey':False};aid=resp(call([["x:AcmeProvider/set",{"create":{"letsencrypt":obj}},"s"]]),"x:AcmeProvider/set")['created']['letsencrypt']['id']
 cm={'@type':'Automatic','acmeProviderId':aid,'subjectAlternativeNames':{'mail':True}}
 call([["x:Domain/set",{"update":{d['id']:{'certificateManagement':cm}}},"s"]]);due=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime());task={'@type':'AcmeRenewal','domainId':d['id'],'status':{'@type':'Pending','due':due}};call([["x:Task/set",{'create':{'renew':task}},'t']]);s=state();s.setdefault('mail_certs',{})[d['name']]={'requested':int(time.time()),'status':'申请中'};save(s)
def request_panel_certificate(name):
 if not re.fullmatch(r"(?=.{4,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}",name):raise ValueError('后台域名格式不正确')
 with open('/var/lib/mailpanel/cert-request','w',encoding='utf8') as f:f.write(name+'\n')
def cleanup_now(days):
 current=resp(call([["x:DataRetention/get",{"ids":["singleton"]},"g"]]),"x:DataRetention/get").get("list",[{}])[0]
 ms=max(1,max(0,int(days))*86400000);minute=(time.gmtime().tm_min+1)%60
 temporary={"expungeTrashAfter":ms,"expungeSubmissionsAfter":ms,"expungeShareNotifyAfter":ms,"expungeSchedulingInboxAfter":ms,"holdMtaReportsFor":ms,"holdTracesFor":ms,"holdMetricsFor":ms,"archiveDeletedItemsFor":ms,"archiveDeletedAccountsFor":ms,"expungeSchedule":{"@type":"Hourly","minute":minute}}
 call([["x:DataRetention/set",{"update":{"singleton":temporary}},"r"]])
 due=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime());creates={}
 for n,t in enumerate(("purgeAccounts","purgeData","purgeBlob")):creates[str(n)]={"@type":"StoreMaintenance","maintenanceType":t,"status":{"@type":"Pending","due":due}}
 call([["x:Task/set",{"create":creates},"t"]])
 def restore():
  time.sleep(120);keep={k:v for k,v in current.items() if k not in ('id','@type')}
  try:call([["x:DataRetention/set",{"update":{"singleton":keep}},"r"]])
  except:pass
 threading.Thread(target=restore,daemon=True).start()
SCRIPT="""<script>function modal(id){document.getElementById(id).classList.add('open')}function closeModal(el){el.closest('.modal').classList.remove('open')}function ask(ev,text){ev.preventDefault();let f=ev.target,m=document.getElementById('web-confirm');m.querySelector('.confirm-text').innerText=text;m._form=f;modal('web-confirm');return false}function toggleAll(x){document.querySelectorAll('input[form=batch][name=ids]').forEach(i=>i.checked=x.checked)}function toggleForm(id,x){document.querySelectorAll(`input[form=${id}][name=ids]`).forEach(i=>i.checked=x.checked)}function domainDeleteAsk(ev){let n=document.querySelectorAll('input[form=domainbatch][name=ids]:checked').length;return ask(ev,n?`删除选中的 ${n} 个域名？`:'未勾选域名，将删除全部域名。')}function deleteAsk(ev){let n=document.querySelectorAll('input[form=batch][name=ids]:checked').length;return ask(ev,n?`删除选中的 ${n} 个用户？`:'未勾选用户，将删除全部用户。')}async function startBulk(ev){ev.preventDefault();let f=ev.target,b=document.getElementById("bulk-start"),box=document.getElementById("bulk-progress");b.disabled=true;b.innerText="创建中";box.style.display="block";document.getElementById("bulk-fill").style.width="0%";let r=await fetch(f.action,{method:"POST",headers:{"Content-Type":"application/x-www-form-urlencoded"},body:new URLSearchParams(new FormData(f))});let j=await r.json();if(!r.ok){b.disabled=false;b.innerText="开始创建";return false}pollBulk(j.id);return false}async function pollBulk(id){let r=await fetch("/api/users/bulk/status?id="+encodeURIComponent(id)),j=await r.json(),total=j.total||0,done=j.done||0,pct=total?Math.round(done*100/total):0;document.getElementById("bulk-fill").style.width=pct+"%";document.getElementById("bulk-count").innerText=done+" / "+total;document.getElementById("bulk-percent").innerText=pct+"%";if(j.finished){document.getElementById("bulk-start").disabled=false;document.getElementById("bulk-start").innerText="创建完成";setTimeout(()=>location.href="/users?msg="+encodeURIComponent("成功创建 "+j.made+" 个用户"),700)}else setTimeout(()=>pollBulk(id),700)}let exportSelected=[];function openExport(){exportSelected=[...document.querySelectorAll("input[form=batch][name=ids]:checked")].map(x=>x.value);document.getElementById("export-domain").value="";updateExport();modal("export-user")}function updateExport(){let d=document.getElementById("export-domain").value,a=(window.exportRecords||[]).filter(x=>(!exportSelected.length||exportSelected.includes(x.id))&&(!d||x.domain==d));document.getElementById("export-text").value=a.map(x=>x.line).join("\\n")}async function copyExport(){await navigator.clipboard.writeText(document.getElementById("export-text").value)}function downloadExport(){let b=new Blob(["\\ufeff"+document.getElementById("export-text").value],{type:"text/plain;charset=utf-8"}),a=document.createElement("a");a.href=URL.createObjectURL(b);a.download="rykvo-users.txt";a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000)}function confirmSubmit(){let m=document.getElementById('web-confirm'),f=m._form;closeModal(m.querySelector('.x'));if(!f)return;if(f.action.endsWith('/users/delete'))startDelete(f);else f.submit()}async function startDelete(f){modal('delete-progress');let r=await fetch('/api/users/delete/start',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:new URLSearchParams(new FormData(f))}),j=await r.json();if(!r.ok){location.href='/users?err='+encodeURIComponent('删除失败');return}pollDelete(j.id)}async function pollDelete(id){let r=await fetch('/api/users/delete/status?id='+encodeURIComponent(id)),j=await r.json(),total=j.total||0,done=j.done||0,pct=total?Math.round(done*100/total):100;document.getElementById('delete-fill').style.width=pct+'%';document.getElementById('delete-count').innerText=done+' / '+total;document.getElementById('delete-percent').innerText=pct+'%';if(j.finished){setTimeout(()=>location.href='/users?msg='+encodeURIComponent('已删除 '+j.deleted+' 个用户'+(j.failed?'，'+j.failed+' 个未删除':'')),500)}else setTimeout(()=>pollDelete(id),500)}async function cp(el){await navigator.clipboard.writeText(el.dataset.copy||el.value||el.innerText);let old=el.title;el.title='已复制';setTimeout(()=>el.title=old,1200)}async function verifyDns(ev,id){ev.preventDefault();let f=ev.target,b=f.querySelector('button');b.disabled=true;b.innerText='检测中…';for(let n=0;n<4;n++){let x=document.getElementById('dnsst-'+id+'-'+n);x.innerHTML='<span style=\"display:inline-block;animation:spin .8s linear infinite\">◌</span> 检测中'}try{let r=await fetch('/api/domains/verify',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:new URLSearchParams(new FormData(f))});let j=await r.json();j.checks.slice(0,4).forEach((v,n)=>{let x=document.getElementById('dnsst-'+id+'-'+n);x.innerHTML=v.ok?'✅ <b style=\"color:#059669\">已通过</b>':'❌ <b style=\"color:#dc2626\">未通过</b>';x.title=v.actual});let ds=document.getElementById('domainst-'+id);if(j.ok){b.innerText='全部通过';ds.className='badge ok';ds.innerText='检测通过'}else{b.innerText='重新检测';ds.className='badge warn';ds.innerText='待检测'}}catch(e){b.innerText='检测失败'}b.disabled=false;return false}function initList(){let t=document.querySelector('.list-table'),q=document.querySelector('.list-search'),p=document.querySelector('.pager'),d=document.querySelector('.domain-filter');if(!t||!q||!p)return;let all=[...t.querySelectorAll('tr')].slice(1),page=1,size=10;function draw(){let s=q.value.trim().toLowerCase(),dv=d?d.value:'',rows=all.filter(r=>r.innerText.toLowerCase().includes(s)&&(!dv||r.dataset.domain==dv)),pages=Math.max(1,Math.ceil(rows.length/size));page=Math.min(page,pages);all.forEach(r=>r.style.display='none');rows.slice((page-1)*size,page*size).forEach(r=>r.style.display='');p.style.display='flex';p.innerHTML=`<button class=\"x small\" ${page<=1?'disabled':''} onclick=\"listPage(-1)\">上一页</button><span>${page} / ${pages}</span><button class=\"x small\" ${page>=pages?'disabled':''} onclick=\"listPage(1)\">下一页</button>`;window.listPage=n=>{page+=n;draw()}}q.addEventListener('input',()=>{page=1;draw()});if(d)d.addEventListener('change',()=>{page=1;draw()});draw()}document.addEventListener('click',e=>{if(e.target.classList.contains('modal')&&!e.target.classList.contains('locked'))e.target.classList.remove('open')});initList()</script><div class=modal id=web-confirm><div class='modalbox narrow'><div class='modalhead confirm-head'><h2>确认操作</h2></div><p class=confirm-text></p><div class=actions><button type=button class=red onclick=confirmSubmit()>确认</button><button type=button class='x' onclick=closeModal(this)>取消</button></div></div></div><style>@keyframes spin{to{transform:rotate(360deg)}}</style>"""
def layout(title,body,on="domains"):
 it=[("domains","✉","邮局域名","/domains"),("users","♙","用户管理","/users"),("settings","⚙","系统设置","/settings")];nav="".join(f"<a data-nav class='{'on' if on==k else ''}' href='{u}'><span class=nav-ico>{i}</span>{t}</a>" for k,i,t,u in it)
 return f"<!doctype html><html lang=zh-CN><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'><link rel=icon type='image/svg+xml' href='/favicon.svg'><meta name=theme-color content='#f5f7fb'><title>Rykvo 邮局</title><style>{CSS}</style><body><aside class=side><div class=brand>{ICON} <span>Rykvo 邮局</span></div><nav class=nav>{nav}<a href=/logout>退出登录</a></nav></aside><main class=main><div class=top><h1>{e(title)}</h1></div>{body}</main><script>history.replaceState(null,'','{ADMIN_PATH}');setTimeout(()=>document.querySelectorAll('.toast').forEach(x=>x.remove()),2200)</script></body></html>"
def note(q):
 x=parse.parse_qs(q);return (f"<div class='msg toast ok'>{e(x['msg'][0])}</div>" if 'msg'in x else "")+(f"<div class='msg toast err'>{e(x['err'][0])}</div>" if 'err'in x else "")
class H(BaseHTTPRequestHandler):
 def log_message(self,*a):pass
 def security_headers(self):
  self.send_header("X-Content-Type-Options","nosniff");self.send_header("X-Frame-Options","DENY");self.send_header("Referrer-Policy","no-referrer");self.send_header("Permissions-Policy","camera=(), microphone=(), geolocation=()")
  self.send_header("Content-Security-Policy","default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'")
 def sendh(self,x,n=200,c=None):
  b=x.encode();self.send_response(n);self.send_header("Content-Type","text/html; charset=utf-8");self.send_header("Content-Length",len(b));self.security_headers();self.send_header("Cache-Control","no-store")
  if c:self.send_header("Set-Cookie",c)
  self.end_headers();self.wfile.write(b)
 def sendj(self,x,n=200):
  b=json.dumps(x,ensure_ascii=False).encode();self.send_response(n);self.send_header("Content-Type","application/json; charset=utf-8");self.send_header("Content-Length",len(b));self.security_headers();self.send_header("Cache-Control","no-store");self.end_headers();self.wfile.write(b)
 def sendsvg(self,x):
  b=x.encode();self.send_response(200);self.send_header("Content-Type","image/svg+xml");self.send_header("Content-Length",len(b));self.send_header("Cache-Control","public, max-age=86400");self.end_headers();self.wfile.write(b)
 def redir(self,u):self.send_response(303);self.send_header("Location",u);self.end_headers()
 def tok(self):
  c=cookies.SimpleCookie(self.headers.get("Cookie",""));return c["mp"].value if "mp"in c else ""
 def authed(self):return valid(self.tok())
 def form(self):
  raw=self.rfile.read(min(int(self.headers.get("Content-Length",0)),2097152)).decode(errors="replace");return {k:(v if len(v)>1 else v[0]) for k,v in parse.parse_qs(raw,keep_blank_values=True).items()}
 def ci(self):return f"<input type=hidden name=csrf value='{csrf(self.tok())}'>"
 def fail(self,x,on="domains"):self.sendh(layout("操作失败",f"<div class='card narrow'><div class='msg err'>{e(x)}</div><a class='btn gray' href='javascript:history.back()'>返回</a></div>",on),500)
 def do_GET(self):
  u=parse.urlsplit(self.path);p,q=u.path,u.query
  if p=="/favicon.svg":return self.sendsvg(ICON)
  if p=="/health":return self.sendh("ok")
  if p=="/":self.send_response(404);self.send_header("Content-Length","0");self.end_headers();return
  if p=="/logout":
   self.send_response(303);self.send_header("Location",ADMIN_PATH);self.send_header("Set-Cookie","mp=; Max-Age=0; Path=/; HttpOnly; SameSite=Lax");self.end_headers();return
  if p=="/login":return self.redir(ADMIN_PATH)
  if p==ADMIN_PATH and self.authed():p="/domains"
  if p==ADMIN_PATH or not self.authed():
   bad="<div class='msg err'>账号或密码错误</div>" if 'err' in parse.parse_qs(q) else ""
   return self.sendh(f"<!doctype html><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'><link rel=icon type='image/svg+xml' href='/favicon.svg'><title>Rykvo 邮局登录</title><style>{CSS}</style><div class='login-wrap'><div class='login-brand'>{ICON}<div><b>Rykvo 邮局</b></div></div><div class='card login'><h1>管理员登录</h1>{bad}<form method=post action={ADMIN_PATH}><label>管理员账号</label><input name=user autocomplete=username><br><br><label>管理员密码</label><input type=password name=password autocomplete=current-password><br><br><button>登录</button></form></div></div>")
  try:
   if p=="/api/users/bulk/status":
    jid=(parse.parse_qs(q).get('id')or[''])[0]
    with JOBS_LOCK:j=dict(JOBS.get(jid,{}))
    return self.sendj(j if j else {'error':'任务不存在'},200 if j else 404)
   if p=="/api/users/delete/status":
    jid=(parse.parse_qs(q).get('id')or[''])[0]
    with JOBS_LOCK:j=dict(JOBS.get(jid,{}))
    return self.sendj(j if j else {'error':'任务不存在'},200 if j else 404)
   if p=="/domains":
    s=state();rows="";mods=""
    for d in domains():
     n=d.get("name");i=str(d.get('id'));ds=s["domains"].get(n,{});ok=ds.get("verified");prev=ds.get('checks',[]);h="mail."+n;z=d.get("dnsZoneFile","");certauto=(d.get('certificateManagement')or{}).get('@type')=='Automatic';rs=[("A",h,IP,"—"),("MX",n,h,"10"),("TXT",n,"v=spf1 mx -all","—"),("TXT","_dmarc."+n,"v=DMARC1; p=quarantine","—")];dr=""
     for ix,(a,b,c,pr) in enumerate(rs):
      was=(prev[ix][1] if ix<len(prev) and isinstance(prev[ix],list) and len(prev[ix])>1 else None);status=("✅ <b style='color:#059669'>已通过</b>" if was is True else "❌ <b style='color:#dc2626'>未通过</b>" if was is False else "<span class=muted>待检测</span>");dr+=f"<tr><td>{a}</td><td class=dns onclick=cp(this) data-copy='{e(b)}' title='点击复制'>{e(b)}</td><td class=dns onclick=cp(this) data-copy='{e(c)}' title='点击复制'>{e(c)}</td><td onclick=cp(this) data-copy='{e(pr)}' title='点击复制'>{e(pr)}</td><td id='dnsst-{e(i)}-{ix}'>{status}</td></tr>"
     rows+=f"<tr><td><input form=domainbatch type=checkbox name=ids value='{e(i)}'></td><td><b>{e(n)}</b><div class=muted>{e(h)}</div></td><td><span id='domainst-{e(i)}' class='badge {'ok' if ok else 'warn'}'>{'检测通过' if ok else '待检测'}</span></td><td class=actions><button class='small' onclick=\"modal('dns-{e(i)}')\">DNS 设置</button><form method=post action=/domains/delete onsubmit=\"return ask(event,'删除该域名？')\">{self.ci()}<input type=hidden name=id value='{e(i)}'><button class='red small'>删除</button></form></td></tr>"
     mods+=f"<div class=modal id='dns-{e(i)}'><div class=modalbox><div class=modalhead><h2>{e(n)} DNS 配置</h2><button class=x onclick=closeModal(this)>关闭</button></div><table><tr><th>类型</th><th>名称</th><th>内容</th><th>优先级</th><th>检测状态</th></tr>{dr}</table><div class=actions style='margin-top:18px'><form method=post action=/api/domains/verify onsubmit=\"return verifyDns(event,'{e(i)}')\">{self.ci()}<input type=hidden name=id value='{e(i)}'><button class=green>检测 DNS</button></form><form method=post action=/domains/certificate>{self.ci()}<input type=hidden name=id value='{e(i)}'><button>{'重新申请邮件 SSL' if certauto else '申请邮件 SSL'}</button></form><span class='badge {'ok' if certauto else 'warn'}'>{'自动证书已开启' if certauto else '尚未申请证书'}</span></div></div></div>"
    if not rows:rows="<tr><td colspan=4>还没有域名</td></tr>"
    add=f"<div class=modal id=add-domain><div class='modalbox narrow'><div class=modalhead><h2>添加域名</h2><button class=x onclick=closeModal(this)>关闭</button></div><form method=post action=/domains/add>{self.ci()}<label>邮箱域名</label><input name=domain placeholder=example.com required><p class=muted>邮件服务器自动使用 mail.你的域名</p><button>保存并生成 DNS</button></form></div></div>"
    return self.sendh(layout("邮局域名",note(q)+f"<div class=card><div class=listbar><input class=list-search placeholder='搜索域名'><div class=actions><form id=domainbatch method=post action=/domains/delete onsubmit=\"return domainDeleteAsk(event)\">{self.ci()}<button class='red small'>删除</button></form><button onclick=\"modal('add-domain')\">＋ 添加域名</button></div></div><table class=list-table><tr><th><input type=checkbox title=全选 onclick=\"toggleForm('domainbatch',this)\"></th><th>域名</th><th>状态</th><th>操作</th></tr>{rows}</table><div class=pager></div></div>{add}{mods}{SCRIPT}"))
   if p=="/users":
    ds=domains();dm={x.get('id'):x.get('name')for x in ds};opts="".join(f"<option value='{e(x.get('id'))}'>{e(x.get('name'))}</option>"for x in ds);filteropts="".join(f"<option value='{e(x.get('name'))}'>{e(x.get('name'))}</option>"for x in ds);rows="";mods="";st=state();names=st.get('display_names',{});vault=st.get('password_vault',{});export_records=[]
    for x in users():
     i=str(x.get('id'));dn=dm.get(x.get('domainId'),'');addr=f"{x.get('name')}@{dn}";display=names.get(i,x.get('name'));mb=(x.get('quotas')or{}).get('maxDiskQuota',0)//1048576;export_records.append({'id':i,'domain':dn,'line':addr+'----'+unseal(vault.get(i,''))});rows+=f"<tr data-domain='{e(dn)}'><td><input form=batch type=checkbox name=ids value='{e(i)}'></td><td><b>{e(display)}</b></td><td>{e(addr)}</td><td>{mb} MB</td><td class=actions><button class='small' onclick=\"modal('edit-{e(i)}')\">修改</button><form method=post action=/users/delete onsubmit=\"return ask(event,'删除 {e(addr)}？')\">{self.ci()}<input type=hidden name=ids value='{e(i)}'><button class='red small'>删除</button></form></td></tr>";mods+=f"<div class=modal id='edit-{e(i)}'><div class='modalbox narrow'><div class=modalhead><h2>修改 {e(addr)}</h2><button class=x onclick=closeModal(this)>关闭</button></div><form method=post action=/users/edit>{self.ci()}<input type=hidden name=id value='{e(i)}'><div class=grid><div><label>用户名</label><input name=display_name value='{e(display)}' required></div><div><label>新密码（留空不修改）</label><input type=password name=password></div><div><label>容量（MB）</label><input type=number name=quota value='{mb}' min=1 required></div><div class=full><button>保存修改</button></div></div></form></div></div>"
    if not rows:rows="<tr><td colspan=5>还没有邮箱用户</td></tr>"
    add=f"<div class=modal id=add-user><div class='modalbox narrow'><div class=modalhead><h2>创建用户</h2><button class=x onclick=closeModal(this)>关闭</button></div><form method=post action=/users/add>{self.ci()}<div class=grid><div><label>用户名</label><input name=display_name required></div><div><label>邮箱账号</label><input name=username placeholder=mailbox required></div><div><label>密码</label><input type=password name=password required></div><div><label>域名</label><select name=domain_id>{opts}</select></div><div><label>容量（MB）</label><input type=number name=quota value=1024 min=1 required></div><div class=full><button>创建</button></div></div></form></div></div>"
    bulk=f"<div class='modal locked' id=bulk-user><div class=modalbox><div class=modalhead><h2>批量创建用户</h2><button class=x onclick=closeModal(this)>关闭</button></div><form id=bulk-form method=post action=/api/users/bulk/start onsubmit=\"return startBulk(event)\">{self.ci()}<label>统一域名</label><select name=domain_id>{opts}</select><br><br><label>选择 TXT 文件</label><input id=file type=file accept=.txt><p class=muted>每行：用户名----邮箱账号----密码----容量MB</p><textarea id=rows name=rows placeholder='张三----zhangsan----Password----1024' required></textarea><br><button id=bulk-start>开始创建</button></form><div class=bulk-progress id=bulk-progress><div class=progress-track><div class=progress-fill id=bulk-fill></div></div><div class=progress-label><span id=bulk-count>0 / 0</span><span id=bulk-percent>0%</span></div></div></div></div><script>file.onchange=async e=>rows.value=await e.target.files[0].text()</script>"
    export_json=json.dumps(export_records,ensure_ascii=False).replace('<','\\u003c');export_modal=f"<div class=modal id=export-user><div class='modalbox narrow'><div class=modalhead><h2>导出邮箱账号</h2><button class=x onclick=closeModal(this)>关闭</button></div><label>域名分类</label><select id=export-domain onchange=updateExport()><option value=''>全部</option>{filteropts}</select><br><br><textarea id=export-text readonly></textarea><div class=actions style='justify-content:flex-end;margin-top:18px'><button class=gray onclick=closeModal(this)>关闭</button><button onclick=copyExport()>复制</button><button onclick=downloadExport()>下载 TXT</button></div></div></div><script>window.exportRecords={export_json}</script>"
    b=note(q)+f"<div class=card><div class=listbar><div class=actions style='flex:1'><input class=list-search placeholder='搜索用户名或邮箱'><select class=domain-filter style='max-width:220px'><option value=''>全部域名</option>{filteropts}</select></div><div class=actions><form id=batch method=post action=/users/delete onsubmit=\"return deleteAsk(event)\">{self.ci()}<button class='red small'>删除</button></form><button class='gray small' onclick=openExport()>导出</button><button class=gray onclick=\"modal('bulk-user')\">批量创建</button><button onclick=\"modal('add-user')\">＋ 创建用户</button></div></div><table class=list-table><tr><th><input type=checkbox title=全选 onclick=toggleAll(this)></th><th>用户名</th><th>邮箱账号</th><th>容量</th><th>操作</th></tr>{rows}</table><div class=pager></div></div>{add}{bulk}{export_modal}{mods}<div class='modal locked' id=delete-progress><div class='modalbox narrow'><div class=modalhead><h2>正在删除</h2></div><div class=progress-track><div class=progress-fill id=delete-fill></div></div><div class=progress-label><span id=delete-count>0 / 0</span><span id=delete-percent>0%</span></div></div></div>{SCRIPT}";return self.sendh(layout("用户管理",b,"users"))
   if p=="/settings":
    s=state();pd=s.get('panel_domain','');days=s.get('retention_days',30);au,ap=admin_creds()
    try:
     with open('/var/lib/mailpanel/cert-result',encoding='utf8') as f:cr=f.read().strip()
    except:cr='尚未申请'
    tab=(parse.parse_qs(q).get('tab')or['account'])[0]
    account=f"<section class='card narrow settings-panel' id=set-account><h2>管理员账号</h2><form method=post action=/settings/account>{self.ci()}<div class=grid><div class=full><label>管理员账号</label><input name=admin_user value='{e(au)}' required></div><div><label>新密码</label><input type=password name=admin_password placeholder='留空不修改'></div><div><label>确认新密码</label><input type=password name=admin_password_confirm placeholder='再次输入新密码'></div><div class=full><button>保存</button></div></div></form></section>"
    panel=f"<section class='card narrow settings-panel' id=set-panel><h2>设置</h2><div class=settings-row><span>服务器 IP</span><b class=dns>{IP}</b></div><form method=post action=/settings/panel>{self.ci()}<label>访问域名</label><input name=panel_domain value='{e(pd)}' placeholder=admin.example.com><br><br><button>保存域名</button></form><div class=settings-divider></div><h2>HTTPS 证书</h2>"+(f"<div class=settings-row><span>证书状态</span><span class='badge {'ok' if cr.startswith('成功') else 'warn'}'>{e(cr)}</span></div><form method=post action=/settings/certificate>{self.ci()}<button class=green>申请／续期证书</button></form>"if pd else"<div class='msg warn'>请先保存访问域名</div>")+"</section>"
    cleanup=f"<section class='card narrow settings-panel' id=set-cleanup><h2>自动清理</h2><form method=post action=/settings/retention>{self.ci()}<label>清理天数</label><input type=number name=days value='{days}' min=0 max=3650 required><br><br><button>保存</button></form><div class=settings-divider></div><h2>立即清理</h2><form method=post action=/settings/cleanup-now onsubmit=\"return ask(event,'执行清理？')\">{self.ci()}<label>清理天数</label><input type=number name=days value=30 min=0 max=3650 required><br><br><button class=red>立即清理</button></form></section>"
    spam_on=bool(s.get('spam_enabled',False));mail=f"<section class='card narrow settings-panel' id=set-mail><h2>垃圾邮件</h2><form method=post action=/settings/spam>{self.ci()}<label>垃圾邮件分类</label><select name=enabled><option value=1 {'selected' if spam_on else ''}>开启（垃圾邮件进入垃圾邮件箱）</option><option value=0 {'selected' if not spam_on else ''}>关闭（全部进入收件箱）</option></select><br><br><button>保存</button></form></section>"
    tabs=f"<input class=settings-radio type=radio name=settings-tab id=tab-account {'checked' if tab=='account' else ''}><input class=settings-radio type=radio name=settings-tab id=tab-panel {'checked' if tab=='panel' else ''}><input class=settings-radio type=radio name=settings-tab id=tab-cleanup {'checked' if tab=='cleanup' else ''}><input class=settings-radio type=radio name=settings-tab id=tab-mail {'checked' if tab=='mail' else ''}><div class=settings-tabs><label class=tab-label for=tab-account>管理员</label><label class=tab-label for=tab-panel>设置</label><label class=tab-label for=tab-cleanup>自动清理</label><label class=tab-label for=tab-mail>邮件设置</label></div>"
    b=note(q)+tabs+account+panel+cleanup+mail+SCRIPT;return self.sendh(layout("系统设置",b,"settings"))
   self.send_error(404)
  except Exception as x:self.fail(x)
 def do_POST(self):
  p=parse.urlsplit(self.path).path;f=self.form()
  if p==ADMIN_PATH:
   ip=self.headers.get('X-Real-IP',self.client_address[0]);now=time.time()
   with LOGIN_LOCK:
    recent=[t for t in LOGIN_ATTEMPTS.get(ip,[]) if now-t<300];LOGIN_ATTEMPTS[ip]=recent
   if len(recent)>=8:return self.sendh('登录尝试过多，请稍后再试',429)
   au,ap=admin_creds()
   if hmac.compare_digest(str(f.get('user','')),au)and hmac.compare_digest(str(f.get('password','')),ap):
    with LOGIN_LOCK:LOGIN_ATTEMPTS.pop(ip,None)
    t=token();secure='; Secure' if self.headers.get('X-Forwarded-Proto','').lower()=='https' else '';self.send_response(303);self.send_header('Location',ADMIN_PATH);self.send_header('Set-Cookie',f'mp={t}; Path=/; HttpOnly; SameSite=Strict; Max-Age=86400{secure}');self.end_headers();return
   with LOGIN_LOCK:LOGIN_ATTEMPTS.setdefault(ip,[]).append(now)
   return self.redir(ADMIN_PATH+'?err=1')
  if not self.authed():return self.redir(ADMIN_PATH)
  if not hmac.compare_digest(str(f.get('csrf','')),csrf(self.tok())):return self.sendh('CSRF failed',403)
  try:
   if p=="/api/users/bulk/start":
    raw=str(f.get('rows',''));domain_id=str(f.get('domain_id',''))
    if not raw.strip():raise ValueError('没有用户数据')
    jid=secrets.token_urlsafe(12)
    with JOBS_LOCK:JOBS[jid]={'total':len([x for x in raw.splitlines() if x.strip()]),'done':0,'made':0,'finished':False,'errors':[]}
    threading.Thread(target=bulk_worker,args=(jid,domain_id,raw),daemon=True).start();return self.sendj({'id':jid})
   if p=="/api/users/delete/start":
    ids=f.get('ids',[]);ids=[ids] if isinstance(ids,str) else ids
    if not ids:ids=[str(x.get('id')) for x in users()]
    jid=secrets.token_urlsafe(12)
    with JOBS_LOCK:JOBS[jid]={'total':len(ids),'done':0,'deleted':0,'failed':0,'finished':False}
    threading.Thread(target=delete_worker,args=(jid,ids),daemon=True).start();return self.sendj({'id':jid})
   if p=="/api/domains/verify":
    i=str(f.get('id'));d=domain(i);cs=checks(d['name'],d.get('dnsZoneFile',''));ok=all(x[1]for x in cs[:4]);s=state();s['domains'][d['name']]={'verified':ok,'checked_at':int(time.time()),'checks':cs};save(s);return self.sendj({'ok':ok,'checks':[{'label':x[0],'ok':x[1],'actual':x[2]} for x in cs]})
   if p=="/domains/add":
    n=str(f.get('domain','')).strip().lower().rstrip('.')
    if not re.fullmatch(r"(?=.{4,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}",n):raise ValueError('域名格式不正确')
    old=next((x for x in domains()if x.get('name')==n),None);i=old.get('id')if old else add_domain(n);return self.redir('/domains?msg='+parse.quote('域名已添加，请打开 DNS 设置继续'))
   if p=="/domains/delete":
    ids=f.get('ids',[]) or f.get('id',[]);ids=[ids]if isinstance(ids,str)else ids
    if not ids:ids=[str(x.get('id')) for x in domains()]
    removed=0
    for did in ids:
     d=domain(str(did));delete_domain_cascade(str(did));st=state()
     if d:st.get('domains',{}).pop(d.get('name',''),None);save(st);removed+=1
    return self.redir('/domains?msg='+parse.quote(f'已删除 {removed} 个域名'))
   if p=="/domains/certificate":
    d=domain(str(f.get('id')));request_mail_certificate(d);return self.redir('/domains?msg='+parse.quote('邮件 SSL 证书申请已提交，系统会自动签发并续期'))
   if p=="/users/add":
    n=str(f.get('username','')).lower();pw=str(f.get('password',''));display=str(f.get('display_name','')).strip()
    if not re.fullmatch(r'[a-z0-9][a-z0-9._+-]{0,63}',n):raise ValueError('邮箱账号格式错误')
    if not pw:raise ValueError('密码不能为空')
    if not display:raise ValueError('用户名不能为空')
    did=str(f.get('domain_id'));uid=str(add_user(n,did,pw,int(f.get('quota',1024)),display));s=state();s.setdefault('display_names',{})[uid]=display;s.setdefault('password_vault',{})[uid]=seal(pw);save(s);d=domain(did);sync_sender_name(f"{n}@{d.get('name')}",display) if d else None;rebuild_sender_name_script();return self.redir('/users?msg='+parse.quote('用户创建成功'))
   if p=="/users/edit":
    uid=str(f.get('id'));display=str(f.get('display_name','')).strip()
    if not display:raise ValueError('用户名不能为空')
    pw=str(f.get('password',''));u=next((x for x in users() if str(x.get('id'))==uid),None);update_user(uid,pw,int(f.get('quota',1024)),display);s=state();s.setdefault('display_names',{})[uid]=display
    if pw:s.setdefault('password_vault',{})[uid]=seal(pw)
    save(s);d=domain(str(u.get('domainId'))) if u else None;sync_sender_name(f"{u.get('name')}@{d.get('name')}",display) if u and d else None;rebuild_sender_name_script();return self.redir('/users?msg='+parse.quote('用户已更新'))
   if p=="/users/delete":
    ids=f.get('ids',[]);ids=[ids]if isinstance(ids,str)else ids
    if not ids:ids=[str(x.get('id')) for x in users()]
    if not ids:return self.redir('/users?msg='+parse.quote('没有可删除的用户'))
    done,failed=destroy_accounts(ids)
    if done:schedule_purge()
    s=state();dn=s.setdefault('display_names',{});vault=s.setdefault('password_vault',{});[dn.pop(str(i),None) for i in done];[vault.pop(str(i),None) for i in done];save(s)
    rebuild_sender_name_script();msg=f'已删除 {len(done)} 个用户'+(f'，{len(failed)} 个未删除' if failed else '');return self.redir('/users?msg='+parse.quote(msg))
   if p=="/settings/panel":
    pd=str(f.get('panel_domain','')).strip().lower().rstrip('.');s=state();s['panel_domain']=pd;save(s);return self.redir('/settings?tab=panel&msg='+parse.quote('后台域名已保存'))
   if p=="/settings/retention":
    days=max(0,min(3650,int(f.get('days',30))));s=state();s['retention_days']=days;save(s);ms=days*86400000 if days else 3153600000000
    retention={"expungeTrashAfter":ms,"expungeSubmissionsAfter":ms,"expungeShareNotifyAfter":ms,"expungeSchedulingInboxAfter":ms,"holdMtaReportsFor":ms,"holdTracesFor":ms,"holdMetricsFor":ms,"archiveDeletedItemsFor":ms,"archiveDeletedAccountsFor":None,"expungeSchedule":{"@type":"Daily","hour":0,"minute":0},"dataCleanupSchedule":{"@type":"Daily","hour":2,"minute":0},"blobCleanupSchedule":{"@type":"Daily","hour":4,"minute":0}}
    call([["x:DataRetention/set",{"update":{"singleton":retention}},"r"]]);return self.redir('/settings?tab=cleanup&msg='+parse.quote('自动清理已保存'))
   if p=="/settings/cleanup-now":
    days=max(0,min(3650,int(f.get('days',0))));cleanup_now(days);return self.redir('/settings?tab=cleanup&msg='+parse.quote('清理任务已提交'))
   if p=="/settings/spam":
    enabled=str(f.get('enabled','0'))=='1';s=state();s['spam_enabled']=enabled;save(s);configure_spam_filter(enabled);return self.redir('/settings?tab=mail&msg='+parse.quote('邮件设置已保存'))
   if p=="/settings/account":
    au=str(f.get('admin_user','')).strip();pw=str(f.get('admin_password',''));pw2=str(f.get('admin_password_confirm',''))
    if len(au)<3:raise ValueError('管理员账号至少 3 位')
    if pw and len(pw)<8:raise ValueError('新密码至少 8 位')
    if pw!=pw2:raise ValueError('两次输入的新密码不一致')
    s=state();s['admin_user']=au
    if pw:s['admin_password']=pw
    save(s);return self.redir('/settings?tab=account&msg='+parse.quote('管理员账号已保存'))
   if p=="/settings/certificate":
    pd=state().get('panel_domain','')
    if not pd:raise ValueError('请先保存后台访问域名')
    request_panel_certificate(pd);return self.redir('/settings?tab=panel&msg='+parse.quote('证书申请已提交'))
   self.send_error(404)
  except Exception as x:
   if p.startswith('/users'):return self.redir('/users?err='+parse.quote(friendly_error(x)))
   if p.startswith('/settings'):return self.redir('/settings?tab=account&err='+parse.quote(friendly_error(x)))
   self.fail(x,'domains')
def configure_spam_filter(enabled=None):
 try:
  if enabled is None:enabled=bool(state().get('spam_enabled',False))
  call([["x:SpamSettings/set",{"update":{"singleton":{"enable":bool(enabled),"greylistFor":None,"scoreDiscard":0,"scoreReject":0,"scoreSpam":5}}},"s"]])
 except Exception:pass
def configure_standard_listeners():
 try:
  typ='x:NetworkListener';q=resp(call([[typ+'/query',{},'q']]),typ+'/query');objs=resp(call([[typ+'/get',{'ids':q.get('ids',[])},'g']]),typ+'/get').get('list',[]);existing={x.get('name') for x in objs};creates={}
  for name,proto,port in [('imap','imap',143),('pop3','pop3',110),('submission','smtp',587)]:
   if name not in existing:creates[name]={'name':name,'bind':{f'[::]:{port}':True},'protocol':proto,'useTls':True,'tlsImplicit':False,'overrideProxyTrustedNetworks':{},'tlsDisableCipherSuites':{},'tlsDisableProtocols':{}}
  if creates:
   call([[typ+'/set',{'create':creates},'s']])
   with open('/var/lib/mailpanel/reload-stalwart','w') as f:f.write(str(time.time()))
 except Exception as ex:print('listener setup:',ex,flush=True)
if __name__=='__main__':
 configure_spam_filter()
 configure_standard_listeners()
 ThreadingHTTPServer((HOST,PORT),H).serve_forever()



