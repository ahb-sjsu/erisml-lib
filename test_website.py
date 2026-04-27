"""Selenium test for Geometric Ethics website interactivity."""

import os
import sys
import time

from selenium import webdriver
from selenium.webdriver.common.by import By


def test_website():
    html_path = os.path.abspath("docs/index.html")
    url = f"file:///{html_path.replace(os.sep, '/')}"

    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--window-size=1400,900")
    options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(options=options)
    driver.get(url)
    time.sleep(2)

    results = []

    def check(name, condition, detail=""):
        status = "PASS" if condition else "FAIL"
        results.append((status, name, detail))
        print(f"  [{status}] {name}" + (f" - {detail}" if detail else ""))

    def click(el):
        driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'}); arguments[0].click();", el
        )
        time.sleep(0.4)

    def css(el, prop):
        return driver.execute_script(
            f"return getComputedStyle(arguments[0]).{prop}", el
        )

    print("\n=== Geometric Ethics Website Interactive Test ===\n")

    # 1. Basic
    print("--- Basic ---")
    check("Page title", "Geometric Ethics" in driver.title)
    check("Nav exists", len(driver.find_elements(By.CSS_SELECTOR, "#main-nav")) > 0)
    check(
        "Hero particles", len(driver.find_elements(By.CSS_SELECTOR, "#hero canvas")) > 0
    )

    # 2. Parable timeline
    print("\n--- Parable Timeline ---")
    events = driver.find_elements(By.CSS_SELECTOR, ".timeline-event")
    check("4 timeline events", len(events) == 4)
    check(
        "One is active",
        len(driver.find_elements(By.CSS_SELECTOR, ".timeline-event.active")) == 1,
    )

    # 3. Object cards
    print("\n--- Object Cards ---")
    cards = driver.find_elements(By.CSS_SELECTOR, ".object-card")
    check("8 object cards", len(cards) == 8)
    click(cards[0])
    check(
        "Expands on click",
        len(driver.find_elements(By.CSS_SELECTOR, ".object-card.expanded")) > 0,
    )
    formal = cards[0].find_elements(By.CSS_SELECTOR, ".object-formal")
    if formal:
        check("Formal def visible", css(formal[0], "opacity") == "1")

    # 4. Dimension wheel
    print("\n--- Dimension Wheel ---")
    check(
        "9 dimension dots",
        len(driver.find_elements(By.CSS_SELECTOR, "#dim-lines circle")) == 9,
    )
    check(
        "9 labels", len(driver.find_elements(By.CSS_SELECTOR, "#dim-labels text")) == 9
    )
    dim_cards = driver.find_elements(By.CSS_SELECTOR, ".dim-card")
    click(dim_cards[2])
    check(
        "Dim card activates",
        len(driver.find_elements(By.CSS_SELECTOR, ".dim-card.active")) == 1,
    )

    # 5. Tensor hierarchy
    print("\n--- Tensor Hierarchy ---")
    btns = driver.find_elements(By.CSS_SELECTOR, ".level-btn")
    check("6+ level buttons", len(btns) >= 6)
    click(btns[2])
    check(
        "Button activates",
        len(driver.find_elements(By.CSS_SELECTOR, ".level-btn.active")) == 1,
    )
    lv2 = driver.find_elements(By.CSS_SELECTOR, "#h-level-2")
    if lv2:
        check("Level 2 shown", css(lv2[0], "display") != "none")

    # 6. Parts accordion
    print("\n--- Parts Accordion ---")
    headers = driver.find_elements(By.CSS_SELECTOR, ".part-header")
    check("7 parts", len(headers) == 7)
    click(headers[0])
    check(
        "Part opens", len(driver.find_elements(By.CSS_SELECTOR, ".part-item.open")) == 1
    )

    # 7. Theorem cards
    print("\n--- Theorem Cards ---")
    thms = driver.find_elements(By.CSS_SELECTOR, ".theorem-card")
    check("7 theorem cards", len(thms) == 7)
    click(thms[0])
    check(
        "Expands on click",
        len(driver.find_elements(By.CSS_SELECTOR, ".theorem-card.expanded")) > 0,
    )
    detail = thms[0].find_elements(By.CSS_SELECTOR, ".theorem-detail")
    if detail:
        check("Detail visible", css(detail[0], "opacity") == "1")
        check(
            "Detail has content",
            len(detail[0].text) > 20,
            f"{len(detail[0].text)} chars",
        )
    check(
        "Hint exists", len(thms[0].find_elements(By.CSS_SELECTOR, ".theorem-hint")) > 0
    )

    # 8. Application hex cards *** FOCUS ***
    print("\n--- App Hex Cards (VII) ***FOCUS*** ---")
    hexes = driver.find_elements(By.CSS_SELECTOR, ".app-hex")
    check("9 hex cards", len(hexes) == 9)

    for h in hexes:
        name = h.get_attribute("data-app")
        check(f"  '{name}' pointer cursor", css(h, "cursor") == "pointer")

    click(hexes[0])
    check(
        "Hex activates",
        len(driver.find_elements(By.CSS_SELECTOR, ".app-hex.active")) > 0,
    )
    panels = driver.find_elements(By.CSS_SELECTOR, ".app-detail-panel")
    check("Detail panel created", len(panels) > 0)
    if panels:
        check("Panel visible", css(panels[0], "opacity") == "1")
        check("Panel has content", len(panels[0].get_attribute("innerHTML")) > 50)

    click(hexes[3])
    active = driver.find_elements(By.CSS_SELECTOR, ".app-hex.active")
    check(
        "Switch to finance",
        len(active) == 1 and active[0].get_attribute("data-app") == "finance",
    )

    click(hexes[3])
    check(
        "Deactivate", len(driver.find_elements(By.CSS_SELECTOR, ".app-hex.active")) == 0
    )

    # 9. Equation
    print("\n--- Equation ---")
    terms = driver.find_elements(By.CSS_SELECTOR, ".eq-term")
    check("3 equation terms", len(terms) == 3)
    check("Terms clickable", css(terms[0], "cursor") == "pointer")

    # 10. Conservation
    print("\n--- Conservation ---")
    cons = driver.find_elements(By.CSS_SELECTOR, ".consequence")
    check("4 consequences", len(cons) == 4)
    check("Clickable cursor", css(cons[0], "cursor") == "pointer")
    click(cons[0])
    check(
        "Activates",
        len(driver.find_elements(By.CSS_SELECTOR, ".consequence.active")) == 1,
    )

    # 11. Reading paths
    print("\n--- Reading Paths ---")
    paths = driver.find_elements(By.CSS_SELECTOR, ".path-card")
    check(f"{len(paths)} path cards", len(paths) >= 4)
    check("Clickable", css(paths[0], "cursor") == "pointer")

    # 12. DEME architecture
    print("\n--- DEME Architecture ---")
    check(
        "Tooltip created",
        len(driver.find_elements(By.CSS_SELECTOR, ".deme-tooltip")) > 0,
    )
    rects = driver.find_elements(By.CSS_SELECTOR, ".deme-svg rect")
    check(f"{len(rects)} SVG rects", len(rects) >= 7)

    # 13. Epistemic cards
    print("\n--- Epistemic Cards ---")
    eps = driver.find_elements(By.CSS_SELECTOR, ".epistemic-card")
    check("4 epistemic cards", len(eps) == 4)
    click(eps[0])
    time.sleep(0.5)
    check(
        "Expands",
        len(driver.find_elements(By.CSS_SELECTOR, ".epistemic-card.expanded")) > 0,
    )
    ep_d = eps[0].find_elements(By.CSS_SELECTOR, ".epistemic-detail")
    if ep_d:
        check("Detail visible", css(ep_d[0], "opacity") == "1")

    # 14. Dear Ethicist game
    print("\n--- Dear Ethicist Game ---")
    btns = driver.find_elements(By.CSS_SELECTOR, ".game-choices .choice-btn")
    check("8 choice buttons", len(btns) == 8)
    click(btns[0])  # O for neighbor
    check(
        "Button activates",
        len(driver.find_elements(By.CSS_SELECTOR, ".choice-btn.active-choice")) >= 1,
    )
    click(btns[5])  # C for writer
    result = driver.find_elements(By.CSS_SELECTOR, ".game-result")
    if result:
        check("Result appears", css(result[0], "display") != "none")
        rt = result[0].text.encode("ascii", "replace").decode()
        check("Result has text", len(result[0].text) > 10, rt[:60])

    # 15. Bell test slider
    print("\n--- Bell Test ---")
    slider = driver.find_elements(By.CSS_SELECTOR, ".bell-slider")
    check("Slider exists", len(slider) > 0)
    display = driver.find_elements(By.CSS_SELECTOR, ".bell-s-display")
    check("S-display exists", len(display) > 0)
    if display:
        check("Shows S value", "S =" in display[0].text, display[0].text)
    verdict = driver.find_elements(By.CSS_SELECTOR, ".bell-verdict")
    check("Verdict exists", len(verdict) > 0 and len(verdict[0].text) > 5)

    # 16. Concept exploration
    print("\n--- Concept Exploration ---")
    # Open a part accordion first to see chapter items
    headers = driver.find_elements(By.CSS_SELECTOR, ".part-header")
    click(headers[0])
    time.sleep(0.3)
    tags = driver.find_elements(By.CSS_SELECTOR, ".concept-tag")
    check(f"{len(tags)} concept tags", len(tags) > 0)
    click(tags[0])
    time.sleep(0.5)
    modal_overlay = driver.find_elements(
        By.CSS_SELECTOR, ".concept-modal-overlay.visible"
    )
    check("Modal opens", len(modal_overlay) > 0)
    if modal_overlay:
        title = driver.find_elements(By.CSS_SELECTOR, ".concept-modal-title")
        check(
            "Modal has title",
            len(title) > 0 and len(title[0].text) > 0,
            title[0].text if title else "",
        )
        formal = driver.find_elements(By.CSS_SELECTOR, ".concept-formal")
        check("Modal has formal def", len(formal) > 0 and len(formal[0].text) > 20)
        desc = driver.find_elements(By.CSS_SELECTOR, ".concept-modal-desc")
        check("Modal has description", len(desc) > 0 and len(desc[0].text) > 20)
        related = driver.find_elements(By.CSS_SELECTOR, ".concept-related .concept-tag")
        check("Has related concepts", len(related) > 0)
        # Close modal
        close_btn = driver.find_elements(By.CSS_SELECTOR, ".concept-modal-close")
        if close_btn:
            click(close_btn[0])
            time.sleep(0.3)
            check(
                "Modal closes",
                len(
                    driver.find_elements(
                        By.CSS_SELECTOR, ".concept-modal-overlay.visible"
                    )
                )
                == 0,
            )

    # 17. Visual demos
    print("\n--- Visual Demos ---")
    tensor_demo = driver.find_elements(By.CSS_SELECTOR, ".scalar-tensor-demo")
    check("Scalar vs Tensor demo", len(tensor_demo) > 0)
    sliders = driver.find_elements(By.CSS_SELECTOR, ".demo-slider")
    check("3 demo sliders", len(sliders) == 3)
    geodesic = driver.find_elements(By.CSS_SELECTOR, ".geodesic-demo")
    check("Geodesic pathfinder", len(geodesic) > 0)
    contraction = driver.find_elements(By.CSS_SELECTOR, ".contraction-btn")
    check("Contraction button", len(contraction) > 0)

    # Summary
    print("\n" + "=" * 60)
    passed = sum(1 for r in results if r[0] == "PASS")
    failed = sum(1 for r in results if r[0] == "FAIL")
    print(f"Results: {passed} PASS, {failed} FAIL out of {len(results)} tests")
    if failed:
        print("\nFailed tests:")
        for s, n, d in results:
            if s == "FAIL":
                print(f"  FAIL: {n}" + (f" - {d}" if d else ""))
    print("=" * 60)

    driver.quit()
    return failed == 0


if __name__ == "__main__":
    success = test_website()
    sys.exit(0 if success else 1)
