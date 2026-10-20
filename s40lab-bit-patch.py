from pathlib import Path
b = Path("app/src/main/java/br/s40lab/app/S40Bridge.java")
s = b.read_text()
assert 'case "brush-observation":answer=brushObservation(b);break;' in s
s = s.replace('case "brush-observation":answer=brushObservation(b);break;', 'case "brush-observation":answer=brushObservation(b);break;\n                case "bit-list":answer=bitList(b);break;')
method = r'''
    private JSONObject bitList(JSONObject b)throws Exception{
        requireDevice();
        if(demo)throw new IllegalArgumentException("BIT disponível somente com S40 conectado.");
        if(!"CONSULTAR BIT".equals(b.optString("confirmation"))||!b.optBoolean("safe_location",false))
            throw new IllegalArgumentException("Confirme a área segura e escreva CONSULTAR BIT.");
        JSONObject result=ok().put("command","set BIT 99-1, read 99-5, set normal 99-1");
        JSONArray props=new JSONArray().put(new JSONObject().put("did","99-5").put("siid",99).put("piid",5));
        boolean received=false;
        try {
            result.put("enter_ack",safe(device.setProperty(99,1,"BIT")));
            for(int i=0;i<12;i++) {
                SystemClock.sleep(1000);
                JSONArray data=device.getProperties(props);
                JSONObject item=data.optJSONObject(0);
                if(item!=null&&item.optInt("code",-1)==0) {
                    Object value=item.opt("value");
                    if(value!=null&&!JSONObject.NULL.equals(value)&&!String.valueOf(value).trim().isEmpty()) {
                        result.put("test_list",value).put("wait_seconds",i+1);
                        received=true;break;
                    }
                }
            }
            result.put("list_received",received);
        } catch(Exception e) {
            result.put("request_error",e.getMessage()==null?"Falha de comunicação":e.getMessage());
        } finally {
            try {
                result.put("exit_ack",safe(device.setProperty(99,1,"normal"))).put("exit_requested",true);
            } catch(Exception e) {
                result.put("exit_requested",false).put("exit_error",e.getMessage()==null?"Falha de comunicação":e.getMessage());
            }
        }
        return result.put("warning","Somente consulta. Nenhum comando de execução de testes 99-2 é enviado.");
    }
'''
assert '    private JSONObject brushObservation(' in s
s=s.replace('    private JSONObject brushObservation(', method+'\n    private JSONObject brushObservation(')
b.write_text(s)
g=Path("app/build.gradle")
g.write_text(g.read_text().replace("versionCode 3; versionName '0.3.0'","versionCode 4; versionName '0.4.0'"))
h=Path("app/src/main/assets/index.html")
x=h.read_text()
assert '<button class="tab" data-tab="explorar">Explorador MIoT</button>' in x
x=x.replace('<button class="tab" data-tab="explorar">Explorador MIoT</button>','<button class="tab" data-tab="explorar">Explorador MIoT</button><button class="tab" data-tab="bit">BIT experimental</button>')
section = '''
<section id="bit" class="page"><div class="heading"><h2>Consultar testes BIT</h2><p>Sequência extraída do plugin oficial S40. Não executa motores ou calibrações.</p></div>
<div class="card stack"><div class="notice red">Ativa temporariamente BIT (99-1), consulta 99-5 durante até 12 segundos e solicita retorno ao modo normal. Se a rede ou o aplicativo falhar, o retorno não é garantido.</div>
<label class="checkline"><input type="checkbox" id="bitSafety"> Robô no chão, longe de escadas, animais e pessoas; estou pronto para interromper fisicamente.</label>
<div><label for="bitConfirm">Digite CONSULTAR BIT</label><input id="bitConfirm" placeholder="CONSULTAR BIT" autocomplete="off"></div>
<button id="bitScan" class="btn primary" disabled>Entrar no BIT, consultar lista e sair</button><pre id="bitOutput" class="output">Ainda não consultado.</pre></div></section>
'''
assert '<section id="registros" class="page">' in x
x=x.replace('<section id="registros" class="page">',section+'<section id="registros" class="page">')
x=x.replace("'rawReadBtn','runTestBtn']","'rawReadBtn','runTestBtn','bitScan']")
fn = '''async function runBitList(){if(!con||busy)return;setBusy(true);$('bitOutput').textContent='Consultando BIT; aguarde retorno ao modo normal...';try{let r=await api('bit-list',{confirmation:$('bitConfirm').value.trim(),safe_location:$('bitSafety').checked});$('bitOutput').textContent=jsonText(r);if(!r.exit_requested)toast('ATENÇÃO: não confirmou saída do BIT! Reinicie o robô se necessário.',true);else toast(r.list_received?'Lista obtida; retorno ao normal solicitado':'Lista vazia; retorno ao normal solicitado')}catch(e){$('bitOutput').textContent=e.message;toast(e.message,true)}finally{setBusy(false)}}
'''
assert 'async function refreshLogs(){' in x
x=x.replace('async function refreshLogs(){',fn+'async function refreshLogs(){')
assert "$('runTestBtn').onclick=runTest;" in x
x=x.replace("$('runTestBtn').onclick=runTest;","$('runTestBtn').onclick=runTest;$('bitScan').onclick=runBitList;")
h.write_text(x)
print("BIT read-only enumeration patch applied successfully")


# --- v0.5: real MIoT DID, stabilized BIT polling, best-effort exit and manual recovery
m = Path("app/src/main/java/br/s40lab/app/MiiSocket.java")
ms = m.read_text()
assert '    public JSONObject info() throws Exception {' in ms
ms = ms.replace('    public JSONObject info() throws Exception {', '''
    /** Actual unsigned device ID from the miIO handshake, never hardcoded. */
    public synchronized String deviceId() throws Exception {
        if(did==null)handshake();
        return Long.toString(readLong(did,0));
    }
    public JSONObject info() throws Exception {''')
ms = ms.replace('req.put("did",s+"-"+p);req.put("siid",s);req.put("piid",p);req.put("value",value);',
                'req.put("did",s==99?deviceId():s+"-"+p);req.put("siid",s);req.put("piid",p);req.put("value",value);')
m.write_text(ms)
src=Path("app/src/main/java/br/s40lab/app/S40Bridge.java")
ss=src.read_text()
assert 'case "bit-list":answer=bitList(b);break;' in ss
ss=ss.replace('case "bit-list":answer=bitList(b);break;',
              'case "bit-list":answer=bitList(b);break;\n                case "bit-exit":answer=bitExit(b);break;')
start=ss.index('    private JSONObject bitList(JSONObject b)throws Exception{')
end=ss.index('    private JSONObject brushObservation(',start)
replacement=r'''    /** Probe only: no test/calibration execution; the robot may drop service communication in BIT. */
    private JSONObject bitList(JSONObject b)throws Exception{
        requireDevice();
        if(demo)throw new IllegalArgumentException("O modo demonstração não oferece BIT.");
        if(!"CONSULTAR BIT".equals(b.optString("confirmation"))||!b.optBoolean("safe_location",false))
            throw new IllegalArgumentException("Confirme ambiente seguro e digite CONSULTAR BIT.");
        JSONObject report=ok().put("procedure","enter BIT -> wait 10s -> read 99-5 with real DID -> attempt normal");
        JSONArray req=new JSONArray().put(new JSONObject()
            .put("did",device.deviceId()).put("siid",99).put("piid",5));
        JSONArray readErrors=new JSONArray();
        boolean gotList=false;
        try{
            report.put("enter_ack",safe(device.setProperty(99,1,"BIT")));
            log("bit","Entrada BIT confirmada pelo transporte; aguardando 10 segundos",null);
            SystemClock.sleep(10000);
            for(int i=0;i<4;i++){
                try{
                    if(i>0)device.handshake(); // Refresh session after service transitions.
                    JSONArray replies=device.getProperties(req);
                    JSONObject item=replies.optJSONObject(0);
                    int code=item==null?-1:item.optInt("code",-1);
                    if(code==0){
                        Object val=item.opt("value");
                        if(val!=null&&!JSONObject.NULL.equals(val)&&!String.valueOf(val).trim().isEmpty()){
                            report.put("test_list",val).put("read_attempt",i+1);
                            gotList=true;
                            break;
                        }
                    }else{
                        readErrors.put(new JSONObject().put("attempt",i+1).put("code",code));
                    }
                }catch(Exception e){
                    readErrors.put(new JSONObject().put("attempt",i+1).put("message",
                        e.getMessage()==null?"Falha de comunicação":e.getMessage()));
                }
                SystemClock.sleep(1300);
            }
        }catch(Exception e){
            report.put("probe_error",e.getMessage()==null?"Falha de comunicação":e.getMessage());
        }finally{
            report.put("list_received",gotList).put("read_errors",readErrors);
            attemptBitExit(report);
        }
        return report.put("warning","Sem execução de 99-2. Falha de confirmação da saída exige desligar e ligar pelo botão físico.");
    }

    /** Always best-effort: transport ACK never proves the robot has left service mode. */
    private void attemptBitExit(JSONObject report)throws Exception{
        report.put("exit_confirmed_by_transport",false).put("exit_send_attempted",true);
        try{
            report.put("exit_ack",safe(device.setProperty(99,1,"normal")));
            report.put("exit_confirmed_by_transport",true);
        }catch(Exception first){
            report.put("exit_error_first",first.getMessage()==null?"Falha de comunicação":first.getMessage());
            try{
                SystemClock.sleep(1600);
                device.handshake();
                report.put("exit_ack_retry",safe(device.setProperty(99,1,"normal")));
                report.put("exit_confirmed_by_transport",true);
            }catch(Exception second){
                report.put("exit_error_retry",second.getMessage()==null?"Falha de comunicação":second.getMessage());
            }
        }
        log("bit","Comando de saída BIT enviado; confirmação="+report.optBoolean("exit_confirmed_by_transport"),null);
    }

    /** Recovery command; does not enter BIT or run any test. */
    private JSONObject bitExit(JSONObject b)throws Exception{
        requireDevice();
        if(demo)throw new IllegalArgumentException("Somente com o S40 real conectado.");
        if(!"SAIR BIT".equals(b.optString("confirmation")))
            throw new IllegalArgumentException("Digite SAIR BIT para enviar o comando de recuperação.");
        JSONObject report=ok().put("procedure","request normal 99-1; retry after handshake if necessary");
        attemptBitExit(report);
        return report.put("warning","Se o S40 continuar em BIT ou não responder, desligue e religue pelo botão físico.");
    }

'''
ss=ss[:start]+replacement+ss[end:]
src.write_text(ss)
g=Path("app/build.gradle")
gg=g.read_text()
assert "versionCode 4; versionName '0.4.0'" in gg
g.write_text(gg.replace("versionCode 4; versionName '0.4.0'", "versionCode 5; versionName '0.5.0'"))
html=Path("app/src/main/assets/index.html")
hh=html.read_text()
assert 'id="bitScan"' in hh
hh=hh.replace('consulta 99-5 durante até 12 segundos', 'aguarda 10 segundos, consulta 99-5 pelo DID real')
hh=hh.replace('<button id="bitScan" class="btn primary" disabled>Entrar no BIT, consultar lista e sair</button>',
'''<button id="bitScan" class="btn primary" disabled>Entrar no BIT, consultar lista e sair</button>
<button id="bitExit" class="btn danger" disabled>Tentar sair do BIT (recuperação)</button>
<p class="note">Recuperação: ao tocar, você precisará confirmar SAIR BIT. Se não houver confirmação de saída, reinicie o S40 pelo botão físico.</p>''')
hh=hh.replace("'rawReadBtn','runTestBtn','bitScan']", "'rawReadBtn','runTestBtn','bitScan','bitExit']")
old="if(!r.exit_requested)toast("
assert old in hh
hh=hh.replace(old,"if(!r.exit_confirmed_by_transport)toast(")
hh=hh.replace("async function refreshLogs(){",
'''async function runBitExit(){if(!con||busy)return;if(!window.confirm('Enviar comando NORMAL para tentar sair do BIT?'))return;setBusy(true);try{let r=await api('bit-exit',{confirmation:'SAIR BIT'});$('bitOutput').textContent=jsonText(r);toast(r.exit_confirmed_by_transport?'Comando NORMAL reconhecido; confirme comportamento no robô.':'Sem confirmação; desligue e ligue o robô pelo botão físico.',!r.exit_confirmed_by_transport)}catch(e){toast('Saída não confirmada: '+e.message,true)}finally{setBusy(false)}}
async function refreshLogs(){''')
hh=hh.replace("$('bitScan').onclick=runBitList;", "$('bitScan').onclick=runBitList;$('bitExit').onclick=runBitExit;")
html.write_text(hh)
print("S40 Lab v0.5 patch applied: DID real, BIT stabilization, recovery UI")


