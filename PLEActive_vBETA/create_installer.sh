#!/bin/bash
# EPA Dashboard - Professional macOS .pkg Installer Builder
# Creates a .pkg installer that automatically installs to /Applications

set -e

APP_NAME="EPA_Dashboard"
APP_DISPLAY_NAME="EPA Dashboard"
APP_VERSION="1.0.1"
BUNDLE_ID="com.epai.dashboard"
DIST_DIR="$(cd "$(dirname "$0")" && pwd)/dist"
APP_BUNDLE="${DIST_DIR}/${APP_NAME}.app"
PKG_OUTPUT="${DIST_DIR}/${APP_NAME}_Installer_v${APP_VERSION}.pkg"
COMPONENT_PKG="${DIST_DIR}/${APP_NAME}_component.pkg"
SCRIPTS_DIR="${DIST_DIR}/installer_scripts"
RESOURCES_DIR="${DIST_DIR}/installer_resources"

echo ""
echo "=== EPA Dashboard - macOS .pkg Installer Builder ==="
echo ""

# Step 1: Verify the .app bundle exists
if [ ! -d "${APP_BUNDLE}" ]; then
    echo "ERROR: .app bundle not found at: ${APP_BUNDLE}"
    echo "Build the app first with PyInstaller, then run this script."
    exit 1
fi

echo "[1/5] Found .app bundle: ${APP_BUNDLE}"

# Step 2: Create installer scripts
echo "[2/5] Creating installer scripts..."

rm -rf "${SCRIPTS_DIR}"
mkdir -p "${SCRIPTS_DIR}"

cat > "${SCRIPTS_DIR}/preinstall" << 'EOF'
#!/bin/bash
pkill -9 -f "EPA_Dashboard" 2>/dev/null || true
if [ -d "/Applications/EPA_Dashboard.app" ]; then
    rm -rf "/Applications/EPA_Dashboard.app"
fi
exit 0
EOF
chmod +x "${SCRIPTS_DIR}/preinstall"

cat > "${SCRIPTS_DIR}/postinstall" << 'EOF'
#!/bin/bash
xattr -rd com.apple.quarantine /Applications/EPA_Dashboard.app 2>/dev/null || true
chmod -R 755 /Applications/EPA_Dashboard.app
/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -f /Applications/EPA_Dashboard.app 2>/dev/null || true
exit 0
EOF
chmod +x "${SCRIPTS_DIR}/postinstall"

echo "  -> preinstall and postinstall scripts created"

# Step 3: Create installer resources
echo "[3/5] Creating installer resources..."

rm -rf "${RESOURCES_DIR}"
mkdir -p "${RESOURCES_DIR}"

