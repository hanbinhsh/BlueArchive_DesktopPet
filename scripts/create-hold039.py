"""Keep synthetic drag testing separate from the user's physical desktop input."""
from pathlib import Path
S=Path('scripts');text=(S/'hold-test.mjs').read_text('utf8')
text=text.replace("const reportPath=process.env.BA_NATIVE?'test-results/hold-native.json':'test-results/hold.json';","const reportPath='test-results/hold039.json';")
text=text.replace("const profile=path.resolve('test-results/hold-profile')","const profile=path.resolve('test-results/hold039-profile')")
text=text.replace('JSON.stringify({character,size:360,','JSON.stringify({character,allowOffscreen:true,size:360,')
text=text.replace("const hasPickup=(await page.evaluate", "await app.evaluate(({BrowserWindow})=>{const w=BrowserWindow.getAllWindows()[0];w.setFocusable(false);w.setBounds({...w.getBounds(),x:-4000,y:180});});\n  const hasPickup=(await page.evaluate")
text=text.replace('test-results/hold-','test-results/hold039-')
(S/'hold039-test.mjs').write_text(text,'utf8')