# --- v0.6: isolated main brush BIT test (firmware-defined 30 seconds)
src=Path("app/src/main/java/br/s40lab/app/S40Bridge.java")
ss=src.read_text()
assert 'case "bit-exit":answer=bitExit(b);break;' in ss
ss=ss.replace('case "bit-exit":answer=bitExit(b);break;',
              'case "bit-exit":answer=bitExit(b);break;\n                case "bit-main-brush":answer=bitMainBrush(b);break;')
anchor='    /** Recovery command; does not enter BIT or run any test. */'
assert anchor in ss
method=r'''
    /** S40/H40 SOP: Rolling brush test runs about 30 seconds and announces pass/fail. */
    private JSONObject bitMainBrush(JSONObject b)throws Exception{
        requireDevice();
        if(demo)throw new IllegalArgumentException("BIT indisponível em demonstração.");
        if(!"TESTAR ESCOVA".equals(b.optString("confirmation"))||!b.optBoolean("safe_location",false))
            throw new IllegalArgumentException("Confirme a posição segura e digite TESTAR ESCOVA.");
        JSONObject report=ok().put("procedure","enter BIT -> 10s -> confirm code 5 in 99-5 -> execute 99-2=5 -> wait 33s -> normal");
        JSONArray req=new JSONArray().put(new JSONObject()
            .put("did",device.deviceId()).put("siid",99).put("piid",5));
        JSONArray errors=new JSONArray();
        boolean entered=false;
        try{
            report.put("enter_ack",safe(device.setProperty(99,1,"BIT")));
            entered=true;
            SystemClock.sleep(10000);
            JSONObject testList=null;
            for(int i=0;i<3;i++){
                try{
                    if(i>0)device.handshake();
                    JSONArray reply=device.getProperties(req);
                    JSONObject item=reply.optJSONObject(0);
                    if(item!=null&&item.optInt("code",-1)==0){
                        Object raw=item.opt("value");
                        if(raw instanceof JSONObject)testList=(JSONObject)raw;
                        else if(raw!=null&&!JSONObject.NULL.equals(raw)&&!String.valueOf(raw).trim().isEmpty())
                            testList=new JSONObject(String.valueOf(raw));
                        if(testList!=null)break;
                    }
                    errors.put(new JSONObject().put("read_attempt",i+1).put("reply",reply));
                }catch(Exception e){
                    errors.put(new JSONObject().put("read_attempt",i+1).put("error",
                        e.getMessage()==null?"Falha de comunicação":e.getMessage()));
                }
                SystemClock.sleep(1300);
            }
            if(testList==null)throw new IllegalStateException("Lista BIT indisponível. Nenhum teste iniciado.");
            report.put("list_confirmed",testList);
            if(!testList.has("Rolling brush testing") || testList.optInt("Rolling brush testing",-1)!=5)
                throw new IllegalStateException("ID da escova diferente de 5. Teste bloqueado.");
            report.put("test_start_ack",safe(device.setProperty(99,2,5)));
            report.put("test_command_sent",true);
            report.put("expected_test","Rolling brush testing, duração oficial ~30 segundos");
            SystemClock.sleep(33000);
            report.put("observation_window_seconds",33);
        }catch(Exception e){
            report.put("test_error",e.getMessage()==null?"Falha de comunicação":e.getMessage());
        }finally{
            report.put("entered_bit",entered).put("read_errors",errors);
            attemptBitExit(report);
        }
        return report.put("warning","O teste pode parar sozinho por falha, ou continuar se a rede cair. Somente o robô anuncia PASS/FAIL. Não encoste na escova; desligue pelo botão físico se necessário.");
    }

'''
ss=ss.replace(anchor,method+anchor)
src.write_text(ss)
g=Path("app/build.gradle")
gg=g.read_text()
assert "versionCode 5; versionName '0.5.0'" in gg
g.write_text(gg.replace("versionCode 5; versionName '0.5.0'", "versionCode 6; versionName '0.6.0'"))
html=Path("app/src/main/assets/index.html")
hh=html.read_text()
needle='<button id="bitExit" class="btn danger" disabled>Tentar sair do BIT (recuperação)</button>'
assert needle in hh
hh=hh.replace(needle,'''
<div class="card stack" style="margin-top:18px">
<h3>Teste individual da escova principal</h3>
<p>Teste BIT oficial Rolling brush testing (ID 5). A escova pode girar por cerca de 30 segundos. O robô anuncia o resultado em inglês. Não encoste nas peças durante o teste.</p>
<label for="brushBitConfirm">Digite TESTAR ESCOVA</label>
<input id="brushBitConfirm" placeholder="TESTAR ESCOVA" autocomplete="off">
<button id="brushBitRun" class="btn primary" disabled>Testar somente a escova principal (~30 s)</button>
<pre id="brushBitResult" class="output">Aguardando teste.</pre>
</div>
<div style="margin-top:16px">'''+needle+'''</div>''')
hh=hh.replace("'runTestBtn','bitScan','bitExit']", "'runTestBtn','bitScan','bitExit','brushBitRun']")
js=r'''
async function runBrushBit(){if(!con||busy)return;setBusy(true);$('brushBitResult').textContent='Entrada BIT, consulta da lista e teste por cerca de 30 segundos... NÃO TOQUE NA ESCOVA. Aguarde a saída.';try{
 const r=await api('bit-main-brush',{confirmation:$('brushBitConfirm').value.trim(),safe_location:$('bitSafety').checked});
 $('brushBitResult').textContent=jsonText(r);
 if(!r.exit_confirmed_by_transport)toast('Saída BIT não confirmada! Desligue e ligue fisicamente.',true);
 else if(!r.test_command_sent)toast('Teste não executado; confira os detalhes.',true);
 else toast('Teste enviado. Informe a mensagem falada: passed ou failed.');
}catch(e){$('brushBitResult').textContent=e.message;toast('Erro: '+e.message,true)}finally{setBusy(false)}}
'''
assert 'async function runBitExit(){' in hh
hh=hh.replace('async function runBitExit(){',js+'\nasync function runBitExit(){')
hh=hh.replace("$('bitExit').onclick=runBitExit;", "$('bitExit').onclick=runBitExit;$('brushBitRun').onclick=runBrushBit;")
html.write_text(hh)
print("S40 Lab v0.6 patch applied: 30-second Rolling brush BIT, verified code 5, safe exit")


