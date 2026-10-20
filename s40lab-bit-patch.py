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
