"""Alibaba Cloud Farm Dashboard v3.2 - With usage tracker from 9Router"""
import os, json, subprocess, time, threading, sqlite3
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import parse_qs

RESULTS_FILE = "/root/alibaba-cloud-farm/results.json"
FARM_SCRIPT = "/root/alibaba-cloud-farm/farm.py"
NINEROUTER_DB = "/root/.9router/db/data.sqlite"
BASE_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
farm_status = {"running": False, "last_output": "", "last_run": "Never", "success": 0, "fail": 0, "slider": 0}

def load_results():
    try:
        with open(RESULTS_FILE) as f: return json.load(f)
    except: return []

def delete_account(email):
    results = load_results()
    results = [r for r in results if r.get("email") != email]
    with open(RESULTS_FILE, "w") as f:
        json.dump(results, f, indent=2)
    return results

def get_usage_stats():
    """Query 9Router usageHistory for qf/ models (via SSH to VPS SGP)"""
    try:
        import subprocess
        sql = "SELECT 'qf/' || model, COUNT(*), COALESCE(SUM(promptTokens),0), COALESCE(SUM(completionTokens),0) FROM usageHistory WHERE provider='openai-compatible-chat-747b30d9-fa93-4812-aecc-9cabe712e0e9' GROUP BY model ORDER BY 4 DESC"
        import shlex
        remote_cmd = f"sqlite3 /root/.9router/db/data.sqlite {shlex.quote(sql)}"
        cmd = ["ssh", "-o", "ConnectTimeout=3", "-o", "BatchMode=yes",
               "root@100.103.96.42", remote_cmd]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        rows = []
        for line in result.stdout.strip().split("\n"):
            if line.strip():
                parts = line.split("|")
                if len(parts) == 4:
                    rows.append((parts[0], int(parts[1]), int(parts[2]), int(parts[3])))
        total_prompt = sum(r[2] for r in rows)
        total_completion = sum(r[3] for r in rows)
        total_requests = sum(r[1] for r in rows)
        return {
            "models": [{"model": r[0], "requests": r[1], "prompt": r[2], "completion": r[3], "total": r[2]+r[3]} for r in rows],
            "total_requests": total_requests,
            "total_tokens": total_prompt + total_completion,
            "total_prompt": total_prompt,
            "total_completion": total_completion
        }
    except Exception as e:
        return {"models": [], "total_requests": 0, "total_tokens": 0, "error": str(e)}

def run_farm(max_attempts):
    farm_status["running"] = True
    farm_status["last_output"] = "Starting farm...\n"
    farm_status["success"] = farm_status["fail"] = farm_status["slider"] = 0
    try:
        env = os.environ.copy(); env["MAX_ATTEMPTS"] = str(max_attempts)
        proc = subprocess.Popen(["xvfb-run","-a","python3","-u",FARM_SCRIPT],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env,
            cwd="/root/alibaba-cloud-farm", text=True)
        output = ""
        for line in proc.stdout:
            output += line; farm_status["last_output"] = output
            if "SUCCESS!" in line: farm_status["success"] += 1
            elif "fail" in line.lower(): farm_status["fail"] += 1
            elif "slider" in line.lower() and "skip" in line.lower(): farm_status["slider"] += 1
        proc.wait()
        farm_status["last_output"] = output
        farm_status["last_run"] = time.strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        farm_status["last_output"] = f"Error: {e}"
    farm_status["running"] = False