# --- v0.7: retry confirmed BIT entry once; safely gate brush test on live list
p=Path("app/src/main/java/br/s40lab/app/S40Bridge.java")
t=p.read_text()
start=t.index('    /** S40/H40 SOP: Rolling brush test runs about 30 seconds and announces pass/fail. */')
end=t.index('    /** Recovery command; does not enter BIT or run any test. */',start)
replacement=r'''
    /** Run rolling brush only after proof-of-BIT: firmware must list test 5. */
    private JSONObject bitMainBrush(JSONObject b)throws Exception{
        requireDevice();
        if(demo)throw new IllegalArgumentException("BIT indisponível em demonstração.");
        if(!"TESTAR ESCOVA".equals(b.optString("confirmation"))||!b.optBoolean("safe_location",false))
            throw new IllegalArgumentException("Confirme a posição segura e digite TESTAR ESCOVA.");
        JSONObject report=ok().put("procedure","enter BIT -> verify live 99-5 (up to 2 entry attempts) -> execute ONLY ID 5 -> wait 33s -> normal -> read 99-5");
        JSONArray req=new JSONArray().put(new JSONObject()
            .put("did",device.deviceId()).put("siid",99).put("piid",5));
        JSONArray events=new JSONArray();
        JSONObject testList=null;
        int usedEntry=0;
        try{
            for(int entry=1;entry<=2 && testList==null;entry++){
                usedEntry=entry;
                if(entry==2){
                    // If the first entry was not confirmed, request normal before trying BIT again.
                    try{
                        report.put("reset_before_retry",safe(device.setProperty(99,1,"normal")));
                    }catch(Exception e){
                        events.put(new JSONObject().put("entry",entry).put("stage","reset").put("error",String.valueOf(e.getMessage())));
                    }
                    SystemClock.sleep(2200);
                    try{device.handshake();}catch(Exception ignored){}
                }
                try {
                    Object ack=device.setProperty(99,1,"BIT");
                    report.put("enter_ack_"+entry,safe(ack));
                    JSONObject first=(ack instanceof JSONArray)?((JSONArray)ack).optJSONObject(0):((ack instanceof JSONObject)?(JSONObject)ack:null);
                    if(first==null||first.optInt("code",-1)!=0)
                        throw new IllegalStateException("Entrada BIT não aceita no ciclo "+entry);
                    SystemClock.sleep(10000);
                    for(int i=0;i<6;i++){
                        try{
                            if(i>0)device.handshake();
                            JSONArray reply=device.getProperties(req);
                            JSONObject item=reply.optJSONObject(0);
                            if(item!=null && item.optInt("code",-1)==0){
                                Object raw=item.opt("value");
                                if(raw instanceof JSONObject)testList=(JSONObject)raw;
                                else if(raw!=null&&!JSONObject.NULL.equals(raw)&&!String.valueOf(raw).trim().isEmpty())
                                    testList=new JSONObject(String.valueOf(raw));
                                if(testList!=null){
                                    report.put("list_read_attempt",i+1);
                                    break;
                                }
                            }
                            events.put(new JSONObject().put("entry",entry).put("poll",i+1).put("reply",reply));
                        }catch(Exception e){
                            events.put(new JSONObject().put("entry",entry).put("poll",i+1).put("error",String.valueOf(e.getMessage())));
                        }
                        if(i<5)SystemClock.sleep(1500);
                    }
                }catch(Exception e){
                    events.put(new JSONObject().put("entry",entry).put("stage","enter").put("error",String.valueOf(e.getMessage())));
                }
            }
            report.put("entry_attempts",usedEntry);
            if(testList==null)throw new IllegalStateException("Entrada BIT não confirmada pela lista 99-5. Motor não acionado.");
            report.put("list_confirmed",testList);
            if(testList.optInt("Rolling brush testing",-1)!=5)
                throw new IllegalStateException("Lista BIT não confirma Rolling brush testing = 5. Motor não acionado.");
            Object startAck=device.setProperty(99,2,5);
            report.put("test_start_ack",safe(startAck));
            JSONObject first=(startAck instanceof JSONArray)?((JSONArray)startAck).optJSONObject(0):((startAck instanceof JSONObject)?(JSONObject)startAck:null);
            if(first==null||first.optInt("code",-1)!=0)
                throw new IllegalStateException("Comando 99-2=5 não aceito. Motor não confirmado.");
            report.put("test_command_accepted",true)
                  .put("expected_test","Rolling brush testing por aproximadamente 30s; resultado falado pelo S40");
            SystemClock.sleep(33000);
            report.put("observation_window_seconds",33);
        }catch(Exception e){
            report.put("test_error",e.getMessage()==null?"Falha de comunicação":e.getMessage());
        }finally{
            report.put("read_events",events).put("entry_attempts",usedEntry);
            attemptBitExit(report);
            if(report.optBoolean("exit_confirmed_by_transport",false)){
                try{
                    SystemClock.sleep(1800);
                    JSONArray check=device.getProperties(req);
                    report.put("exit_list_read",check);
                    JSONObject item=check.optJSONObject(0);
                    if(item!=null && item.optInt("code",-1)==0){
                        Object val=item.opt("value");
                        report.put("exit_list_empty",
                            val==null||JSONObject.NULL.equals(val)||String.valueOf(val).trim().isEmpty());
                    }
                }catch(Exception e){
                    report.put("exit_list_check_error",String.valueOf(e.getMessage()));
                }
            }
        }
        return report.put("warning","99-2=5 só é enviado após lista BIT confirmar identificador 5. ACK não confirma resultado do motor. Saída incerta: reinicie pelo botão físico. Não toque na escova durante o BIT.");
    }

'''
t=t[:start]+replacement+t[end:]
p.write_text(t)
g=Path("app/build.gradle")
gs=g.read_text()
assert "versionCode 6; versionName '0.6.0'" in gs
g.write_text(gs.replace("versionCode 6; versionName '0.6.0'","versionCode 7; versionName '0.7.0'"))
h=Path("app/src/main/assets/index.html")
hs=h.read_text()
assert "Testar somente a escova principal (~30 s)" in hs
hs=hs.replace("Teste BIT oficial Rolling brush testing (ID 5). A escova pode girar por cerca de 30 segundos.",
              "Teste BIT Rolling brush testing (ID 5). A entrada será confirmada pela lista do firmware antes do acionamento, com até duas tentativas. A escova pode girar por cerca de 30 segundos.")
hs=hs.replace("if(!r.exit_confirmed_by_transport)toast('Saída BIT não confirmada! Desligue e ligue fisicamente.',true);",
              "if(!r.exit_confirmed_by_transport||r.exit_list_empty===false)toast('Saída BIT não verificada: desligue e ligue fisicamente.',true);")
hs=hs.replace("else if(!r.test_command_sent)toast('Teste não executado; confira os detalhes.',true);",
              "else if(!r.test_command_accepted)toast('Teste não executado; confira os detalhes.',true);")
h.write_text(hs)
print("S40 Lab v0.7 patch ready: automatic guarded BIT retry, exit-list probe")


# --- v0.8: All 11 S40 BIT tests, selectable with one-touch tiles and per-test safeguards
src=Path("app/src/main/java/br/s40lab/app/S40Bridge.java")
ss=src.read_text()
assert 'case "bit-main-brush":answer=bitMainBrush(b);break;' in ss
ss=ss.replace('case "bit-main-brush":answer=bitMainBrush(b);break;',
              'case "bit-main-brush":answer=bitMainBrush(b);break;\n                case "bit-any-test":answer=bitAnyTest(b);break;')
