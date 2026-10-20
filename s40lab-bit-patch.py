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
                    JSONArray ack=device.setProperty(99,1,"BIT");
                    report.put("enter_ack_"+entry,safe(ack));
                    JSONObject first=ack.optJSONObject(0);
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
            JSONArray startAck=device.setProperty(99,2,5);
            report.put("test_start_ack",safe(startAck));
            JSONObject first=startAck.optJSONObject(0);
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
