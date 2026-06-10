# Limitations

Blackhole AI Workbench is an early research prototype.

## Current Limitations

- Current coverage includes web, API, browser artifacts, Android static/config analysis, and iOS static/config analysis.
- Real Playwright execution is opt-in and early. Browser planning, Playwright execution preview, execution request modeling, adapter context/stub preparation, safety-gated execution CLI, artifact loading, capture-result evidence import, and report rendering are supported.
- Android and iOS support is currently limited to static manifest, plist, configuration, permission, component, deep-link, domain, URL-scheme, and endpoint analysis.
- LLM-provider integration remains disabled scaffolding; the current research brain is deterministic and local.
- HAR import is implemented. First-class Burp Suite proxy-history, sitemap, Repeater, extension, and controlled replay integration remains incomplete.
- Response-diff results require manual validation.
- The tool does not prove vulnerabilities automatically.

## Future Work

- full browser and DevTools interaction loop
- first-class Burp Suite integration
- general local shell and Kali tool adapters
- approved package-install workflow
- observation-to-research-state feedback loop
- controlled proof-of-concept validation runtime
- concurrent multi-agent workers
- enabled LLM-provider integration
- specialized security-research LLM and evaluation harness