anchor='    /** Run rolling brush only after proof-of-BIT: firmware must list test 5. */'
assert anchor in ss
method=r'''
    private static final String[] BIT_NAMES={
        "Collision plate testing","Downview testing","Duty box testing",
        "Edge brush testing","Fan testing","IMU testing","LDS testing",
        "Pump testing","Rolling brush testing","Wheel testing","*Test all"
    };
    private static final int[] BIT_IDS={7,8,15,4,3,13,12,16,5,2,1};
    private static final int[] BIT_WAIT_SECONDS={65,50,60,45,55,75,40,45,35,50,240};

    /** Each test is selected from a strict whitelist and checked against the live device catalog. */
    private JSONObject bitAnyTest(JSONObject b)throws Exception{
        requireDevice();
        if(demo)throw new IllegalArgumentException("BIT apenas com robô físico conectado.");
        String name=b.optString("test_name","");
        int index=-1;
        for(int i=0;i<BIT_NAMES.length;i++){
            if(BIT_NAMES[i].equals(name)){index=i;break;}
        }
        if(index<0)throw new IllegalArgumentException("Teste BIT desconhecido ou não permitido.");
        final int id=BIT_IDS[index],seconds=BIT_WAIT_SECONDS[index];
        final boolean all=id==1;
        String phrase=all?"TESTAR TODOS":"TESTAR "+id;
        if(!phrase.equals(b.optString("confirmation"))||!b.optBoolean("safe_location",false))
            throw new IllegalArgumentException("Marque a segurança e digite "+phrase+".");
        if(all&&!b.optBoolean("all_tests_acknowledged",false))
            throw new IllegalArgumentException("O modo todos exige confirmação adicional; as rodas, escovas e bomba podem ser acionadas.");
        final JSONObject report=ok().put("test_name",name).put("test_id",id)
            .put("wait_seconds",seconds).put("procedure",
             "verify live BIT list (max 2 attempts) -> write 99-2/test_id -> wait -> request normal -> check BIT catalog");
        final JSONArray req=new JSONArray().put(new JSONObject()
            .put("did",device.deviceId()).put("siid",99).put("piid",5));
        final JSONArray events=new JSONArray();
        JSONObject available=null;
        int entryAttempts=0;
        boolean commandAccepted=false;
        try{
            for(int cycle=1;cycle<=2&&available==null;cycle++){
                entryAttempts=cycle;
                if(cycle==2){
                    try {report.put("reset_before_retry",safe(device.setProperty(99,1,"normal")));}
                    catch(Exception e){events.put(new JSONObject().put("stage","reset").put("error",String.valueOf(e.getMessage())));}
                    SystemClock.sleep(2200);
                    try{device.handshake();}catch(Exception ignored){}
                }
                try{
                    Object ack=device.setProperty(99,1,"BIT");
                    report.put("enter_ack_"+cycle,safe(ack));
                    JSONObject first=(ack instanceof JSONArray)?((JSONArray)ack).optJSONObject(0):
                        ((ack instanceof JSONObject)?(JSONObject)ack:null);
                    if(first==null||first.optInt("code",-1)!=0)
                        throw new IllegalStateException("Entrada BIT não aceita.");
                    SystemClock.sleep(10000);
                    for(int poll=1;poll<=6;poll++){
                        try{
                            if(poll>1)device.handshake();
                            JSONArray data=device.getProperties(req);
                            JSONObject item=data.optJSONObject(0);
                            if(item!=null&&item.optInt("code",-1)==0){
                                Object raw=item.opt("value");
                                if(raw instanceof JSONObject)available=(JSONObject)raw;
                                else if(raw!=null&&!JSONObject.NULL.equals(raw)&&!String.valueOf(raw).trim().isEmpty())
                                    available=new JSONObject(String.valueOf(raw));
                                if(available!=null) {
                                    report.put("catalog_poll",poll);
                                    break;
                                }
                            }
                            events.put(new JSONObject().put("entry",cycle).put("poll",poll).put("reply",data));
                        }catch(Exception e){
                            events.put(new JSONObject().put("entry",cycle).put("poll",poll)
                                .put("error",e.getMessage()==null?"Falha de rede":e.getMessage()));
                        }
                        if(poll<6)SystemClock.sleep(1500);
                    }
                }catch(Exception e){
                    events.put(new JSONObject().put("entry",cycle).put("stage","enter")
                        .put("error",e.getMessage()==null?"Falha de rede":e.getMessage()));
                }
            }
            if(available==null)
                throw new IllegalStateException("BIT não confirmado: lista 99-5 vazia. O teste NÃO foi acionado.");
            report.put("catalog_confirmed",true);
            final int actualId=available.optInt(name,-1);
            if(actualId!=id)
                throw new IllegalStateException("ID do teste no firmware diverge. Esperado "+id+", obtido "+actualId+". Execução bloqueada.");
            report.put("test_id_verified",true);
            Object startAck=device.setProperty(99,2,id);
            report.put("start_ack",safe(startAck));
            JSONObject first=(startAck instanceof JSONArray)?((JSONArray)startAck).optJSONObject(0):
                ((startAck instanceof JSONObject)?(JSONObject)startAck:null);
            if(first==null||first.optInt("code",-1)!=0)
                throw new IllegalStateException("Comando do teste rejeitado: saída será solicitada.");
            commandAccepted=true;
            report.put("test_command_accepted",true);
            // Some tests require human interaction; the firmware is responsible for pass/fail.
            SystemClock.sleep(seconds*1000L);
            report.put("observation_completed",true);
        }catch(Exception e){
            report.put("test_error",e.getMessage()==null?"Falha de rede":e.getMessage());
        }finally{
            report.put("entry_attempts",entryAttempts).put("events",events);
            report.put("test_command_accepted",commandAccepted);
            attemptBitExit(report);
            if(report.optBoolean("exit_confirmed_by_transport",false)){
                for(int tries=1;tries<=3;tries++){
                    try{
                        SystemClock.sleep(1400);
                        if(tries>1)device.handshake();
                        JSONArray check=device.getProperties(req);
                        JSONObject item=check.optJSONObject(0);
                        if(item!=null&&item.optInt("code",-1)==0){
                            Object val=item.opt("value");
                            boolean empty=val==null||JSONObject.NULL.equals(val)||String.valueOf(val).trim().isEmpty();
                            report.put("exit_list_empty",empty).put("exit_check_attempt",tries);
                            if(empty)report.put("exit_evidence","Lista BIT vazia após NORMAL.");
                            else report.put("exit_evidence","Lista BIT ainda acessível.");
                            break;
                        }
                    }catch(Exception e){
                        report.put("exit_check_error",e.getMessage()==null?"Sem resposta":e.getMessage());
                    }
                }
            }
        }
        return report.put("warning","Nenhum resultado PASS/FAIL é inferido do code 0: observe a fala do robô. Saída não comprovada: reinicie pelo botão físico. Não toque em partes móveis durante testes.");
    }

'''
ss=ss.replace(anchor,method+anchor)
src.write_text(ss)
grad=Path("app/build.gradle")
gs=grad.read_text()
assert "versionCode 7; versionName '0.7.0'" in gs
grad.write_text(gs.replace("versionCode 7; versionName '0.7.0'","versionCode 8; versionName '0.8.0'"))
h=Path("app/src/main/assets/index.html")
hs=h.read_text()
import json,html
test_opts=[
    {"key":"Collision plate testing","id":7,"pt":"Para-choque frontal","info":"Após a mensagem do robô, aperte e solte os lados esquerdo e direito do para-choque, seguindo os avisos de voz. Robô apoiado no chão.","sec":65},
    {"key":"Downview testing","id":8,"pt":"Sensores de queda","info":"Após a mensagem, erga o robô e coloque-o novamente no chão, conforme a instrução falada. Mantenha-o firme.","sec":50},
    {"key":"Duty box testing","id":15,"pt":"Reservatório de pó","info":"Após a mensagem, abra a tampa superior, remova o reservatório de pó e recoloque-o. Não toque em partes móveis.","sec":60},
    {"key":"Edge brush testing","id":4,"pt":"Escova lateral","info":"A escova lateral girará automaticamente. Mantenha fios, cabelos, mãos e objetos afastados.","sec":45},
    {"key":"Fan testing","id":3,"pt":"Ventilador / sucção","info":"Robô na posição normal sobre o piso. O ventilador passa por três níveis; espere a mensagem de resultado.","sec":55},
    {"key":"IMU testing","id":13,"pt":"Sensor de orientação (IMU)","info":"Após a fala de início, gire o robô 360 graus no lugar, conforme a instrução técnica. Cuidado com partes móveis.","sec":75},
    {"key":"LDS testing","id":12,"pt":"Laser / LiDAR","info":"O conjunto de radar gira por aproximadamente 30 segundos. Não toque na torre giratória.","sec":40},
    {"key":"Pump testing","id":16,"pt":"Bomba de água","info":"Prepare o reservatório de água montado de acordo com o procedimento do fabricante. Ouça se a bomba funciona. Não faça testes repetidos a seco.","sec":45},
    {"key":"Rolling brush testing","id":5,"pt":"Escova principal","info":"A escova principal pode girar por cerca de 30 segundos. Não a toque ou segure durante o teste.","sec":35},
    {"key":"Wheel testing","id":2,"pt":"Rodas motrizes","info":"Apoie o robô INVERTIDO, estável, em suportes que não pressionem a torre LiDAR. Rodas livres, dedos afastados.","sec":50},
    {"key":"*Test all","id":1,"pt":"TODOS os testes (sequência)","info":"ATENÇÃO: sequencia automaticamente testes com instruções incompatíveis de posição, inclusive rodas e escovas. Exige supervisão constante e pode durar vários minutos. Use preferencialmente testes individuais.","sec":240}
]
choices='\n'.join(
    '<button class="btn bit-test-choice" type="button" data-bit-key="'+html.escape(t["key"],quote=True)+'" disabled>'
    +html.escape(t["pt"])+' · '+str(t["id"])+'</button>' for t in test_opts
)
panel='''<div class="card stack section" id="bitAllPanel" style="margin-top:18px">
<h3>Todos os testes disponíveis no BIT</h3>
<p class="note">Escolha um teste abaixo. O aplicativo verifica o código na lista do próprio S40 antes de executar. Não executa calibrações.</p>
<div class="grid" id="bitChoiceGrid">'''+choices+'''</div>
<div class="notice blue" id="bitSelectedHelp">Selecione um teste para ver a posição correta do robô e o que observar.</div>
<div><label for="bitChoiceConfirmation">Confirmação específica (mostrada após selecionar)</label>
<input id="bitChoiceConfirmation" autocomplete="off" placeholder="Selecione um teste"/></div>
<label class="checkline" id="allTestsExtraRow" style="display:none"><input id="allTestsExtra" type="checkbox" />
Entendo que executar TODOS pode acionar rodas, escovas e bomba em sequência e exige mudar a posição e interagir sob supervisão.</label>
<button id="runSelectedBit" class="btn primary block" disabled>Executar teste selecionado</button>
<pre id="bitSelectedResult" class="output">Nenhum teste executado.</pre>
<p class="note">Durante os testes, siga os avisos de voz. Não toque nos motores em funcionamento. Se o robô não sair do BIT, use o botão físico para reiniciar.</p>
</div>'''
needle='<div style="margin-top:16px"><button id="bitExit"'
assert needle in hs
hs=hs.replace(needle,panel+'\n'+needle)
assert "'runTestBtn','bitScan','bitExit','brushBitRun']" in hs
hs=hs.replace("'runTestBtn','bitScan','bitExit','brushBitRun']",
              "'runTestBtn','bitScan','bitExit','brushBitRun','runSelectedBit']")
assert "document.querySelectorAll('.act, .setting button')" in hs
hs=hs.replace("document.querySelectorAll('.act, .setting button')",
              "document.querySelectorAll('.act, .setting button, .bit-test-choice')")
init_needle="$('brushBitRun').onclick=runBrushBit;"
assert init_needle in hs
hs=hs.replace(init_needle,init_needle+"setupBitTestCatalog();")
jsconf=json.dumps(test_opts,ensure_ascii=False)
js=r'''
const bitTestSpecs=BIT_SPECS_HERE;
let bitSelected=null;
function setupBitTestCatalog(){
 document.querySelectorAll('.bit-test-choice').forEach(btn=>{
   btn.onclick=()=>{
     if(busy)return;
     let spec=bitTestSpecs.find(t=>t.key===btn.dataset.bitKey);
     if(!spec)return;
     bitSelected=spec;
     document.querySelectorAll('.bit-test-choice').forEach(el=>{
       el.style.borderColor=el===btn?'#ffa45c':'';
       el.style.background=el===btn?'#493527':'';
     });
     const phrase=spec.id===1?'TESTAR TODOS':'TESTAR '+spec.id;
     $('bitSelectedHelp').textContent=spec.pt+' (ID '+spec.id+'): '+spec.info+' Duração máxima de observação: '+spec.sec+' segundos. Confirme digitando '+phrase+'.';
     $('bitChoiceConfirmation').placeholder=phrase;
     $('bitChoiceConfirmation').value='';
     $('allTestsExtraRow').style.display=spec.id===1?'flex':'none';
     $('allTestsExtra').checked=false;
   };
 });
}
async function runSelectedBit(){
 if(!con||busy||!bitSelected){toast('Escolha um teste antes.',true);return;}
 let id=bitSelected.id;
 let phrase=id===1?'TESTAR TODOS':'TESTAR '+id;
 if($('bitChoiceConfirmation').value.trim()!==phrase){
   toast('Digite '+phrase+' exatamente para confirmar.',true);return;
 }
 if(!$('bitSafety').checked){toast('Marque a confirmação de segurança no início da aba BIT.',true);return;}
 if(id===1&&!$('allTestsExtra').checked){
   toast('Confirme também o risco de executar todos os testes.',true);return;
 }
 if(!window.confirm('Executar '+bitSelected.pt+'? Siga a posição e as instruções indicadas.')){
   return;
 }
 setBusy(true);
 $('bitSelectedResult').textContent='Executando '+bitSelected.pt+'. Aguarde o teste e a solicitação de saída do BIT; ouça os anúncios do robô.';
 try{
   const r=await api('bit-any-test',{
      test_name:bitSelected.key,
      confirmation:phrase,
      safe_location:$('bitSafety').checked,
      all_tests_acknowledged:$('allTestsExtra').checked
   });
   $('bitSelectedResult').textContent=jsonText(r);
   if(!r.exit_confirmed_by_transport||r.exit_list_empty===false)
      toast('Saída BIT não verificada. Reinicie pelo botão físico se necessário.',true);
   else if(!r.test_command_accepted)
      toast('Teste NÃO foi iniciado. Confira o resultado.',true);
   else
      toast('Teste enviado. Informe se o robô disse Test passed ou Test failed.');
 }catch(e){
   $('bitSelectedResult').textContent=e.message;
   toast('Erro do teste: '+e.message,true);
 }finally{setBusy(false)}
}
'''.replace('BIT_SPECS_HERE',jsconf)
needlejs='async function runBitExit(){'
assert needlejs in hs
hs=hs.replace(needlejs,js+'\n'+needlejs)
hs=hs.replace("setupBitTestCatalog();","setupBitTestCatalog();$('runSelectedBit').onclick=runSelectedBit;")
hs=hs.replace("S40 Lab v0.2 · Interface experimental", "S40 Lab v0.8 · Interface experimental")
h.write_text(hs)
print("S40 Lab v0.8 patch: 11 BIT entries, live ID verification, required per-test instructions, guarded execution")


