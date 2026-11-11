// A change the assistant proposed, put in the words a person would use: what will happen, and the values it will use.
// The tool's own name and its call syntax are never shown.

export interface ProposalText {
  title: string // "Create cluster “Site A”"
  details: [label: string, value: string][] // "Description" -> "Foundation works"
}

const quote = (value: unknown) => `“${String(value)}”`

// Titles of the changes the PPE server offers; a tool not listed here is spelled out from its name
const TITLES: Record<string, (args: Record<string, unknown>) => string> = {
  create_cluster: (a) => `Create cluster ${quote(a.name)}`,
  create_node: (a) => `Create node ${quote(a.name)}`,
  delete_node: (a) => `Delete node #${a.node_id}`,
  create_camera: (a) => `Create camera ${quote(a.name)}`,
  update_camera: (a) => `Update camera #${a.camera_id}`,
  delete_camera: (a) => `Delete camera #${a.camera_id}`,
}

const LABELS: Record<string, string> = {
  name: 'Name',
  description: 'Description',
  cluster_id: 'Cluster',
  node_id: 'Node',
  camera_id: 'Camera',
  max_cameras: 'Camera limit',
  zone: 'Zone',
  enabled: 'Enabled',
}

const sentence = (text: string) => text.replace(/_/g, ' ').replace(/^./, (c) => c.toUpperCase())

function valueText(key: string, value: unknown): string {
  if (typeof value === 'boolean') return value ? 'Yes' : 'No'
  if (key.endsWith('_id')) return `#${value}`
  return String(value)
}

export function describeProposal(tool: string | undefined, args: Record<string, unknown> | undefined, summary: string): ProposalText {
  if (!tool) return { title: summary.split('): ').pop() ?? summary, details: [] } // a conversation saved before the tool was sent
  const given = args ?? {}
  const title = TITLES[tool]?.(given) ?? sentence(tool)
  const details = Object.entries(given)
    .filter(([, value]) => value !== null && value !== undefined && value !== '')
    .map(([key, value]): [string, string] => [LABELS[key] ?? sentence(key), valueText(key, value)])
  return { title, details }
}