HTML = """<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Alibaba Farm</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:system-ui,-apple-system,sans-serif;background:#0f0f0f;color:#e0e0e0;padding:20px;max-width:950px;margin:0 auto}
h1{font-size:1.8em;color:#fff} h2{font-size:1.1em;margin:20px 0 10px;color:#aaa;border-bottom:1px solid #333;padding-bottom:5px}
.sub{color:#888;margin-bottom:20px;font-size:.85em}
.sub a{color:#4fc3f7;text-decoration:none}.sub a:hover{text-decoration:underline}
.card{background:#1a1a1a;border:1px solid #333;border-radius:8px;padding:15px;margin:10px 0}
.stat{display:inline-block;margin-right:25px;text-align:center}
.stat .n{font-size:1.8em;font-weight:bold;color:#4fc3f7} .stat .l{font-size:.75em;color:#888}
table{width:100%;border-collapse:collapse;margin-top:10px}
th{text-align:left;padding:8px;color:#888;border-bottom:1px solid #333;font-size:.8em}
td{padding:8px;border-bottom:1px solid #222;font-size:.85em;vertical-align:middle}
.m{font-family:monospace;font-size:.78em;color:#81d4fa;word-break:break-all}
.btn{background:#1565c0;color:#fff;border:none;padding:8px 16px;border-radius:6px;cursor:pointer;font-size:.9em;margin:3px}
.btn:hover{background:#1976d2}.btn:disabled{background:#444;cursor:not-allowed}
.btn.sm{padding:6px 14px;font-size:.88em;border-radius:5px}
.btn.del{background:#b71c1c;color:#fff;border:none;padding:5px 10px;border-radius:5px;cursor:pointer;font-size:.8em}.btn.del:hover{background:#d32f2f}
.btn.ok{background:#2e7d32}.btn.er{background:#c62828}
.log{background:#111;border:1px solid #333;border-radius:6px;padding:10px;font-family:monospace;font-size:.78em;max-height:300px;overflow-y:auto;white-space:pre-wrap;color:#aaa;margin-top:10px}
.st{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:5px}
.st.on{background:#4caf50}.st.off{background:#666}
.warn{background:#3e2723;border:1px solid #5d4037;border-radius:6px;padding:10px;margin:10px 0;color:#ffab91;font-size:.85em}
.warn b{color:#ff8a65}
select,input[type=number],input[type=text]{background:#222;border:1px solid #444;color:#fff;padding:5px 8px;border-radius:4px}
.ib{display:inline-flex;align-items:center;background:#1e1e1e;border:1px solid #444;border-radius:6px;overflow:hidden;height:32px;margin:4px 0}
.ib input{background:transparent;border:none;color:#4fc3f7;padding:4px 8px;font-family:monospace;font-size:.8em;outline:none;width:100%;min-width:0}
.ib .cp{display:flex;align-items:center;justify-content:center;min-width:32px;height:32px;cursor:pointer;color:#888;border-left:1px solid #333;transition:all .15s;font-size:.9em;padding:0 6px}
.ib .cp:hover{background:#2a2a2a;color:#fff}
.ib .cp.ok{color:#4caf50}
.base-box{background:#111;border:1px solid #333;border-radius:8px;padding:12px 15px;margin:10px 0;display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.base-box .lbl{color:#888;font-size:.85em;white-space:nowrap}
.bar{height:6px;border-radius:3px;background:#333;margin-top:4px;overflow:hidden}
.bar-fill{height:100%;border-radius:3px;transition:width .3s}
.bar-ok{background:#4caf50}.bar-warn{background:#ff9800}.bar-danger{background:#f44336}
.tok{font-size:.75em;color:#888;margin-top:2px}
</style></head><body>
<h1>&#127805; Alibaba Cloud Farm</h1>
<p class="sub">VPS-sing2 &nbsp;&bull;&nbsp; <a href="https://dashscope.console.aliyun.com/" target="_blank">Alibaba DashScope Console &#8599;</a></p>
<div class="card">
<div class="stat"><div class="n" id="tc">0</div><div class="l">Accounts</div></div>
<div class="stat"><div class="n">14+</div><div class="l">Models</div></div>
<div class="stat"><div class="n">1M</div><div class="l">Tokens/Model</div></div>
<div class="stat"><span class="st off" id="sts"></span><span class="l" id="stt">Idle</span></div>
</div>
<div class="warn" id="wrn" style="display:none"></div>
<h2>Base URL</h2>
<div class="base-box">
<span class="lbl">Endpoint:</span>
<div class="ib" style="flex:1;min-width:300px"><input id="bu" value="https://dashscope-intl.aliyuncs.com/compatible-mode/v1" readonly><div class="cp" onclick="cpv('bu')" title="Copy">&#128203;</div></div>
</div>
<h2>&#128203; Farmed Accounts</h2>
<div class="card"><table><tr><th>#</th><th>Email</th><th>Password</th><th>API Key</th><th>Date</th><th></th></tr>
<tbody id="ab"></tbody></table></div>
<h2>&#128200; Usage Tracker</h2>
<div class="card">
<div style="display:flex;gap:20px;flex-wrap:wrap;margin-bottom:10px">
<div><span style="color:#888;font-size:.85em">Total Requests:</span> <span id="ur" style="color:#4fc3f7;font-weight:bold">0</span></div>
<div><span style="color:#888;font-size:.85em">Total Tokens:</span> <span id="ut" style="color:#4fc3f7;font-weight:bold">0</span></div>
<div><span style="color:#888;font-size:.85em">Quota/Model:</span> <span style="color:#888">3M tokens (3 accounts)</span></div>
</div>
<div id="ub" style="max-height:300px;overflow-y:auto"></div>
</div>
<h2>&#128640; Run Farm</h2>
<div class="card"><div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">
<label style="color:#888">Max:</label><input type="number" id="mx" value="5" min="1" max="50" style="width:60px">
<button class="btn" onclick="go()" id="rb">Start</button><span id="rs" style="color:#888;font-size:.85em"></span>
</div><div class="log" id="lg">No runs yet...</div></div>
<h2>&#129513; Quick API Test</h2>
<div class="card"><div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:10px">
<select id="md"><option>qwen-plus</option><option>qwen-turbo</option><option>qwen3-max</option>
<option>qwen3.6-flash</option><option>qwen3.6-plus</option><option>deepseek-v3.2</option>
<option>deepseek-v4-flash</option><option>glm-5.2</option><option>qwen3-coder-plus</option>
<option>qwen3-coder-flash</option><option>qwen3-8b</option><option>qwen3-30b-a3b</option>
<option>qwen3-235b-a22b</option></select>
<input type="text" id="pm" value="Say hello in 3 words" style="width:220px">
<button class="btn" onclick="tst()">Test</button></div>
<div class="log" id="al">Pick a model and click Test...</div></div>
<script>
var QUOTA=3000000;
function fmt(n){if(n>=1e6)return(n/1e6).toFixed(1)+'M';if(n>=1e3)return(n/1e3).toFixed(1)+'K';return n.toString();}
function go(){var m=document.getElementById('mx').value;document.getElementById('rb').disabled=true;
document.getElementById('lg').textContent='Starting...\\n';fetch('/api/run?max='+m).then(r=>r.json()).then(poll);}
function poll(){fetch('/api/log').then(r=>r.json()).then(function(d){
document.getElementById('lg').textContent=d.log;document.getElementById('stt').textContent=d.running?'Running':'Done';
document.getElementById('sts').className='st '+(d.running?'on':'off');
document.getElementById('rs').textContent=d.success+' OK | '+d.fail+' Fail | '+d.slider+' Slider';
if(d.running)setTimeout(poll,2000);else{document.getElementById('rb').disabled=false;ref();}});}
function ref(){fetch('/api/accounts').then(r=>r.json()).then(function(d){
document.getElementById('tc').textContent=d.accounts.length;var h='',w='';
d.accounts.forEach(function(a,i){
var ok=a.api_key&&a.api_key.indexOf('sk-')===0&&a.api_key.length>20;
h+='<tr><td>'+(i+1)+'</td><td>'+a.email+'</td><td class="m">'+a.password+'</td>';
h+='<td><div class="ib"><input id="k'+i+'" value="'+a.api_key+'" readonly onclick="this.select()">';
h+='<div class="cp" onclick="cpv(\\'k'+i+'\\')" title="Copy">&#128203;</div></div></td>';
h+='<td>'+a.timestamp+'</td>';
h+='<td><button class="btn del" onclick="delAc(\\''+a.email+'\\')">Delete</button></td></tr>';
if(!ok)w+='&bull; '+a.email+' &rarr; <code>'+a.api_key+'</code><br>';});
document.getElementById('ab').innerHTML=h;
if(w){document.getElementById('wrn').style.display='block';document.getElementById('wrn').innerHTML='<b>&#9888;&#65039; Issues:</b><br>'+w;}
else document.getElementById('wrn').style.display='none';});}
function refUsage(){fetch('/api/usage').then(r=>r.json()).then(function(d){
document.getElementById('ur').textContent=d.total_requests.toLocaleString();
document.getElementById('ut').textContent=fmt(d.total_tokens);
if(!d.models||d.models.length===0){document.getElementById('ub').innerHTML='<div style="color:#666;font-size:.85em;padding:10px">No usage yet. Start using qf/ models to see stats here.</div>';return;}
var h='<table><tr><th>Model</th><th>Requests</th><th>Prompt</th><th>Completion</th><th>Total</th><th>Quota</th></tr>';
d.models.forEach(function(m){
var pct=Math.min(100,(m.total/QUOTA)*100);
var cls=pct<50?'bar-ok':pct<80?'bar-warn':'bar-danger';
h+='<tr><td class="m">'+m.model.replace('qf/','')+'</td><td>'+m.requests+'</td>';
h+='<td>'+fmt(m.prompt)+'</td><td>'+fmt(m.completion)+'</td><td>'+fmt(m.total)+'</td>';
h+='<td style="min-width:120px"><div class="bar"><div class="bar-fill '+cls+'" style="width:'+pct+'%"></div></div>';
h+='<div class="tok">'+fmt(m.total)+' / 3M ('+pct.toFixed(1)+'%)</div></td></tr>';});
h+='</table>';document.getElementById('ub').innerHTML=h;});}
function cpv(id){var inp=document.getElementById(id);var v=inp.value;
var ta=document.createElement('textarea');ta.value=v;
ta.style.position='fixed';ta.style.left='-9999px';
document.body.appendChild(ta);ta.select();
document.execCommand('copy');document.body.removeChild(ta);
var btn=inp.parentElement.querySelector('.cp');
btn.innerHTML='&#10003;';btn.classList.add('ok');
setTimeout(function(){btn.innerHTML='&#128203;';btn.classList.remove('ok');},1200);}
function delAc(email){if(!confirm('Delete '+email+'?'))return;
fetch('/api/delete?email='+encodeURIComponent(email)).then(r=>r.json()).then(function(d){ref();});}
function tst(){var m=document.getElementById('md').value,p=document.getElementById('pm').value;
document.getElementById('al').textContent='Testing '+m+'...';
fetch('/api/test?model='+encodeURIComponent(m)+'&prompt='+encodeURIComponent(p))
.then(function(r){return r.json();}).then(function(d){document.getElementById('al').textContent=d.result||d.error;});}
ref();refUsage();
setInterval(function(){if(document.getElementById('rb').disabled)poll();},5000);
setInterval(refUsage,30000);
</script></body></html>"""