# --- v0.9: persistent manual BIT session with explicit entry, selected tests, explicit exit
p=Path("app/src/main/java/br/s40lab/app/S40Bridge.java")
t=p.read_text()
anchor='    private static final String[] BIT_NAMES={'
assert anchor in t
t=t.replace(anchor,'    private boolean manualBitSession=false;\n'+anchor)
anchor='                case "bit-any-test":answer=bitAnyTest(b);break;'
assert anchor in t
t=t.replace(anchor,anchor+'''
                case "bit-session-start":answer=bitSessionStart(b);break;
                case "bit-session-status":answer=bitSessionStatus(b);break;
                case "bit-session-test":answer=bitSessionTest(b);break;
                case "bit-session-exit":answer=bitSessionExit(b);break;''')
assert 'case "connect":answer=connect(b);break;' in t
t=t.replace('case "connect":answer=connect(b);break;', 'case "connect":manualBitSession=false;answer=connect(b);break;')
t=t.replace('case "disconnect":device=null;demo=false;ip=null;', 'case "disconnect":manualBitSession=false;device=null;demo=false;ip=null;')
anchor='    /** Each test is selected from a strict whitelist and checked against the live device catalog. */'
assert anchor in t
code=r'''
    /** Returns null if the device reports an empty catalog; throws on transport errors. */
    private JSONObject liveBitCatalog()throws Exception{
        JSONArray req=new JSONArray().put(new JSONObject()
            .put("did",device.deviceId()).put("siid",99).put("piid",5));
        JSONArray data=device.getProperties(req);
        JSONObject item=data.optJSONObject(0);
        if(item==null||item.optInt("code",-1)!=0)
            throw new IllegalStateException("Sem confirmação da lista BIT 99-5.");
        Object raw=item.opt("value");
        if(raw==null||JSONObject.NULL.equals(raw)||String.valueOf(raw).trim().isEmpty())
            return null;
        if(raw instanceof JSONObject)return (JSONObject)raw;
        return new JSONObject(String.valueOf(raw));
    }
    private JSONObject verifiedBitCatalog(JSONObject report,int polls)throws Exception{
        JSONArray events=new JSONArray();
        JSONObject list=null;
        for(int poll=1;poll<=polls;poll++){
            try{
                if(poll>1)device.handshake();
                list=liveBitCatalog();
                if(list!=null){report.put("catalog_read_attempt",poll);break;}
                events.put(new JSONObject().put("poll",poll).put("note","Lista vazia"));
            }catch(Exception e){
                events.put(new JSONObject().put("poll",poll).put("error",
                    e.getMessage()==null?"Falha de comunicação":e.getMessage()));
            }
            if(poll<polls)SystemClock.sleep(1500);
        }
        report.put("catalog_events",events);
        return list;
    }
    /** Start only, do not automatically leave if entry is successful. */
    private JSONObject bitSessionStart(JSONObject b)throws Exception{
        requireDevice();
        if(demo)throw new IllegalArgumentException("BIT indisponível na demonstração.");
        if(!b.optBoolean("safe_location",false)||
            !"ENTRAR BIT".equals(b.optString("confirmation")))
            throw new IllegalArgumentException("Confirme o local seguro e digite ENTRAR BIT.");
        JSONObject report=ok().put("procedure","enter BIT once, verify 99-5, keep session active");
        JSONObject catalogNow=null;
        try{catalogNow=liveBitCatalog();}catch(Exception e){
            report.put("initial_check_error",e.getMessage());
        }
        if(catalogNow!=null){
            manualBitSession=true;
            return report.put("already_active",true).put("bit_active",true)
                .put("catalog",catalogNow).put("note","Sessão BIT já detectada. Nenhum comando BIT reenviado.");
        }
        JSONArray attempts=new JSONArray();
        for(int entry=1;entry<=2&&catalogNow==null;entry++){
            JSONObject record=new JSONObject().put("entry_attempt",entry);
            attempts.put(record);
            if(entry==2){
                try{record.put("reset_ack",safe(device.setProperty(99,1,"normal"))); }
                catch(Exception e){record.put("reset_error",e.getMessage());}
                SystemClock.sleep(2000);
                try{device.handshake();}catch(Exception ignore){}
            }
            try{
                Object ack=device.setProperty(99,1,"BIT");
                record.put("ack",safe(ack));
                JSONObject item=(ack instanceof JSONArray)?((JSONArray)ack).optJSONObject(0):
                    ((ack instanceof JSONObject)?(JSONObject)ack:null);
                if(item==null||item.optInt("code",-1)!=0)
                    throw new IllegalStateException("Comando BIT não aceito.");
                SystemClock.sleep(10000);
                catalogNow=verifiedBitCatalog(record,6);
            }catch(Exception e){record.put("entry_error",
                e.getMessage()==null?"Falha de comunicação":e.getMessage());}
        }
        report.put("entry_attempts",attempts);
        if(catalogNow==null){
            manualBitSession=false;
            attemptBitExit(report);
            return report.put("bit_active",false)
                .put("error_message","Entrada não confirmada; solicitação NORMAL enviada. Se houver dúvida, reinicie pelo botão físico.");
        }
        manualBitSession=true;
        return report.put("bit_active",true).put("catalog",catalogNow)
            .put("warning","Sessão BIT permanece aberta até usar Sair do BIT manualmente. Não inicie limpeza convencional.");
    }
    /** One live-status read; restoring a session after relaunch requires active user click. */
    private JSONObject bitSessionStatus(JSONObject b)throws Exception{
        requireDevice();
        if(demo)throw new IllegalArgumentException("BIT indisponível na demonstração.");
        JSONObject report=ok();
        try{
            JSONObject catalogNow=liveBitCatalog();
            manualBitSession=(catalogNow!=null);
            return report.put("bit_active",manualBitSession)
                .put("catalog",catalogNow==null?JSONObject.NULL:catalogNow)
                .put("note",manualBitSession?"Lista BIT presente: sessão recuperada.":"Lista BIT vazia: compatível com modo normal.");
        }catch(Exception e){
            manualBitSession=false;
            return report.put("bit_active",JSONObject.NULL)
                .put("status_error",e.getMessage()==null?"Sem resposta":e.getMessage())
                .put("warning","Estado desconhecido; não execute testes. Se necessário, reinicie pelo botão físico.");
        }
    }
    /** Execute exactly one manually selected test, without BIT entry or exit. */
    private JSONObject bitSessionTest(JSONObject b)throws Exception{
        requireDevice();
        if(demo)throw new IllegalArgumentException("BIT indisponível na demonstração.");
        String name=b.optString("test_name","");
        int index=-1;
        for(int i=0;i<BIT_NAMES.length;i++)if(BIT_NAMES[i].equals(name))index=i;
        if(index<0)throw new IllegalArgumentException("Teste não reconhecido.");
        int id=BIT_IDS[index],wait=BIT_WAIT_SECONDS[index];
        if(id==1)throw new IllegalArgumentException("Teste automático de todos desativado: execute cada um manualmente.");
        if(!manualBitSession)throw new IllegalStateException("Sessão BIT não confirmada. Entre no BIT ou use Verificar estado.");
        if(!b.optBoolean("safe_location",false)||
            !("TESTAR "+id).equals(b.optString("confirmation")))
            throw new IllegalArgumentException("Confirme posição segura e digite TESTAR "+id+".");
        JSONObject report=ok().put("test_name",name).put("test_id",id)
            .put("procedure","verify BIT active -> run only selected test -> remain in BIT")
            .put("observation_seconds",wait);
        JSONObject list=null;
        try{list=liveBitCatalog();}catch(Exception e){
            return report.put("test_command_accepted",false)
                .put("test_error","Não foi possível confirmar BIT: "+e.getMessage());
        }
        if(list==null){
            manualBitSession=false;
            return report.put("test_command_accepted",false)
                .put("test_error","Lista 99-5 vazia. Motor e sensores NÃO acionados.");
        }
        if(list.optInt(name,-1)!=id)
            return report.put("test_command_accepted",false)
                .put("test_error","ID do teste não corresponde à lista do robô. Execução bloqueada.");
        report.put("catalog_confirmed",true);
        Object ack=device.setProperty(99,2,id);
        report.put("start_ack",safe(ack));
        JSONObject item=(ack instanceof JSONArray)?((JSONArray)ack).optJSONObject(0):
            ((ack instanceof JSONObject)?(JSONObject)ack:null);
        boolean accepted=item!=null&&item.optInt("code",-1)==0;
        report.put("test_command_accepted",accepted);
        if(accepted)SystemClock.sleep(wait*1000L);
        return report.put("bit_remains_requested",true)
            .put("warning","BIT NÃO é encerrado após este teste. Ouça o PASS/FAIL do robô e use Sair do BIT manualmente ao terminar.");
    }
    /** Explicitly leave BIT. Distinguish transport ack from proof by catalog. */
    private JSONObject bitSessionExit(JSONObject b)throws Exception{
        requireDevice();
        if(demo)throw new IllegalArgumentException("Apenas o robô real.");
        if(!"SAIR BIT".equals(b.optString("confirmation")))
            throw new IllegalArgumentException("Confirme SAIR BIT.");
        JSONObject report=ok().put("procedure","request normal 99-1; verify 99-5 empty");
        attemptBitExit(report);
        boolean verified=false;
        JSONArray events=new JSONArray();
        for(int i=1;i<=4;i++){
            try{
                SystemClock.sleep(1500);
                if(i>1)device.handshake();
                JSONObject list=liveBitCatalog();
                if(list==null){verified=true;report.put("exit_check_attempt",i);break;}
                events.put(new JSONObject().put("attempt",i).put("result","Catálogo BIT ainda presente"));
            }catch(Exception e){
                events.put(new JSONObject().put("attempt",i).put("error",
                    e.getMessage()==null?"Sem resposta":e.getMessage()));
            }
        }
        manualBitSession=false;
        report.put("exit_verified_by_empty_catalog",verified).put("exit_checks",events)
            .put("bit_active",verified?false:JSONObject.NULL);
        if(!verified)report.put("warning",
            "Saída não verificada. Pare os testes; desligue e ligue pelo botão físico se permanecer no BIT.");
        return report;
    }

'''
t=t.replace(anchor,code+anchor)
p.write_text(t)
g=Path("app/build.gradle")
gs=g.read_text()
assert "versionCode 8; versionName '0.8.0'" in gs
g.write_text(gs.replace("versionCode 8; versionName '0.8.0'",
                         "versionCode 9; versionName '0.9.0'"))
