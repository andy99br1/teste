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
