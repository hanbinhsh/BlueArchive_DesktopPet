"""Create isolated final executable test drivers for this increment."""
from pathlib import Path
R=Path(__file__).resolve().parents[1];S=R/'scripts'
p=(S/'wave13-runtime.mjs').read_text('utf8').replace('wave13','wave14').replace('eyeFollow:false,','eyeFollow:false,allowOffscreen:true,')
p=p.replace('const panel=await openTestPanel(app,page);',"const panel=await openTestPanel(app,page);await app.evaluate(({BrowserWindow})=>{const w=BrowserWindow.getAllWindows().find(w=>w.webContents.getURL().endsWith('/index.html'));w.setFocusable(false);w.setBounds({...w.getBounds(),x:-4000,y:180});});")
(S/'wave14-runtime.mjs').write_text(p,'utf8')
p=(S/'verify-release039.py').read_text('utf8').replace('039','040').replace('0.2.18','0.2.19')
(S/'verify-release040.py').write_text(p,'utf8')
p=(S/'transitions039-test.mjs').read_text('utf8').replace('039','040').replace('character,size:360','character,allowOffscreen:true,size:360')
p=p.replace('await page.waitForFunction(()=>window.petDiagnostics?.frames>5);',"await page.waitForFunction(()=>window.petDiagnostics?.frames>5);await app.evaluate(({BrowserWindow})=>{const w=BrowserWindow.getAllWindows().find(w=>w.webContents.getURL().endsWith('/index.html'));w.setFocusable(false);w.setBounds({...w.getBounds(),x:-4000,y:180});});")
(S/'transitions040-test.mjs').write_text(p,'utf8')