h=Path("app/src/main/assets/index.html")
html=h.read_text()
import re
# Replace old per-test automatic BIT UI with manual-session controls, preserving tile selection IDs.
prefix='''<section id="bit" class="page">
<div class="heading"><h2>BIT manual · Sessão única</h2><p>Entre uma vez, execute os testes individuais que desejar e saia pelo botão Sair do BIT.</p></div>
<div class="card stack">
<div class="notice red">O BIT movimenta componentes. Mantenha o robô em local seguro, com supervisão contínua. Não feche o aplicativo nem desconecte sem sair do BIT. Se perder a comunicação, reinicie pelo botão físico.</div>
<label class="checkline"><input type="checkbox" id="bitSafety"> Robô estável, afastado de quedas, pessoas e animais; vou seguir o posicionamento de cada teste.</label>
<div><label for="bitStartConfirm">Para entrar digite ENTRAR BIT</label><input id="bitStartConfirm" placeholder="ENTRAR BIT" autocomplete="off"/></div>
<div class="row" style="flex-wrap:wrap;gap:10px">
<button id="bitSessionStart" class="btn primary" disabled>1. Entrar no BIT</button>
<button id="bitSessionStatus" class="btn" disabled>Verificar estado do BIT</button>
<button id="bitExit" class="btn danger" disabled>3. Sair do BIT</button>
</div>
<div class="notice blue" id="bitSessionState">BIT não confirmado. Clique em Entrar no BIT antes de escolher testes.</div>
<pre id="bitOutput" class="output">Nenhuma sessão BIT iniciada.</pre>
</div>
<div class="card stack section" id="bitAllPanel" style="margin-top:18px">
<h3>2. Escolher e executar testes individualmente</h3>
<p class="note">Os testes NÃO saem do BIT automaticamente. Altere a posição do robô somente depois que o teste anterior terminar e com componentes parados.</p>
<div class="grid" id="bitChoiceGrid">'''
pat=r'(?s)<section id="bit" class="page">.*?<div class="grid" id="bitChoiceGrid">'
html,n=re.subn(pat,prefix,html,count=1)
assert n==1
# Remove Test-all tile but preserve other ten choices; no automatic sequence in manual mode.
html,n=re.subn(r'<button class="btn bit-test-choice" type="button" data-bit-key="\*Test all" disabled>.*?</button>', '',html,count=1)
assert n==1
# Replace old bottom content (keeps test grid, description and button) from after panel until before next section.
endpattern=r'(?s)<p class="note">Durante os testes, siga os avisos de voz\..*?</div></section>\s*<section id="registros" class="page">'
endreplace='''<p class="note">Quando terminar, use o botão “3. Sair do BIT” no topo. O S40 deve parar todos os testes antes de você mudar sua posição. Se houver timeout na saída, use o botão físico para reiniciar.</p>
</div></section>
<section id="registros" class="page">'''
html,n=re.subn(endpattern,endreplace,html,count=1)
assert n==1, "end section not found"
# Session widgets must participate in busy connection handling
assert "'bitScan','bitExit','brushBitRun','runSelectedBit'" in html
html=html.replace("'bitScan','bitExit','brushBitRun','runSelectedBit'",
                  "'bitSessionStart','bitSessionStatus','bitExit','runSelectedBit'")
# Update JS selection handling for manually selected test.
start=html.index('async function runSelectedBit(){')
end=html.index('async function runBitExit(){',start)
manual_js=r'''
let bitSessionUiActive=false;
function showSessionState(active){
 bitSessionUiActive=(active===true);
 $('bitSessionState').textContent=active===true
     ?'BIT ATIVO: escolha e execute os testes abaixo; ao terminar, clique em Sair do BIT.'
     :active===false
        ?'BIT inativo/fora do modo de testes. Clique em Entrar no BIT.'
        :'Estado do BIT incerto. Não execute testes. Verifique o modo ou reinicie pelo botão físico.';
 $('bitSessionState').style.borderColor=active===true?'#63b793':active===false?'':'#f27b87';
}
async function enterManualBit(){
 if(!con||busy)return;
 if(!$('bitSafety').checked||$('bitStartConfirm').value.trim()!=='ENTRAR BIT'){
   toast('Confirme o local seguro e digite ENTRAR BIT.',true);return;
 }
 if(!window.confirm('Entrar no BIT? O robô permanecerá nesse modo até você clicar em Sair do BIT.'))return;
 setBusy(true);
 $('bitOutput').textContent='Aguardando a lista de testes para confirmar entrada no BIT...';
 try{
  const r=await api('bit-session-start',{confirmation:'ENTRAR BIT',safe_location:true});
  $('bitOutput').textContent=jsonText(r);
  showSessionState(r.bit_active===true);
  if(r.bit_active===true){$('autoRefresh').checked=false;toast('BIT ativo. Selecione testes individualmente e saia manualmente.');}
  else toast('BIT não confirmado. Não execute testes.',true);
 }catch(e){showSessionState(null);$('bitOutput').textContent=e.message;toast(e.message,true);}
 finally{setBusy(false)}
}
async function verifyManualBit(){
 if(!con||busy)return;
 setBusy(true);
 try {
  let r=await api('bit-session-status',{});
  $('bitOutput').textContent=jsonText(r);
  showSessionState(r.bit_active);
  toast(r.bit_active===true?'BIT ativo.':'BIT não confirmado ou desligado.',r.bit_active!==true);
 }catch(e){showSessionState(null);toast('Não foi possível confirmar o modo: '+e.message,true);}
 finally{setBusy(false)}
}
async function exitManualBit(){
 if(!con||busy)return;
 if(!window.confirm('Enviar NORMAL e encerrar a sessão BIT? Certifique-se de que nenhum teste ainda está girando.'))return;
 setBusy(true);
 $('bitOutput').textContent='Enviando NORMAL e verificando lista BIT...';
 try{
  const r=await api('bit-session-exit',{confirmation:'SAIR BIT'});
  $('bitOutput').textContent=jsonText(r);
  showSessionState(r.exit_verified_by_empty_catalog===true?false:null);
  if(r.exit_verified_by_empty_catalog)toast('Saída do BIT compatível com modo normal.');
  else toast('Saída não comprovada. Reinicie pelo botão físico se continuar no BIT.',true);
 }catch(e){showSessionState(null);$('bitOutput').textContent=e.message;toast('Saída não confirmada: '+e.message,true);}
 finally{setBusy(false)}
}
async function runSelectedBit(){
 if(!con||busy||!bitSelected){toast('Escolha um teste antes.',true);return;}
 if(!bitSessionUiActive){toast('Entre no BIT e confirme a lista antes de executar.',true);return;}
 const id=bitSelected.id;
 if(id===1){toast('A sequência automática está desativada. Selecione testes individuais.',true);return;}
 let phrase='TESTAR '+id;
 if($('bitChoiceConfirmation').value.trim()!==phrase){
  toast('Digite '+phrase+' exatamente para confirmar.',true);return;
 }
 if(!$('bitSafety').checked){toast('Confirme o ambiente seguro.',true);return;}
 if(!window.confirm('Executar SOMENTE '+bitSelected.pt+' (ID '+id+') sem sair do BIT? Verifique a posição do robô.'))return;
 setBusy(true);
 $('bitSelectedResult').textContent='Executando '+bitSelected.pt+'; aguarde o resultado. O aplicativo NÃO sairá do BIT.';
 try{
  let r=await api('bit-session-test',{
   test_name:bitSelected.key,
   confirmation:phrase,
   safe_location:true
  });
  $('bitSelectedResult').textContent=jsonText(r);
  if(r.test_command_accepted)toast('Teste concluído no tempo de observação. BIT continua ativo.');
  else{
    if((r.test_error||'').includes('vazia'))showSessionState(false);
    toast('Teste não iniciado: veja o diagnóstico.',true);
  }
 }catch(e){$('bitSelectedResult').textContent=e.message;showSessionState(null);toast('Falha de comunicação. Verifique BIT antes de continuar.',true);}
 finally{setBusy(false)}
}
'''
html=html[:start]+manual_js+html[end:]
# Existing runBitExit is old/unused, remove to avoid ambiguity
start=html.index('async function runBitExit(){')
end=html.index('async function refreshLogs(){',start)
html=html[:start]+html[end:]
# Init handlers exact replacement
old="$('bitScan').onclick=runBitList;$('bitExit').onclick=runBitExit;$('brushBitRun').onclick=runBrushBit;setupBitTestCatalog();$('runSelectedBit').onclick=runSelectedBit;"
new="$('bitSessionStart').onclick=enterManualBit;$('bitSessionStatus').onclick=verifyManualBit;$('bitExit').onclick=exitManualBit;setupBitTestCatalog();$('runSelectedBit').onclick=runSelectedBit;"
assert old in html
html=html.replace(old,new)
# In setupBitTestCatalog, allTestsExtraRow and allTestsExtra elements remain as hidden backing; no auto button.
# Remove stray old runBitList and runBrushBit to avoid confusing API, if present.
# These orphan functions aren't wired to controls and are harmless.
html=html.replace('S40 Lab v0.8 · Interface experimental', 'S40 Lab v0.9 · Sessão BIT manual')
h.write_text(html)
print("S40 Lab v0.9 patch done: manual BIT session control, explicit safe test selection & exit")


