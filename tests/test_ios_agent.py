from bugintel.agents.ios_agent import analyze_ios_plist


def sample_plist():
    return """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "https://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleIdentifier</key>
  <string>com.demo.iosapp</string>

  <key>CFBundleDisplayName</key>
  <string>Demo iOS App</string>

  <key>CFBundleURLTypes</key>
  <array>
    <dict>
      <key>CFBundleURLName</key>
      <string>com.demo.iosapp</string>
      <key>CFBundleURLSchemes</key>
      <array>
        <string>demoapp</string>
        <string>demo-login</string>
      </array>
    </dict>
  </array>

  <key>com.apple.developer.associated-domains</key>
  <array>
    <string>applinks:demo.example.com</string>
    <string>webcredentials:login.demo.example.com</string>
  </array>

  <key>NSAppTransportSecurity</key>
  <dict>
    <key>NSAllowsArbitraryLoads</key>
    <false/>
  </dict>
</dict>
</plist>
"""


def test_analyze_ios_plist_extracts_bundle_and_name():
    result = analyze_ios_plist(sample_plist())

    assert result.bundle_id == "com.demo.iosapp"
    assert result.display_name == "Demo iOS App"


def test_analyze_ios_plist_extracts_url_schemes():
    result = analyze_ios_plist(sample_plist())

    assert len(result.url_schemes) == 1
    assert result.url_schemes[0].name == "com.demo.iosapp"
    assert "demoapp" in result.url_schemes[0].schemes
    assert "demo-login" in result.url_schemes[0].schemes


def test_analyze_ios_plist_extracts_associated_domains_and_ats():
    result = analyze_ios_plist(sample_plist())

    assert "applinks:demo.example.com" in result.associated_domains
    assert "webcredentials:login.demo.example.com" in result.associated_domains
    assert result.ats_allows_arbitrary_loads is False


def test_analyze_ios_plist_mines_endpoints_and_hosts_from_extra_text():
    extra_text = """
    API_BASE=https://api.demo.example.com
    fetch("/api/users/me")
    fetch("/api/projects/123")
    """

    result = analyze_ios_plist(sample_plist(), extra_text=extra_text)

    assert "/api/users/me" in result.endpoints
    assert "/api/projects/123" in result.endpoints
    assert "api.demo.example.com" in result.hosts
