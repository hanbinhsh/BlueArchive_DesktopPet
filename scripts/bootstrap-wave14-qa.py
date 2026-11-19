"""Derive batch-specific QA drivers without overwriting older release evidence."""
from pathlib import Path
R=Path(__file__).resolve().parents[1];S=R/'scripts'
p=(S/'find-fx-dependency-headers.py').read_text('utf8').replace("W/'cafe-fx/source.json'","W/'cafe-wave14/source.json'").replace('fx-dependency-acquisition-1105','wave14-fx-dependencies')
(S/'find-wave14-fx-dependencies.py').write_text(p,'utf8')
p=(S/'audit-persistent13.py').read_text('utf8').replace('wave13','wave14').replace("W/'expanded-ready'","W/'wave14-final'")
(S/'audit-persistent14.py').write_text(p,'utf8')
p=(S/'audit-static039.py').read_text('utf8').replace('039','040').replace("Path('characters')","Path('.assets/wave14-final')")
(S/'audit-static040.py').write_text(p,'utf8')
p=(S/'wave13-preview.mjs').read_text('utf8').replace('wave13','wave14').replace("path.resolve('.assets/expanded-ready')","path.resolve('.assets/wave14-final')").replace("eyeFollow:false}","eyeFollow:false,allowOffscreen:true}")
p=p.replace('const panel=await openTestPanel(app,page);',"const panel=await openTestPanel(app,page);await app.evaluate(({BrowserWindow})=>{const w=BrowserWindow.getAllWindows().find(w=>w.webContents.getURL().endsWith('/index.html'));w.setFocusable(false);w.setBounds({...w.getBounds(),x:-4000,y:180});});")
(S/'wave14-preview.mjs').write_text(p,'utf8')
p=(S/'faces039.mjs').read_text('utf8').replace('039','040')
start=p.index('const names=');end=p.index(';',start)
p=p[:start]+"const names=Object.keys(JSON.parse(readFileSync('scripts/roster-wave14.json','utf8')))"+p[end:]
p=p.replace('eyeFollow:false,','eyeFollow:false,allowOffscreen:true,')
p=p.replace('const panel=await openTestPanel(app,pet);',"const panel=await openTestPanel(app,pet);await app.evaluate(({BrowserWindow})=>{const w=BrowserWindow.getAllWindows().find(w=>w.webContents.getURL().endsWith('/index.html'));w.setFocusable(false);w.setBounds({...w.getBounds(),x:-4000,y:180});});")
(S/'faces040.mjs').write_text(p,'utf8')
p=(S/'hold039-test.mjs').read_text('utf8').replace('039','040')
(S/'hold040-test.mjs').write_text(p,'utf8')
p=(S/'prop-review-1104.mjs').read_text('utf8').replace('eyeFollow:false}', 'eyeFollow:false,allowOffscreen:true}')
p=p.replace('const panel=await openTestPanel(app,page);',"const panel=await openTestPanel(app,page);await app.evaluate(({BrowserWindow})=>{const w=BrowserWindow.getAllWindows().find(w=>w.webContents.getURL().endsWith('/index.html'));w.setFocusable(false);w.setBounds({...w.getBounds(),x:-4000,y:180});});")
(S/'wave14-furniture-preview.mjs').write_text(p,'utf8')