# --- v1.0: asynchronous LAN transport (WebView does not freeze during S40 BIT tests)
bridge=Path("app/src/main/java/br/s40lab/app/S40Bridge.java")
b=bridge.read_text()
assert 'import android.webkit.JavascriptInterface;' in b
b=b.replace('import android.webkit.JavascriptInterface;',
'''import android.webkit.JavascriptInterface;
import android.webkit.WebView;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.RejectedExecutionException;''')
assert '    private final JSONObject catalog;' in b
b=b.replace('    private final JSONObject catalog;',
'''    private final WebView callbackWebView;
    private final ExecutorService ioQueue=Executors.newSingleThreadExecutor();
    private final JSONObject catalog;''')
assert 'public S40Bridge(AssetManager assets){' in b
b=b.replace('public S40Bridge(AssetManager assets){',
            'public S40Bridge(AssetManager assets, WebView webView){\n        callbackWebView=webView;')
needle='    @JavascriptInterface\n    public synchronized String request(String raw){'
assert needle in b
# A synchronous method remains for compatibility, but normal UI calls requestAsync.
async_java=r'''
    /** Nonblocking JS bridge: device work is serialized on a dedicated worker. */
    @JavascriptInterface
    public void requestAsync(final String raw,final String callbackId){
        if(callbackId==null||!callbackId.matches("[a-zA-Z0-9_-]{1,50}"))return;
        try{
            ioQueue.execute(()->{
                String result;
                try{ result=request(raw); }
                catch(Throwable e){
                    try{result=new JSONObject().put("ok",false).put("error",
                        "Falha interna de comunicação: "+e.getClass().getSimpleName()).toString();}
                    catch(Exception ignored){result="{\"ok\":false,\"error\":\"Falha interna\"}";}
                }
                final String finalResult=result;
                try{
                    callbackWebView.post(()->{
                        try{
                            callbackWebView.evaluateJavascript(
                                "window.s40NativeDone("+JSONObject.quote(callbackId)+","+
                                    JSONObject.quote(finalResult)+");",null);
                        }catch(Exception ignored){}
                    });
                }catch(Exception ignored){}
            });
        }catch(RejectedExecutionException ignored){}
    }

    public void close(){
        ioQueue.shutdownNow();
    }

'''
b=b.replace(needle,async_java+needle)
bridge.write_text(b)
activity=Path("app/src/main/java/br/s40lab/app/MainActivity.java")
a=activity.read_text()
assert '    private WebView web;' in a
a=a.replace('    private WebView web;', '    private WebView web;\n    private S40Bridge robotBridge;')
assert 'web.addJavascriptInterface(new S40Bridge(getAssets()), "S40Android");' in a
a=a.replace('web.addJavascriptInterface(new S40Bridge(getAssets()), "S40Android");',
'''robotBridge=new S40Bridge(getAssets(),web);
        web.addJavascriptInterface(robotBridge, "S40Android");''')
a=a.replace('    @Override protected void onDestroy() {\n',
            '    @Override protected void onDestroy() {\n        if(robotBridge!=null){robotBridge.close();robotBridge=null;}\n')
activity.write_text(a)
page=Path("app/src/main/assets/index.html")
ht=page.read_text()
needle="async function api(route,body=undefined){if(!window.S40Android)throw Error('Abra pelo aplicativo S40 Lab instalado, não pelo navegador.');let raw=S40Android.request(JSON.stringify({route:route,body:body===undefined?null:body}));let data=JSON.parse(raw);if(!data.ok)throw Error(data.error||'Falha de comunicação');return data}"
assert needle in ht
replacement=r'''const s40PendingCalls=new Map();
let s40CallSerial=0;
window.s40NativeDone=(id,raw)=>{
  const item=s40PendingCalls.get(id);
  if(!item)return;
  s40PendingCalls.delete(id);
  try{
    const data=JSON.parse(raw);
    if(data.ok)item.resolve(data);
    else item.reject(new Error(data.error||'Falha de comunicação'));
  }catch(err){item.reject(err)}
};
async function api(route,body=undefined){
 if(!window.S40Android)throw Error('Abra pelo aplicativo S40 Lab instalado, não pelo navegador.');
 const serialized=JSON.stringify({route,body:body===undefined?null:body});
 if(typeof S40Android.requestAsync==='function'){
   return new Promise((resolve,reject)=>{
     const id='s40_'+(++s40CallSerial);
     s40PendingCalls.set(id,{resolve,reject});
     try{S40Android.requestAsync(serialized,id)}
     catch(e){s40PendingCalls.delete(id);reject(e)}
   });
 }
 const data=JSON.parse(S40Android.request(serialized));
 if(!data.ok)throw Error(data.error||'Falha de comunicação');
 return data;
}'''
ht=ht.replace(needle,replacement)
# Fix a stale reference to a nonexistent checkbox that previously caused a UI exception
ht=ht.replace("$('autoRefresh').checked=false;","")
# Provide a live elapsed timer while the robot runs the BIT test on the native worker
old="""setBusy(true);
 $('bitSelectedResult').textContent='Executando '+bitSelected.pt+'; aguarde o resultado. O aplicativo NÃO sairá do BIT.';
 try{
  let r=await api('bit-session-test',"""
assert old in ht
new="""setBusy(true);
 const progressLabel=bitSelected.pt;
 const progressStart=Date.now();
 const progressEstimated=bitSelected.sec;
 const progressTimer=setInterval(()=>{
   const elapsed=Math.floor((Date.now()-progressStart)/1000);
   $('bitSelectedResult').textContent='Teste em andamento: '+progressLabel+'\\nTempo decorrido: '+elapsed+'s / ~'+progressEstimated+'s\\n\\nA interface continua disponível. Aguarde o aviso de PASS/FAIL do S40. O modo BIT permanece ativo.';
 },500);
 $('bitSelectedResult').textContent='Iniciando '+progressLabel+'. Aguardando resposta do S40...';
 try{
  let r=await api('bit-session-test',"""
ht=ht.replace(old,new)
old="finally{setBusy(false)}\n}\nasync function refreshLogs(){"
# Should be last runSelectedBit finally before refresh logs? need inspect transformed source contains before other code
if old not in ht:
    # prefix find ending of runSelectedBit between that and old dead functions
    pos=ht.find("async function runSelectedBit(){")
    print("Tail function:",ht[pos:pos+2200][-500:])
    raise AssertionError("Run test finally pattern missing")
ht=ht.replace(old,"finally{clearInterval(progressTimer);setBusy(false)}\n}\nasync function refreshLogs(){",1)
# UI copy
ht=ht.replace('S40 Lab v0.9 · Sessão BIT manual','S40 Lab v1.0 · BIT fluido')
page.write_text(ht)
grad=Path('app/build.gradle');gs=grad.read_text()
assert "versionCode 9; versionName '0.9.0'" in gs
grad.write_text(gs.replace("versionCode 9; versionName '0.9.0'","versionCode 10; versionName '1.0.0'"))
print("v1.0: requestAsync background worker + responsive WebView + live timer")


# --- v1.1: Finish on voice pass/fail, no fixed test waits, no typing TESTAR X
bridge=Path("app/src/main/java/br/s40lab/app/S40Bridge.java")
s=bridge.read_text()
assert 'private boolean manualBitSession=false;' in s
s=s.replace('private boolean manualBitSession=false;',
'''private boolean manualBitSession=false;
    private int manualBitPendingId=-1;
    private String manualBitPendingName="";''')
needle='                case "bit-session-test":answer=bitSessionTest(b);break;'
assert needle in s
s=s.replace(needle,needle+'\n                case "bit-session-finish":answer=bitSessionFinish(b);break;')
s=s.replace('case "connect":manualBitSession=false;answer=connect(b);break;',
            'case "connect":manualBitSession=false;manualBitPendingId=-1;answer=connect(b);break;')
s=s.replace('case "disconnect":manualBitSession=false;device=null;demo=false;ip=null;',
            'case "disconnect":manualBitSession=false;manualBitPendingId=-1;device=null;demo=false;ip=null;')
# In session start existing valid BIT still doesn't start a test; stale pending cleared only on re-enter verified BIT.
needle='        JSONObject report=ok().put("procedure","enter BIT once, verify 99-5, keep session active");'
assert needle in s
s=s.replace(needle,needle+'\n        manualBitPendingId=-1;manualBitPendingName="";')
needle='        JSONObject report=ok();\n        try{\n            JSONObject catalogNow=liveBitCatalog();'
assert needle in s
s=s.replace(needle,'        JSONObject report=ok().put("pending_test_id",manualBitPendingId).put("pending_test_name",manualBitPendingName);\n        try{\n            JSONObject catalogNow=liveBitCatalog();')
needle='        if(!manualBitSession)throw new IllegalStateException("Sessão BIT não confirmada. Entre no BIT ou use Verificar estado.");'
assert needle in s
s=s.replace(needle,needle+'''
        if(manualBitPendingId>=0)
            throw new IllegalStateException("Confirme o resultado do teste anterior antes de iniciar outro.");''')
needle='        if(!b.optBoolean("safe_location",false)||\n            !("TESTAR "+id).equals(b.optString("confirmation")))\n            throw new IllegalArgumentException("Confirme posição segura e digite TESTAR "+id+".");'
assert needle in s
s=s.replace(needle,
'''        if(!b.optBoolean("safe_location",false)||!b.optBoolean("confirmed",false))
            throw new IllegalArgumentException("Confirme a posição segura e a execução do teste.");''')
needle='        report.put("test_command_accepted",accepted);\n        if(accepted)SystemClock.sleep(wait*1000L);'
assert needle in s
s=s.replace(needle,
'''        report.put("test_command_accepted",accepted);
        if(accepted){
            manualBitPendingId=id;
            manualBitPendingName=name;
        }
        report.put("awaiting_user_result",accepted)
              .put("note","Comando enviado imediatamente. Espere a fala de PASS/FAIL e confirme no aplicativo; não há espera fixa.");''')