class H(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path=="/" or self.path=="":
            html=HTML
            self.send_response(200); self.send_header("Content-Type","text/html;charset=utf-8"); self.end_headers()
            self.wfile.write(html.encode())
        elif self.path.startswith("/api/run"):
            if farm_status["running"]: self.j({"error":"busy"}); return
            qs=parse_qs(self.path.split("?")[1] if "?" in self.path else "")
            t=threading.Thread(target=run_farm,args=(int(qs.get("max",["5"])[0]),),daemon=True); t.start()
            self.j({"ok":True})
        elif self.path=="/api/log":
            self.j({"log":farm_status["last_output"][-3000:],"running":farm_status["running"],
                "success":farm_status["success"],"fail":farm_status["fail"],"slider":farm_status["slider"]})
        elif self.path=="/api/accounts":
            self.j({"accounts":load_results()})
        elif self.path=="/api/usage":
            self.j(get_usage_stats())
        elif self.path.startswith("/api/test"):
            qs=parse_qs(self.path.split("?")[1] if "?" in self.path else "")
            model=qs.get("model",["qwen-plus"])[0]; prompt=qs.get("prompt",["hi"])[0]
            valid=[r for r in load_results() if r.get("api_key","").startswith("sk-") and len(r.get("api_key",""))>20]
            if not valid: self.j({"error":"No valid keys"}); return
            try:
                import urllib.request
                data=json.dumps({"model":model,"messages":[{"role":"user","content":prompt}],"max_tokens":50,"enable_thinking":False}).encode()
                req=urllib.request.Request("https://dashscope-intl.aliyuncs.com/compatible-mode/v1/chat/completions",
                    data=data,headers={"Authorization":f"Bearer {valid[-1]['api_key']}","Content-Type":"application/json"})
                r=json.loads(urllib.request.urlopen(req,timeout=15).read())
                c=r["choices"][0]["message"]["content"]; u=r.get("usage",{})
                self.j({"result":f"OK {model}\\n\\n{c}\\n\\ntokens: {u.get('total_tokens','?')}"})
            except Exception as e: self.j({"error":str(e)})
        elif self.path.startswith("/api/delete"):
            qs = parse_qs(self.path.split("?")[1] if "?" in self.path else "")
            email = qs.get("email", [""])[0]
            if email:
                remaining = delete_account(email)
                self.j({"ok": True, "accounts": remaining})
            else:
                self.j({"error": "no email"})
        else: self.send_error(404)
    def j(self,d):
        self.send_response(200); self.send_header("Content-Type","application/json"); self.end_headers()
        self.wfile.write(json.dumps(d).encode())
    def log_message(self,*a): pass

if __name__=="__main__":
    print("Farm Dashboard v3.2 on :8888"); HTTPServer(("0.0.0.0",8888),H).serve_forever()
