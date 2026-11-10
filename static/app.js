const $ = id => document.getElementById(id);
const code = $("code"), output = $("output"), build = $("build");
function target(){return document.querySelector('input[name="target"]:checked').value}
function setState(text, color){$("buildState").textContent=text;$("buildState").style.color=color||"#69b7ff"}
function saveFile(){
 const t=target(), ext=t==="esp"?".ino":t==="exe"?".cpp":".cpp";
 const name=t==="esp"?"CloudSketch"+ext:t==="exe"?"main.cpp":"main.cpp";
 const blob=new Blob([code.value],{type:"text/plain"});
 const a=document.createElement("a");a.href=URL.createObjectURL(blob);a.download=name;a.click();URL.revokeObjectURL(a.href);
}
$("save").onclick=saveFile;
$("newFile").onclick=()=>{code.value="";code.focus();output.textContent="Yeni dosya oluşturuldu.";};
document.querySelectorAll('input[name="target"]').forEach(r=>r.onchange=()=>{
 const t=target();
 $("platform").textContent=t==="esp"?"ESP32 / Arduino CLI":t==="exe"?"Windows x64 / MinGW-w64":"C++17 / GCC";
 $("outputType").textContent=t==="esp"?"Firmware .bin":t==="exe"?"Windows .exe":"Program çıktısı";
 $("filename").textContent=t==="esp"?"CloudSketch.ino":"main.cpp";
 $("editorLabel").textContent=$("filename").textContent;
});
async function compile(){
 const t=target(); build.disabled=true;build.textContent="Derleniyor…";setState("BUILDING","#e6b45b");output.textContent="Bulut derlemesi başlatılıyor…";
 try{
   let url, body={code:code.value};
   if(t==="cpp") url="/api/cpp/run";
   else if(t==="exe") url="/api/cpp/exe";
   else url="/api/esp32/bin";
   const res=await fetch(url,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});
   if(!res.ok){let msg=await res.text();try{msg=JSON.parse(msg).detail||msg}catch{};throw new Error(msg)}
   if(t==="cpp"){
     const data=await res.json();
     output.textContent=`Compiler: ${data.compiler}\nStatus: ${data.status}\n\n${data.compiler_message||""}\n${data.program_message||""}`;
     setState(data.status==="0"||data.status===0?"SUCCESS":"FINISHED",data.status==="0"||data.status===0?"#65d69a":"#e6b45b");
   }else{
     const blob=await res.blob(), a=document.createElement("a");
     a.href=URL.createObjectURL(blob);a.download=t==="esp"?"cloud_code_esp32.bin":"program.exe";a.click();URL.revokeObjectURL(a.href);
     output.textContent=`Derleme başarılı.\nDosya indirildi: ${a.download}\nBoyut: ${blob.size.toLocaleString()} byte`;
     setState("SUCCESS","#65d69a");
   }
 }catch(e){output.textContent="Derleme hatası:\n"+e.message;setState("ERROR","#ff7777")}
 finally{build.disabled=false;build.innerHTML="▶ &nbsp; Derle"}
}
build.onclick=compile;
fetch("/api/health").then(r=>r.json()).then(d=>{$("status").textContent="Sunucu çevrimiçi";document.querySelector(".status i").style.background="#65d69a"}).catch(()=>$("status").textContent="Yerel / sunucu bekleniyor");
