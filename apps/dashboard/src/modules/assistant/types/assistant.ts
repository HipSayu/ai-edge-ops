export interface ChatMessage { id: number; role: 'user' | 'assistant'; text: string; timestamp?: string }

// One step of how the agent reached its answer, shown in the reasoning trace:
// the model's reasoning, text it wrote while working, and each tool call merged with its result
export type TraceStep =
  | { kind: 'reasoning'; text: string }
  | { kind: 'text'; text: string }
  | {
      kind: 'tool'
      id: string
      tool: string
      args: Record<string, unknown>
      status: 'running' | 'success' | 'error'
      output?: string
    }

export interface PendingApproval {
  sessionId: string
  requests: { tool_call_id: string; name: string; args: Record<string, unknown> }[]
}

export type ToolDecision = { tool_call_id: string; decision: 'approve' | 'reject' | 'other'; message?: string }

// SSE events of GET /chat/stream/{stream_id} (apps/assistant)
export type ChatStreamEvent =
  | { event: 'reasoning'; data: { content: string } }
  | { event: 'token'; data: { content: string } }
  | { event: 'status'; data: { type: 'TOOLS'; tools: { id: string; name: string; args: Record<string, unknown> }[] } }
  | { event: 'tool_end'; data: { id: string | null; tool: string; status: 'success' | 'error'; output: string } }
  | { event: 'done'; data: { reply: string; session_id: string } }
  | { event: 'approval_required'; data: { session_id: string; requests: PendingApproval['requests'] } }
  | { event: 'error'; data: { message: string } }

// Conversations are kept by the Cloud (/api/v1/conversations); the id is the assistant's session_id
export interface Conversation { id: string; title: string | null; createdAt: string; updatedAt: string }

export interface StoredMessage {
  id: string
  role: 'USER' | 'ASSISTANT'
  content: string | null
  metadata: { trace?: TraceStep[]; startedAt?: number; finishedAt?: number; error?: boolean }
  createdAt: string
}
