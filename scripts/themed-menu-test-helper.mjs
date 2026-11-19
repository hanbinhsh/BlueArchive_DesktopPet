export async function openTestPanel(app,pet){
 const opening=app.waitForEvent('window');await pet.evaluate(()=>window.pet.menu());const menu=await opening;
 await menu.waitForSelector('[data-menu-item="open-panel"]');const panelOpening=app.waitForEvent('window');await menu.locator('[data-menu-item="open-panel"]').click();const panel=await panelOpening;await panel.waitForSelector('#roster .star');return panel;
}
