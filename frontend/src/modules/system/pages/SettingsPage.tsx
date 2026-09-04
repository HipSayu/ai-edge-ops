import { useState } from 'react'
import {
  Sliders,
  Bell,
  Cpu,
  Monitor,
  CheckCircle2,
  Save,
  Key} from 'lucide-react'
import { useOutletContext } from 'react-router-dom'
import type { Theme } from '@/pages\Layout'

type TabKey = 'general' | 'ai' | 'alerts' | 'edge'

export default function SettingsPage() {
  const context = useOutletContext<{ theme: Theme; toggleTheme: () => void }>()
  const [activeTab, setActiveTab] = useState<TabKey>('general')

  // General state
  const [refreshInterval, setRefreshInterval] = useState('5')
  const [streamQuality, setStreamQuality] = useState('1080p')

  // AI model tuning state
  const [confidenceThreshold, setConfidenceThreshold] = useState(65)
  const [iouThreshold, setIouThreshold] = useState(45)
  const [temporalPersistence, setTemporalPersistence] = useState(5)
  const [autoTriageEnabled, setAutoTriageEnabled] = useState(true)

  // Notification state
  const [soundAlerts, setSoundAlerts] = useState(true)
  const [emailAlerts, setEmailAlerts] = useState(true)
  const [webhookUrl, setWebhookUrl] = useState('https://hooks.slack.com/services/T00/B00/XXXX')
  const [savedFeedback, setSavedFeedback] = useState(false)

  function handleSave() {
    setSavedFeedback(true)
    setTimeout(() => setSavedFeedback(false), 2000)
  }

  return (
    <div className="av-settings-container">
      

      <div className="av-settings-tabs">
        <button
          className={`av-settings-tab${activeTab === 'general' ? ' active' : ''}`}
          onClick={() => setActiveTab('general')}
        >
          <Monitor size={15} />
          <span>General & Display</span>
        </button>
        <button
          className={`av-settings-tab${activeTab === 'ai' ? ' active' : ''}`}
          onClick={() => setActiveTab('ai')}
        >
          <Sliders size={15} />
          <span>AI Model Tuning</span>
        </button>
        <button
          className={`av-settings-tab${activeTab === 'alerts' ? ' active' : ''}`}
          onClick={() => setActiveTab('alerts')}
        >
          <Bell size={15} />
          <span>Alerts & Notifications</span>
        </button>
        <button
          className={`av-settings-tab${activeTab === 'edge' ? ' active' : ''}`}
          onClick={() => setActiveTab('edge')}
        >
          <Cpu size={15} />
          <span>Edge Hardware & API</span>
        </button>
      </div>

      {activeTab === 'general' && (
        <div className="av-settings-section">
          <div className="av-settings-card">
            <span className="av-settings-card-title">
              <Monitor size={16} color="var(--accent)" />
              <span>Display & Interface Preferences</span>
            </span>

            <div className="av-settings-row">
              <div className="av-settings-row-info">
                <span className="av-settings-label">Interface Color Theme</span>
                <span className="av-settings-desc">
                  Toggle between high-contrast Dark Command Center and Clean Light SOC mode.
                </span>
              </div>
              <button
                className="av-btn-secondary"
                onClick={context?.toggleTheme}
                type="button"
              >
                {context?.theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
              </button>
            </div>

            <div className="av-settings-row">
              <div className="av-settings-row-info">
                <span className="av-settings-label">Telemetry Polling Rate</span>
                <span className="av-settings-desc">
                  Frequency of polling edge inference FPS and incident queue.
                </span>
              </div>
              <select
                value={refreshInterval}
                onChange={(e) => setRefreshInterval(e.target.value)}
                style={{ borderRadius: 8, padding: '6px 12px', background: 'var(--panel-2)', color: 'var(--text)', border: '1px solid var(--border-strong)' }}
              >
                <option value="1">1 second (Ultra real-time)</option>
                <option value="5">5 seconds (Recommended)</option>
                <option value="15">15 seconds (Battery saver)</option>
              </select>
            </div>

            <div className="av-settings-row">
              <div className="av-settings-row-info">
                <span className="av-settings-label">Default Live Stream Quality</span>
                <span className="av-settings-desc">
                  Target resolution for multiview matrix and single camera focus.
                </span>
              </div>
              <select
                value={streamQuality}
                onChange={(e) => setStreamQuality(e.target.value)}
                style={{ borderRadius: 8, padding: '6px 12px', background: 'var(--panel-2)', color: 'var(--text)', border: '1px solid var(--border-strong)' }}
              >
                <option value="1080p">1080p Full HD (60 FPS)</option>
                <option value="720p">720p HD (Balanced)</option>
                <option value="480p">480p SD (Low Bandwidth)</option>
              </select>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'ai' && (
        <div className="av-settings-section">
          <div className="av-settings-card">
            <span className="av-settings-card-title">
              <Sliders size={16} color="var(--accent)" />
              <span>Computer Vision Inference Parameters</span>
            </span>

            <div className="av-settings-row">
              <div className="av-settings-row-info">
                <span className="av-settings-label">Confidence Threshold ({confidenceThreshold}%)</span>
                <span className="av-settings-desc">
                  Detections below this score are automatically suppressed.
                </span>
              </div>
              <input
                type="range"
                min="40"
                max="95"
                value={confidenceThreshold}
                onChange={(e) => setConfidenceThreshold(Number(e.target.value))}
                style={{ width: 180 }}
              />
            </div>

            <div className="av-settings-row">
              <div className="av-settings-row-info">
                <span className="av-settings-label">NMS IoU Threshold ({iouThreshold}%)</span>
                <span className="av-settings-desc">
                  Non-maximum suppression overlap threshold for duplicate bounding boxes.
                </span>
              </div>
              <input
                type="range"
                min="20"
                max="80"
                value={iouThreshold}
                onChange={(e) => setIouThreshold(Number(e.target.value))}
                style={{ width: 180 }}
              />
            </div>

            <div className="av-settings-row">
              <div className="av-settings-row-info">
                <span className="av-settings-label">Temporal Consistency ({temporalPersistence} Frames)</span>
                <span className="av-settings-desc">
                  Consecutive positive frames required before dispatching a critical alert.
                </span>
              </div>
              <input
                type="number"
                min="1"
                max="15"
                value={temporalPersistence}
                onChange={(e) => setTemporalPersistence(Number(e.target.value))}
                style={{
                  width: 80,
                  padding: '6px 10px',
                  borderRadius: 6,
                  border: '1px solid var(--border-strong)',
                  background: 'var(--panel-2)',
                  color: 'var(--text)'}}
              />
            </div>

            <div className="av-settings-row">
              <div className="av-settings-row-info">
                <span className="av-settings-label">Auto-Triage Low Severity Events</span>
                <span className="av-settings-desc">
                  Mark informational events as reviewed if confidence is below 75%.
                </span>
              </div>
              <label className="av-toggle-switch">
                <input
                  type="checkbox"
                  checked={autoTriageEnabled}
                  onChange={(e) => setAutoTriageEnabled(e.target.checked)}
                />
                <span className="av-toggle-slider" />
              </label>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'alerts' && (
        <div className="av-settings-section">
          <div className="av-settings-card">
            <span className="av-settings-card-title">
              <Bell size={16} color="var(--accent)" />
              <span>Incident Notification Channels</span>
            </span>

            <div className="av-settings-row">
              <div className="av-settings-row-info">
                <span className="av-settings-label">Critical Audible Alarm</span>
                <span className="av-settings-desc">
                  Play audio ping in the operations room when a CRITICAL violation triggers.
                </span>
              </div>
              <label className="av-toggle-switch">
                <input
                  type="checkbox"
                  checked={soundAlerts}
                  onChange={(e) => setSoundAlerts(e.target.checked)}
                />
                <span className="av-toggle-slider" />
              </label>
            </div>

            <div className="av-settings-row">
              <div className="av-settings-row-info">
                <span className="av-settings-label">Emergency Email Notifications</span>
                <span className="av-settings-desc">
                  Dispatch instant notification packet to site safety supervisors.
                </span>
              </div>
              <label className="av-toggle-switch">
                <input
                  type="checkbox"
                  checked={emailAlerts}
                  onChange={(e) => setEmailAlerts(e.target.checked)}
                />
                <span className="av-toggle-slider" />
              </label>
            </div>

            <div className="av-settings-row">
              <div className="av-settings-row-info">
                <span className="av-settings-label">Slack / Teams Webhook Integration</span>
                <span className="av-settings-desc">
                  Incoming webhook endpoint for incident event dispatch.
                </span>
              </div>
              <input
                type="text"
                value={webhookUrl}
                onChange={(e) => setWebhookUrl(e.target.value)}
                style={{
                  width: 320,
                  padding: '7px 12px',
                  borderRadius: 6,
                  border: '1px solid var(--border-strong)',
                  background: 'var(--panel-2)',
                  color: 'var(--text)',
                  fontSize: 12}}
              />
            </div>
          </div>
        </div>
      )}

      {activeTab === 'edge' && (
        <div className="av-settings-section">
          <div className="av-settings-card">
            <span className="av-settings-card-title">
              <Cpu size={16} color="var(--accent)" />
              <span>Edge Node & Security Tokens</span>
            </span>

            <div className="av-settings-row">
              <div className="av-settings-row-info">
                <span className="av-settings-label">Edge Service Daemon IP</span>
                <span className="av-settings-desc">
                  Local RTSP and telemetry daemon running on Jetson Orin NX.
                </span>
              </div>
              <span className="av-mono" style={{ fontSize: 13, color: 'var(--accent)' }}>
                192.168.1.120:8000
              </span>
            </div>

            <div className="av-settings-row">
              <div className="av-settings-row-info">
                <span className="av-settings-label">API Access Token</span>
                <span className="av-settings-desc">
                  Bearer authentication key for REST & WebSocket telemetry streams.
                </span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span className="av-mono" style={{ fontSize: 12, color: 'var(--text-faint)' }}>
                  av_live_9f83a210bc93***
                </span>
                <button className="av-btn-secondary" type="button">
                  <Key size={13} />
                  <span>Regenerate</span>
                </button>
              </div>
            </div>

            <div className="av-settings-row">
              <div className="av-settings-row-info">
                <span className="av-settings-label">TensorRT Engine Version</span>
                <span className="av-settings-desc">
                  Hardware-accelerated CUDA 12.6 engine built for Ampere/Orin GPU.
                </span>
              </div>
              <span className="av-status-pill reviewed">
                <CheckCircle2 size={12} />
                <span>TensorRT 10.3.0 Verified</span>
              </span>
            </div>
          </div>
        </div>
      )}

      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginTop: 14 }}>
        <button className="av-btn-primary" onClick={handleSave} type="button">
          <Save size={15} />
          <span>Save Preferences</span>
        </button>
        {savedFeedback && (
          <span style={{ color: 'var(--good)', fontSize: 13, display: 'flex', alignItems: 'center', gap: 6 }}>
            <CheckCircle2 size={15} />
            <span>Settings saved successfully!</span>
          </span>
        )}
      </div>
    </div>
  )
}

