from bugintel.agents.android_agent import analyze_android_manifest


def sample_manifest():
    return """<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="com.demo.app">
    <uses-permission android:name="android.permission.INTERNET"/>
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE"/>

    <application android:label="Demo">
        <activity android:name=".MainActivity" android:exported="true">
            <intent-filter>
                <data android:scheme="demo" android:host="open" android:pathPrefix="/profile"/>
            </intent-filter>
        </activity>

        <activity android:name=".InternalActivity" android:exported="false"/>

        <receiver android:name=".BootReceiver" android:exported="true"/>

        <service android:name=".SyncService"/>
    </application>
</manifest>"""


def test_analyze_android_manifest_extracts_package_and_permissions():
    result = analyze_android_manifest(sample_manifest())

    assert result.package_name == "com.demo.app"
    assert "android.permission.INTERNET" in result.permissions
    assert "android.permission.ACCESS_NETWORK_STATE" in result.permissions


def test_analyze_android_manifest_extracts_components_and_exported():
    result = analyze_android_manifest(sample_manifest())

    names = [component.name for component in result.components]
    exported_names = [component.name for component in result.exported_components]

    assert ".MainActivity" in names
    assert ".InternalActivity" in names
    assert ".BootReceiver" in names
    assert ".SyncService" in names

    assert ".MainActivity" in exported_names
    assert ".BootReceiver" in exported_names
    assert ".InternalActivity" not in exported_names


def test_analyze_android_manifest_extracts_deep_links():
    result = analyze_android_manifest(sample_manifest())

    assert len(result.deep_links) == 1

    link = result.deep_links[0]

    assert link.component == ".MainActivity"
    assert link.scheme == "demo"
    assert link.host == "open"
    assert link.path == "/profile"


def test_analyze_android_manifest_mines_endpoints_from_extra_text():
    extra_text = """
    const API_BASE = "https://api.demo.example.com";
    fetch("/api/users/me");
    fetch("/api/projects/123");
    """

    result = analyze_android_manifest(sample_manifest(), extra_text=extra_text)

    assert "/api/users/me" in result.endpoints
    assert "/api/projects/123" in result.endpoints