anchor='    /** Explicitly leave BIT. Distinguish transport ack from proof by catalog. */'
assert anchor in s
method=r'''
    /** Manual acknowledgment from the operator, not an automatic diagnosis from firmware. */
    private JSONObject bitSessionFinish(JSONObject b)throws Exception{
        String result=b.optString("result","");
        if(!("passed".equals(result)||"failed".equals(result)||"unknown".equals(result)))
            throw new IllegalArgumentException("Resultado inválido.");
        if(manualBitPendingId<0)
            throw new IllegalStateException("Nenhum teste iniciado está aguardando confirmação.");
        JSONObject report=ok()
            .put("test_id",manualBitPendingId)
            .put("test_name",manualBitPendingName)
            .put("manual_result",result)
            .put("manual_result_only",true)
            .put("bit_remains_active",manualBitSession)
            .put("note","Resultado registrado pelo usuário após ouvir/observar o robô. Não é validação automática do firmware.");
        manualBitPendingId=-1;manualBitPendingName="";
        return report;
    }

'''
s=s.replace(anchor,method+anchor)
needle='        manualBitSession=false;\n        report.put("exit_verified_by_empty_catalog",verified).put("exit_checks",events)'
assert needle in s
s=s.replace(needle,
'''        manualBitSession=false;
        manualBitPendingId=-1;manualBitPendingName="";
        report.put("exit_verified_by_empty_catalog",verified).put("exit_checks",events)''')
bridge.write_text(s)
grad=Path('app/build.gradle'); gs=grad.read_text()
assert "versionCode 10; versionName '1.0.0'" in gs
grad.write_text(gs.replace("versionCode 10; versionName '1.0.0'","versionCode 11; versionName '1.1.0'"))
h=Path("app/src/main/assets/index.html")
html=h.read_text()
import re
# Remove all manual phrase entry controls from session UI.
html,count=re.subn(
    r'<div><label for="bitStartConfirm">.*?</div>',
    '',html,count=1,flags=re.S)
assert count==1
html,count=re.subn(
    r'<div><label for="bitChoiceConfirmation">.*?</div>',
    '',html,count=1,flags=re.S)
assert count==1
html,count=re.subn(
    r'<label class="checkline" id="allTestsExtraRow".*?</label>',
    '',html,count=1,flags=re.S)
assert count==1
# Remove redundant execute button, test tiles themselves will open a native confirmation dialog.
html,count=re.subn(
    r'<button id="runSelectedBit".*?</button>',
    '',html,count=1,flags=re.S)
assert count==1
# Insert visible post-test manual action buttons.
needle='<pre id="bitSelectedResult" class="output">Nenhum teste executado.</pre>'
assert needle in html
html=html.replace(needle,needle+'''
<div id="bitOutcomePanel" class="card stack" style="display:none;margin-top:12px">
<h3>O teste terminou?</h3>
<p id="bitOutcomeMessage">Quando o robô anunciar o resultado, toque no botão correspondente para liberar o próximo teste.</p>
<div class="row" style="gap:10px;flex-wrap:wrap">
  <button id="bitOutcomePass" class="btn primary" type="button">✓ Passou — liberar</button>
  <button id="bitOutcomeFail" class="btn danger" type="button">✗ Falhou — liberar</button>
  <button id="bitOutcomeUnknown" class="btn" type="button">Não concluiu / não ouvi</button>
</div>
<p class="note">Só confirme após o robô encerrar o teste e parar seus componentes. A confirmação é manual, não altera o resultado do firmware nem sai do BIT.</p>
</div>''')
# No need for old data form references in setupBitTestCatalog.
start=html.index('function setupBitTestCatalog(){')
end=html.index('\n}\n',start)+len('\n}\n')
replacement=r'''
function setupBitTestCatalog(){
 document.querySelectorAll('.bit-test-choice').forEach(btn=>{
  btn.onclick=()=>{
   if(busy||bitTestPending){toast('Aguarde e confirme o resultado do teste anterior.',true);return;}
   const spec=bitTestSpecs.find(t=>t.key===btn.dataset.bitKey);
   if(!spec)return;
   bitSelected=spec;
   $('bitSelectedHelp').textContent=spec.pt+' (ID '+spec.id+'): '+spec.info;
   runSelectedBit();
  };
 });
}
'''
html=html[:start]+replacement+html[end:]
# Wrap all normal BIT commands against a test awaiting completion.
needle="let bitSessionUiActive=false;"
assert needle in html
html=html.replace(needle,"let bitTestPending=false;\nlet bitPendingSpec=null;\n"+needle)
# Simplify entry: checkbox and confirm prompt are enough, no phrase typing.
needle="if(!$('bitSafety').checked||$('bitStartConfirm').value.trim()!=='ENTRAR BIT'){"
assert needle in html
html=html.replace(needle,"if(!$('bitSafety').checked){")
html=html.replace("toast('Confirme o local seguro e digite ENTRAR BIT.',true);",
                  "toast('Confirme que o robô está em local seguro.',true);")
# If there is still a running test, don't leave without explicit note.
needle="if(!window.confirm('Enviar NORMAL e encerrar a sessão BIT? Certifique-se de que nenhum teste ainda está girando.'))return;"
assert needle in html
html=html.replace(needle,
"""if(bitTestPending){toast('Aguarde o teste acabar e confirme seu resultado antes de sair.',true);return;}
 if(!window.confirm('Enviar NORMAL e encerrar a sessão BIT? Certifique-se de que nenhum teste ainda está girando.'))return;""")
# Replace runSelectedBit completely with confirmation-only flow (native ACK ends quickly, no timer).
start=html.index('async function runSelectedBit(){')
end=html.index('async function refreshLogs(){',start)
ui=r'''
function setBitAwaitingOutcome(active,spec){
 bitTestPending=active;
 bitPendingSpec=active?spec:null;
 $('bitOutcomePanel').style.display=active?'block':'none';
 if(active)$('bitOutcomeMessage').textContent='Teste: '+spec.pt+'. Aguarde a fala de PASS/FAIL do robô. Assim que terminar, selecione o resultado para liberar os próximos testes.';
 // Maintain visual and logical one-test-at-a-time gating.
 document.querySelectorAll('.bit-test-choice').forEach(btn=>btn.disabled=active||busy||!con);
}
async function finishBitTest(result){
 if(!bitTestPending||busy)return;
 if(result==='unknown'&&!window.confirm('O robô encerrou o teste e seus componentes pararam? Se estiver girando, não confirme.'))return;
 setBusy(true);
 try {
  const r=await api('bit-session-finish',{result});
  $('bitSelectedResult').textContent=jsonText(r);
  setBitAwaitingOutcome(false,null);
  toast(result==='passed'?'Resultado anotado: PASSOU. Pode escolher outro teste.':
       result==='failed'?'Resultado anotado: FALHOU. Pode escolher outro teste.':
       'Resultado inconclusivo anotado. Pode escolher outro teste.',result!=='passed');
 }catch(e){$('bitSelectedResult').textContent=e.message;toast('Não foi possível liberar: '+e.message,true);}
 finally{setBusy(false);document.querySelectorAll('.bit-test-choice').forEach(btn=>btn.disabled=bitTestPending||busy||!con);}
}
async function runSelectedBit(){
 if(!con||busy||!bitSelected)return;
 if(bitTestPending){toast('Finalize o teste anterior usando Passou ou Falhou.',true);return;}
 if(!bitSessionUiActive){toast('Entre no BIT e confirme a lista antes de executar.',true);return;}
 const spec=bitSelected;
 if(spec.id===1){toast('Selecione testes individuais.',true);return;}
 if(!$('bitSafety').checked){toast('Confirme o ambiente seguro.',true);return;}
 if(!window.confirm('Executar '+spec.pt+' (ID '+spec.id+')?\\n\\n'+spec.info+'\\n\\nO modo BIT continuará ativo.'))return;
 setBusy(true);
 $('bitSelectedResult').textContent='Enviando comando para '+spec.pt+'...';
 try{
  const r=await api('bit-session-test',{
    test_name:spec.key,
    safe_location:true,
    confirmed:true
  });
  $('bitSelectedResult').textContent=jsonText(r);
  if(r.test_command_accepted){
    setBitAwaitingOutcome(true,spec);
    toast('Comando aceito. Após a fala do S40, marque Passou ou Falhou para liberar.');
  }else{
    if((r.test_error||'').includes('vazia'))showSessionState(false);
    toast('Teste não iniciado. Confira o resultado.',true);
  }
 }catch(e){
  $('bitSelectedResult').textContent=e.message;
  showSessionState(null);
  toast('Falha ao iniciar: '+e.message,true);
 }
 finally{
  setBusy(false);
  document.querySelectorAll('.bit-test-choice').forEach(btn=>btn.disabled=bitTestPending||busy||!con);
 }
}
'''
html=html[:start]+ui+html[end:]
# Wire all post-test action buttons; JS uses explicit click events.
anchor="$('bitExit').onclick=exitManualBit;setupBitTestCatalog();$('runSelectedBit').onclick=runSelectedBit;"
assert anchor in html
html=html.replace(anchor,
"""$('bitExit').onclick=exitManualBit;setupBitTestCatalog();$('bitOutcomePass').onclick=()=>finishBitTest('passed');$('bitOutcomeFail').onclick=()=>finishBitTest('failed');$('bitOutcomeUnknown').onclick=()=>finishBitTest('unknown');""")
# Update all disabled elements list; old runSelectedBit no longer exists.
html=html.replace("'bitSessionStart','bitSessionStatus','bitExit','runSelectedBit'",
                  "'bitSessionStart','bitSessionStatus','bitExit','bitOutcomePass','bitOutcomeFail','bitOutcomeUnknown'")
# Eliminate old hidden input refs and rename UI to match current feature.
html=html.replace('Para entrar digite ENTRAR BIT','Entrar no BIT com confirmação')
html=html.replace('S40 Lab v1.0 · BIT fluido','S40 Lab v1.1 · BIT sem espera')
h.write_text(html)
print("v1.1 patch: immediate test ACK, pass/fail buttons, test tile confirm, no typed phrases")
