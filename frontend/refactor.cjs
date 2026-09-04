const fs = require('fs');
const path = require('path');

const srcRoot = path.resolve(__dirname, 'src');

// Build alias map: old src-relative path (no ext) -> new @/ alias (no ext)  
const moveTable = [
  ["app/App.tsx",                                         "App.tsx"],
  ["app/main.tsx",                                        "main.tsx"],
  ["app/pages/Layout.tsx",                                "pages/Layout.tsx"],
  ["app/styles/theme.css",                                "theme.css"],
  ["app/styles/index.css",                                "index.css"],
  ["app/styles/layout-extras.css",                        "layout-extras.css"],
  ["shared/assets/hero.png",                              "assets/hero.png"],
  ["shared/assets/react.svg",                             "assets/react.svg"],
  ["shared/assets/vite.svg",                              "assets/vite.svg"],
  ["shared/components/Header.tsx",                        "components/Header.tsx"],
  ["shared/components/Sidebar.tsx",                       "components/Sidebar.tsx"],
  ["shared/components/KpiCard.tsx",                       "components/KpiCard.tsx"],
  ["shared/components/AnalyticsChart.tsx",                "components/AnalyticsChart.tsx"],
  ["shared/components/MiniTimeSeries.tsx",                "components/MiniTimeSeries.tsx"],
  ["modules/overview/pages/Overview.tsx",                 "pages/Overview.tsx"],
  ["modules/overview/pages/AnalyticsPage.tsx",            "pages/AnalyticsPage.tsx"],
  ["modules/overview/pages/LiveMonitor.tsx",              "pages/LiveMonitor.tsx"],
  ["modules/fleet/pages/DevicesPage.tsx",                 "pages/fleet/DevicesPage.tsx"],
  ["modules/fleet/pages/CamerasPage.tsx",                 "pages/fleet/CamerasPage.tsx"],
  ["modules/fleet/pages/SnapshotsPage.tsx",               "pages/fleet/SnapshotsPage.tsx"],
  ["modules/fleet/pages/CameraGroupsPage.tsx",            "pages/fleet/CameraGroupsPage.tsx"],
  ["modules/fleet/pages/Cameras.tsx",                     "pages/Cameras.tsx"],
  ["modules/fleet/pages/EdgeDevicesPage.tsx",             "pages/EdgeDevicesPage.tsx"],
  ["modules/fleet/components/EdgeDeviceCard.tsx",         "components/EdgeDeviceCard.tsx"],
  ["modules/fleet/components/CameraListPanel.tsx",        "components/CameraListPanel.tsx"],
  ["modules/fleet/components/LiveMonitorPanel.tsx",       "components/LiveMonitorPanel.tsx"],
  ["modules/fleet/mock/fleet.ts",                         "mock/fleet.ts"],
  ["modules/fleet/mock/cameras.ts",                       "mock/cameras.ts"],
  ["modules/ai/pages/InferencePage.tsx",                  "pages/ai/InferencePage.tsx"],
  ["modules/ai/pages/ModelsPage.tsx",                     "pages/ai/ModelsPage.tsx"],
  ["modules/ai/pages/DeploymentsPage.tsx",                "pages/ai/DeploymentsPage.tsx"],
  ["modules/ai/mock/ai.ts",                               "mock/ai.ts"],
  ["modules/observability/pages/IncidentsPage.tsx",       "pages/IncidentsPage.tsx"],
  ["modules/observability/pages/MonitoringPage.tsx",      "pages/observability/MonitoringPage.tsx"],
  ["modules/observability/pages/AlertsPage.tsx",          "pages/observability/AlertsPage.tsx"],
  ["modules/observability/pages/EventsPage.tsx",          "pages/observability/EventsPage.tsx"],
  ["modules/observability/pages/LogsPage.tsx",            "pages/observability/LogsPage.tsx"],
  ["modules/observability/components/IncidentsTable.tsx", "components/IncidentsTable.tsx"],
  ["modules/observability/components/IncidentModal.tsx",  "components/IncidentModal.tsx"],
  ["modules/observability/components/AlertsPanel.tsx",    "components/AlertsPanel.tsx"],
  ["modules/observability/hooks/useIncidents.ts",         "hooks/useIncidents.ts"],
  ["modules/observability/mock/incidents.ts",             "mock/incidents.ts"],
  ["modules/observability/mock/observability.ts",         "mock/observability.ts"],
  ["modules/assistant/pages/ChatPage.tsx",                "pages/ChatPage.tsx"],
  ["modules/assistant/pages/AiAssistantPage.tsx",         "pages/AiAssistantPage.tsx"],
  ["modules/assistant/components/AiAssistantChat.tsx",    "components/AiAssistantChat.tsx"],
  ["modules/assistant/components/ChatWidget.tsx",         "components/ChatWidget.tsx"],
  ["modules/assistant/components/ChatInputForm.tsx",      "components/ChatInputForm.tsx"],
  ["modules/system/pages/SettingsPage.tsx",               "pages/system/SettingsPage.tsx"],
  ["modules/system/pages/AuditLogsPage.tsx",              "pages/system/AuditLogsPage.tsx"],
  ["modules/system/pages/UsersPage.tsx",                  "pages/system/UsersPage.tsx"],
  ["modules/system/pages/Settings.tsx",                   "pages/Settings.tsx"],
  ["modules/system/mock/system.ts",                       "mock/system.ts"],
];

