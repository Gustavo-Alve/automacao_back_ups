from playwright.sync_api import sync_playwright
import time

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=False)
    context = browser.new_context(
        permissions=["clipboard-read", "clipboard-write"]
    )

    pagina = context.new_page()
    time.sleep(1)
    pagina.goto('http://192.168.1.1/')
    time.sleep(1)
    nome_f670L = pagina.locator('//*[@id="head"]/div[1]/font').text_content()
    time.sleep(1)
    print(nome_f670L)
    if 'F670L' in nome_f670L:
        pagina.locator("#Frm_Username").click()
        time.sleep(1)
        pagina.locator("#Frm_Username").fill('multipro')
        time.sleep(1)
        pagina.locator("#Frm_Password").click()
        time.sleep(1)
        pagina.locator("#Frm_Password").fill('multipro')
        time.sleep(1)
        pagina.get_by_role("button", name="Login").click()
        time.sleep(1)
        pagina.locator("iframe[name=\"mainFrame\"]").content_frame.get_by_text("Administration").click()
        time.sleep(1)
        pagina.locator("iframe[name=\"mainFrame\"]").content_frame.get_by_text("System Management").click()
        time.sleep(1)
        pagina.locator("iframe[name=\"mainFrame\"]").content_frame.get_by_role("cell", name="Default Configuration Management", exact=True).click()
        time.sleep(1)
        time.sleep(2)
        pagina.locator("iframe[name=\"mainFrame\"]").content_frame.get_by_role("button", name="Restore Configuration").click()
        time.sleep(1)
        pagina.locator("iframe[name=\"mainFrame\"]").content_frame.get_by_role("button", name="Confirm").click()
        time.sleep(1)

    time.sleep(1)
    browser.close()