cat > "${RESOURCES_DIR}/welcome.html" << 'EOF'
<!DOCTYPE html>
<html>
<head>
<style>
body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; padding: 20px; color: #333; }
h1 { color: #1a73e8; font-size: 22px; }
h2 { color: #555; font-size: 16px; font-weight: normal; }
p { font-size: 14px; line-height: 1.6; }
.version { color: #888; font-size: 12px; }
ul { padding-left: 20px; }
li { margin-bottom: 8px; font-size: 14px; }
</style>
</head>
<body>
<h1>EPA Dashboard</h1>
<h2>Personal Learning Environment</h2>
<p>This installer will install <strong>EPA Dashboard</strong> into your Applications folder.</p>
<p><strong>Features included:</strong></p>
<ul>
<li>Personal Learning Environment (PLE) Management</li>
<li>Chrome History Integration</li>
<li>Intelligent Keyword Extraction (NLP)</li>
<li>Course Recommendations</li>
<li>Multi-profile Support</li>
</ul>
<p>Click <strong>Continue</strong> to proceed with the installation.</p>
<p class="version">Version 1.0.1</p>
</body>
</html>
EOF

cat > "${RESOURCES_DIR}/conclusion.html" << 'EOF'
<!DOCTYPE html>
<html>
<head>
<style>
body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; padding: 20px; color: #333; }
h1 { color: #34a853; font-size: 22px; }
p { font-size: 14px; line-height: 1.6; }
.note { background: #f0f7ff; border-left: 4px solid #1a73e8; padding: 12px 16px; margin: 16px 0; border-radius: 4px; }
</style>
</head>
<body>
<h1>Installation Complete!</h1>
<p>EPA Dashboard has been installed successfully.</p>
<p>You can find it in your <strong>Applications</strong> folder or search for it in <strong>Spotlight</strong> (Cmd + Space).</p>
<div class="note">
<strong>First Launch:</strong> If macOS shows a security warning, go to <strong>System Settings &gt; Privacy &amp; Security</strong> and click <strong>Open Anyway</strong>.
</div>
<p>You can now close this installer.</p>
</body>
</html>
EOF

echo "  -> welcome and conclusion pages created"

# Step 4: Build the component .pkg
echo "[4/5] Building installer package..."

PAYLOAD_DIR="${DIST_DIR}/pkg_payload"
rm -rf "${PAYLOAD_DIR}"
mkdir -p "${PAYLOAD_DIR}"

# Copy app and strip extended attributes to avoid resource fork issues
cp -R "${APP_BUNDLE}" "${PAYLOAD_DIR}/EPA_Dashboard.app"
xattr -cr "${PAYLOAD_DIR}/EPA_Dashboard.app"
dot_clean "${PAYLOAD_DIR}/EPA_Dashboard.app"
find "${PAYLOAD_DIR}" -name '._*' -delete

# Create component plist to disable bundle relocation
COMPONENT_PLIST="${DIST_DIR}/component.plist"
pkgbuild --analyze --root "${PAYLOAD_DIR}" "${COMPONENT_PLIST}"
# Disable relocation for all bundles so macOS doesn't redirect the install
python3 -c "
import plistlib
with open('${COMPONENT_PLIST}', 'rb') as f:
    pl = plistlib.load(f)
for item in pl:
    item['BundleIsRelocatable'] = False
with open('${COMPONENT_PLIST}', 'wb') as f:
    plistlib.dump(pl, f)
"

pkgbuild \
    --root "${PAYLOAD_DIR}" \
    --component-plist "${COMPONENT_PLIST}" \
    --identifier "${BUNDLE_ID}" \
    --version "${APP_VERSION}" \
    --install-location "/Applications" \
    --scripts "${SCRIPTS_DIR}" \
    "${COMPONENT_PKG}"

rm -f "${COMPONENT_PLIST}"

echo "  -> component package built"

# Step 5: Create distribution XML and final product .pkg
echo "[5/5] Creating final distribution installer..."

DISTRIBUTION_XML="${DIST_DIR}/distribution.xml"

cat > "${DISTRIBUTION_XML}" << DISTXML
<?xml version="1.0" encoding="utf-8"?>
<installer-gui-script minSpecVersion="2">
    <title>${APP_DISPLAY_NAME}</title>
    <organization>${BUNDLE_ID}</organization>
    <domains enable_localSystem="true" enable_currentUserHome="false" enable_anywhere="false"/>
    <options customize="never" require-scripts="true" rootVolumeOnly="true" hostArchitectures="arm64,x86_64"/>
    <welcome file="welcome.html" mime-type="text/html"/>
    <conclusion file="conclusion.html" mime-type="text/html"/>
    <choices-outline>
        <line choice="default">
            <line choice="${BUNDLE_ID}.pkg"/>
        </line>
    </choices-outline>
    <choice id="default"/>
    <choice id="${BUNDLE_ID}.pkg" visible="false">
        <pkg-ref id="${BUNDLE_ID}"/>
    </choice>
    <pkg-ref id="${BUNDLE_ID}" version="${APP_VERSION}" onConclusion="none">${APP_NAME}_component.pkg</pkg-ref>
</installer-gui-script>
DISTXML

productbuild \
    --distribution "${DISTRIBUTION_XML}" \
    --resources "${RESOURCES_DIR}" \
    --package-path "${DIST_DIR}" \
    "${PKG_OUTPUT}"

echo ""
echo "  -> Final installer created!"

# Cleanup temp files
rm -rf "${PAYLOAD_DIR}" "${SCRIPTS_DIR}" "${RESOURCES_DIR}" "${COMPONENT_PKG}" "${DISTRIBUTION_XML}"

# Summary
PKG_SIZE=$(du -sh "${PKG_OUTPUT}" | awk '{print $1}')

echo ""
echo "=== Installer built successfully! ==="
echo ""
echo "  File: ${PKG_OUTPUT}"
echo "  Size: ${PKG_SIZE}"
echo ""
echo "  How to distribute:"
echo "  1. Share the .pkg file with users"
echo "  2. Users double-click -> installer wizard opens"
echo "  3. App installs directly to /Applications"
echo "  4. No DMG mounting, no drag-and-drop needed"
echo ""