// Map: old-src-relative (without extension) -> new alias (without extension)
const aliasMap = new Map();
for (const [newRel, oldRel] of moveTable) {
  const oldKey = oldRel.replace(/\.(tsx?|css|png|svg)$/, '');
  const newAlias = '@/' + newRel.replace(/\.(tsx?)$/, '');
  aliasMap.set(oldKey, newAlias);
  // Also keep full path for assets/css
  if (/\.(css|png|svg)$/.test(newRel)) {
    aliasMap.set(oldRel, '@/' + newRel);
  }
}

function getAllFiles(dir, list = []) {
  for (const f of fs.readdirSync(dir)) {
    const full = path.join(dir, f);
    if (fs.statSync(full).isDirectory()) getAllFiles(full, list);
    else list.push(full);
  }
  return list;
}

const allFiles = getAllFiles(srcRoot).filter(f => /\.(tsx?|css)$/.test(f));

// Build reverse: new abs -> old abs
const newToOld = {};
for (const [newRel, oldRel] of moveTable) {
  newToOld[path.join(srcRoot, newRel)] = path.join(srcRoot, oldRel);
}

let totalUpdated = 0;

for (const filePath of allFiles) {
  let content = fs.readFileSync(filePath, 'utf8');
  const original = content;
  
  // Determine the "old" directory of this file (before moving)
  const oldFilePath = newToOld[filePath] || filePath; // if not moved, same location
  const oldFileDir = path.dirname(oldFilePath);

  // Replace relative imports
  content = content.replace(/((?:from|import)\s+['"])(\.[^'"]+)/g, (match, prefix, importPath) => {
    // Resolve the import relative to the old file location
    const resolvedAbs = path.resolve(oldFileDir, importPath);
    // Make it relative to srcRoot
    const relToSrc = path.relative(srcRoot, resolvedAbs).replace(/\\/g, '/').replace(/\.(tsx?)$/, '');
    
    if (aliasMap.has(relToSrc)) {
      return prefix + aliasMap.get(relToSrc);
    }
    // Try with extension for css
    const relToSrcFull = path.relative(srcRoot, resolvedAbs).replace(/\\/g, '/');
    if (aliasMap.has(relToSrcFull)) {
      return prefix + aliasMap.get(relToSrcFull);
    }
    return match;
  });

  if (content !== original) {
    fs.writeFileSync(filePath, content, 'utf8');
    console.log('Updated:', path.relative(srcRoot, filePath));
    totalUpdated++;
  }
}

console.log('\nTotal files updated:', totalUpdated);
